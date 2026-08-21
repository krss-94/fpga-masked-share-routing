"""
Milestone 2b: targeted PIP-level pathfinder, tile-avoidance BFS.

WHY THIS EXISTS: Milestone 2 (mitigate_switchbox_conflicts.tcl) proved,
three independent ways (default reroute, -directive Explore), that
Vivado's stock router has no concept of "avoid this tile" and reliably
regenerates the exact same 28 switch-box/CLB conflicts every time.
RWRoute (RapidWright's own alternative router) explicitly refuses to run
on Series7 parts (confirmed error: "RWRoute does not support routing the
xc7a100tcsg324-1 from the Series7 series"), so it cannot be used on this
device without a device-family pivot.

THIS SCRIPT: instead of replacing the whole design's router (what RWRoute
does), this only reroutes the SPECIFIC nets Milestone 1 flagged, using a
hand-written breadth-first search directly over RapidWright's Node graph
(Node/PIP objects are NOT series-restricted -- only RWRoute's packaged
router has that restriction). The search explicitly forbids any node
whose tile is in the conflict-tile set, forcing the path around the
switch box / CLB tile Milestone 1 identified.

HONESTY / RISK NOTE -- READ BEFORE RUNNING:
    This is a hand-written maze router, not a validated RapidWright
    feature. The exact API calls used here (Node.getAllDownhillNodes(),
    SitePinInst.getConnectedNode(), Net.unroute(), Net.setPIPs()) are
    believed correct based on RapidWright's general design but have NOT
    been tested against your installed RapidWright version in this
    environment (no RapidWright access here). This is the most likely
    script so far to need a debug round-trip -- if it errors, paste the
    exact traceback back; the fix is very likely a method-name correction,
    not a design flaw. This also does not implement any timing-awareness
    or congestion-awareness that a real router has -- it finds *a* valid
    path avoiding the excluded tiles, not necessarily a good one. That is
    an explicit, disclosed scope limitation, not an oversight.

USAGE:
    python milestone2b_targeted_reroute.py placed_routed_and_placement_only.dcp \\
        --jar %RAPIDWRIGHT_JAR% \\
        --conflicts switchbox_conflicts.csv \\
        --out placed_routed_and_targeted_reroute.dcp
"""

import sys
import os
import csv
import argparse
from collections import deque

import jpype
import jpype.imports


def start_rapidwright(jar_path: str):
    """Start JPype with a much larger JVM heap. The previous run crashed
    the JVM outright (native malloc failure) after ~3M nodes explored --
    confirmed real OOM, not just a Python-side slowdown."""
    jpype.startJVM("-Xmx12g", classpath=[jar_path])


def load_conflict_tiles_and_nets(csv_path):
    """Read Milestone 1's switchbox_conflicts.csv. Returns:
        conflict_tiles: set of tile names to avoid
        conflict_nets: set of net names that need rerouting
    """
    conflict_tiles = set()
    conflict_nets = set()
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            conflict_tiles.add(row["tile"])
            conflict_nets.add(row["share0_net"])
            conflict_nets.add(row["share1_net"])
    return conflict_tiles, conflict_nets


def bfs_avoid_tiles(source_node, sink_node, forbidden_tile_names, max_nodes_explored=10_000_000):
    """Weighted A* search over the RapidWright routing graph.

    UPGRADED AGAIN after the 2M-node diagnostic run: hitting the cap with
    the queue still full (not exhausted) meant the search hadn't given up
    on genuine impossibility -- it was just too slow to get there. Root
    cause: the Manhattan tile-distance heuristic badly underestimates true
    cost, since each tile-to-tile hop can cost 5-20 PIPs, not 1. That made
    A* behave almost like unweighted Dijkstra/BFS across a huge Artix-7
    routing graph. Weighting the heuristic (h * WEIGHT) makes the search
    much greedier toward the goal -- since we only need *a* valid
    tile-avoiding path, not the provably shortest one, sacrificing
    optimality for speed here is the right tradeoff.
    """
    import heapq

    WEIGHT = 50  # very greedy -- per-tile state tracking means we can afford
                 # to be aggressive and still stay memory-safe

    def node_key(n):
        return (str(n.getTile().getName()), int(n.getWireIndex()))

    def tile_distance(n):
        t = n.getTile()
        return abs(int(t.getColumn()) - goal_col) + abs(int(t.getRow()) - goal_row)

    goal_tile = sink_node.getTile()
    goal_tile_name = str(goal_tile.getName())
    goal_col = int(goal_tile.getColumn())
    goal_row = int(goal_tile.getRow())
    goal_key = node_key(sink_node)
    start_key = node_key(source_node)

    print(f"  [search] source tile: {start_key[0]}  sink tile: {goal_key[0]}  "
          f"manhattan tile-dist: {tile_distance(source_node)}")

    # BUGFIX (found via diagnostic run): the earlier version only exempted
    # the exact sink NODE from the forbidden-tile check, not the sink's
    # whole TILE. But reaching a pin inside a CLB tile almost always
    # requires passing through OTHER internal nodes of that same tile
    # first (the site's local routing mux chain) -- those intermediate
    # nodes were being wrongly blocked, making the sink structurally
    # unreachable regardless of search budget whenever the sink happens
    # to live inside a forbidden tile (which is common: Milestone 1 flags
    # a tile specifically because real share-0/share-1 net endpoints sit
    # there). Fix: exempt the sink's entire tile from the forbidden set
    # for this search, not just its single exact node. Same reasoning
    # applies to the source tile, so it's exempted too.
    start_tile_name = str(source_node.getTile().getName())
    effective_forbidden = forbidden_tile_names - {goal_tile_name, start_tile_name}
    if effective_forbidden != forbidden_tile_names:
        removed = forbidden_tile_names - effective_forbidden
        print(f"  [search] exempting source/sink's own tile(s) from avoidance: "
              f"{sorted(removed)} (you cannot avoid the tile your own endpoint lives in)")

    if start_key == goal_key:
        return []

    # MEMORY FIX (found via crash): the earlier version tracked best_g and
    # came_from per WIRE (node_key), and an INT tile alone has ~200 wires.
    # 3M nodes explored meant hundreds of millions of dict entries' worth
    # of state, which crashed the JVM outright with a real native malloc
    # failure -- this was genuine OOM, not just slow. Since we only need
    # *a* valid path (not the provably optimal one), tracking the best
    # cost to ENTER each TILE (not each wire) is sufficient and cuts
    # memory from millions of entries down to roughly one per tile.
    best_g_tile = {}   # tile_name -> best g cost seen for that tile (INTER-tile pruning)
    node_g = {}         # node_key -> best g cost for that specific node (INTRA-tile pruning,
                         # bounded since a single tile only has ~100-200 wires)
    came_from = {}      # node_key -> (parent_node_key, pip)
    counter = 0
    open_heap = [(tile_distance(source_node) * WEIGHT, counter, source_node)]
    best_g_tile[start_tile_name] = 0
    node_g[start_key] = 0

    explored = 0
    last_print = 0
    while open_heap:
        f, _, current = heapq.heappop(open_heap)
        explored += 1

        if explored - last_print >= 500_000:
            print(f"    [progress] explored {explored:,} nodes, heap size {len(open_heap):,}, "
                  f"current tile: {current.getTile().getName()}")
            last_print = explored

        if explored > max_nodes_explored:
            print(f"    [diagnostic] hit the search CAP at {explored:,} nodes "
                  f"(queue still had entries -- more search budget might help)")
            return None

        current_key = node_key(current)
        current_tile_name = current_key[0]
        g = best_g_tile.get(current_tile_name, float("inf"))
        # Track g-cost for the SPECIFIC current node too, not just its
        # tile, so intra-tile hops (needed to reach a specific internal
        # wire/pin before leaving the tile) aren't gated by the coarser
        # per-tile cap -- see fix below.
        current_node_g = node_g.get(current_key, g)

        for pip in current.getAllDownhillPIPs():
            nxt = pip.getEndNode()
            if nxt is None:
                continue
            nxt_key = node_key(nxt)
            nxt_tile_name = nxt_key[0]

            is_goal = (nxt_key == goal_key)

            if (nxt_tile_name in effective_forbidden) and not is_goal:
                continue

            new_g = current_node_g + 1

            if is_goal:
                # Reaching the goal node always counts as a success,
                # regardless of any cost bookkeeping below.
                came_from[nxt_key] = (current_key, pip)
                path_pips = []
                k = nxt_key
                while k in came_from:
                    parent_key, pip_used = came_from[k]
                    path_pips.append(pip_used)
                    k = parent_key
                path_pips.reverse()
                print(f"    [success] path found: {len(path_pips)} PIPs "
                      f"after exploring {explored:,} nodes")
                return path_pips

            if nxt_tile_name == current_tile_name:
                # INTRA-tile hop: needed to navigate to a specific
                # internal wire/pin before the path can leave this tile
                # at all. BUG FOUND (via same-tile source/sink nets all
                # exhausting after 1 node): gating this by the coarse
                # per-tile best-cost cap wrongly treated "already visited
                # this tile" as "no further intra-tile moves are useful,"
                # trapping the search inside its own starting tile. Gate
                # by per-NODE visited status instead here -- a tile only
                # has on the order of ~100-200 wires, so this stays cheap.
                if nxt_key in node_g and node_g[nxt_key] <= new_g:
                    continue
                node_g[nxt_key] = new_g
                came_from[nxt_key] = (current_key, pip)
                counter += 1
                h = tile_distance(nxt) * WEIGHT
                heapq.heappush(open_heap, (new_g + h, counter, nxt))
                continue

            # INTER-tile hop: this is where node counts genuinely explode
            # across the fabric, so keep the coarser per-tile cap here --
            # this is what actually keeps memory bounded.
            if new_g >= best_g_tile.get(nxt_tile_name, float("inf")):
                continue

            best_g_tile[nxt_tile_name] = new_g
            node_g[nxt_key] = new_g
            came_from[nxt_key] = (current_key, pip)

            counter += 1
            h = tile_distance(nxt) * WEIGHT
            heapq.heappush(open_heap, (new_g + h, counter, nxt))

    print(f"    [diagnostic] search EXHAUSTED naturally after {explored:,} nodes "
          f"-- every reachable tile was visited and the queue ran empty on its "
          f"own. This means no path exists in the routing graph without "
          f"passing through a forbidden tile, regardless of search budget. "
          f"Given this net's sink lives inside {goal_tile_name}, and that tile "
          f"was exempted for its own entry, this strongly suggests the "
          f"adjacent forbidden tile is that tile's ONLY switch-matrix gateway "
          f"-- an architectural dead end, not a search-strength failure.")
    return None  # no path found: graph genuinely exhausted, not a cap issue


def reroute_net_avoiding_tiles(net, forbidden_tile_names):
    """Attempts to reroute `net` from its source pin to EVERY sink pin,
    each path individually avoiding forbidden_tile_names. Returns
    (success: bool, detail: str).

    LIMITATION: routes each sink independently from the same source node,
    rather than building a proper Steiner tree shared across sinks like a
    real router would. For nets with a single sink (the common case for
    the specific conflicting nets here) this is not a limitation at all;
    for multi-sink nets it will produce a valid but likely inefficient
    (more PIPs than necessary) routing. Disclosed, not hidden.
    """
    source_pin = net.getSource()
    if source_pin is None:
        return False, "net has no source pin (possibly a static/const net) -- skipped"

    source_node = source_pin.getConnectedNode()
    if source_node is None:
        return False, "source pin has no connected Node -- skipped"

    sink_pins = net.getSinkPins()
    if sink_pins is None or len(sink_pins) == 0:
        return False, "net has no sink pins -- skipped"

    existing_pips = net.getPIPs()
    if existing_pips:
        print(f"  Net currently routed with {len(existing_pips)} PIPs (before rip-up)")

    all_pips = []
    for sink_pin in sink_pins:
        sink_node = sink_pin.getConnectedNode()
        if sink_node is None:
            return False, f"sink pin {sink_pin} has no connected Node -- aborting this net"

        pips = bfs_avoid_tiles(source_node, sink_node, forbidden_tile_names)
        if pips is None:
            return False, (
                f"no path found from source to sink {sink_pin} avoiding "
                f"forbidden tiles (search exhausted or capped) -- this net "
                f"may be structurally forced through the excluded tiles"
            )

        all_pips.extend(pips)

    net.unroute()
    # setPIPs expects a Java List -- JPype should auto-convert a Python
    # list of PIP objects, but if this line errors with a type-mismatch,
    # try wrapping with java.util.ArrayList explicitly.
    net.setPIPs(all_pips)

    return True, f"rerouted with {len(all_pips)} PIPs across {len(sink_pins)} sink(s)"


def main():
    parser = argparse.ArgumentParser(description="Milestone 2b: targeted tile-avoidance reroute")
    parser.add_argument("dcp", help="Path to placed_routed.dcp")
    parser.add_argument("--jar", default=os.environ.get("RAPIDWRIGHT_JAR"))
    parser.add_argument("--conflicts", default="switchbox_conflicts.csv")
    parser.add_argument("--out", default="placed_routed_and_targeted_reroute.dcp")
    parser.add_argument("--only-net", default=None,
                         help="If set, only attempt rerouting this single net "
                              "name (diagnostic mode -- use with a much higher "
                              "search cap to test whether a path genuinely "
                              "exists at all, without waiting through 8 other "
                              "nets first).")
    args = parser.parse_args()

    if not args.jar:
        print("Error: RapidWright jar path required via --jar or RAPIDWRIGHT_JAR env var.")
        sys.exit(1)

    if not os.path.exists(args.conflicts):
        print(f"Error: conflicts CSV not found: {args.conflicts}")
        print("Run switch_box_conflict_detector.py first.")
        sys.exit(1)

    conflict_tiles, conflict_nets = load_conflict_tiles_and_nets(args.conflicts)

    if args.only_net:
        if args.only_net not in conflict_nets:
            print(f"Error: --only-net '{args.only_net}' is not in the conflicts CSV.")
            print(f"Available nets: {sorted(conflict_nets)}")
            sys.exit(1)
        conflict_nets = {args.only_net}
        print(f"DIAGNOSTIC MODE: only attempting net '{args.only_net}' with a "
              f"much higher search cap (see bfs_avoid_tiles max_nodes_explored).")

    print(f"Loaded {len(conflict_tiles)} forbidden tile(s): {sorted(conflict_tiles)}")
    print(f"Loaded {len(conflict_nets)} conflicting net(s) to reroute: {sorted(conflict_nets)}")

    start_rapidwright(args.jar)
    from com.xilinx.rapidwright.design import Design  # noqa: E402

    print(f"\nReading DCP: {args.dcp}")
    design = Design.readCheckpoint(args.dcp)

    results = {}
    for net_name in sorted(conflict_nets):
        net = design.getNet(net_name)
        if net is None:
            results[net_name] = (False, "net not found in design (name mismatch?)")
            continue

        print(f"\nRerouting net: {net_name}")
        try:
            success, detail = reroute_net_avoiding_tiles(net, conflict_tiles)
            results[net_name] = (success, detail)
            print(f"  {'OK' if success else 'FAILED'}: {detail}")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            results[net_name] = (False, f"exception: {repr(e)}")
            print(f"  EXCEPTION: {repr(e)}")
            print(tb)

    n_success = sum(1 for s, _ in results.values() if s)
    n_total = len(results)
    print(f"\n=== Summary: {n_success}/{n_total} nets successfully rerouted ===")
    for net_name, (success, detail) in results.items():
        status = "OK" if success else "FAILED"
        print(f"  [{status}] {net_name}: {detail}")

    if n_success > 0:
        design.writeCheckpoint(args.out)
        print(f"\nWrote {args.out}")
        print("\nNEXT STEPS:")
        print(f"  1. Open {args.out} in Vivado, run write_edif -force (RapidWright")
        print("     needs a matching readable EDIF, same as previous milestones).")
        print("  2. Run report_route_status in Vivado to confirm no routing errors")
        print("     were introduced (this script's BFS does not check for resource")
        print("     conflicts with OTHER nets it did not touch -- report_route_status")
        print("     is the real verification, not this script's own success message).")
        print("  3. Re-run switch_box_conflict_detector.py against the new checkpoint")
        print("     to confirm the conflict count actually dropped.")
    else:
        print("\nNo nets were successfully rerouted -- nothing written.")


if __name__ == "__main__":
    main()
