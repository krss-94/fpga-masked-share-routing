#!/usr/bin/env python3
"""
generate_constraints.py

Phase 3 constraint generator for the M5 automated conflict-mitigation
pipeline. Takes the classifier's JSON output (from detect_classify.tcl,
frozen/unmodified) plus an explicit repair-policy config, and emits a
deterministic XDC repair file plus a structured, auditable generation
log. Contains NO hardcoded cell names (no "cross01"/"cross10" in this
file) and NO geometric/nearest-pblock inference for UNCLASSIFIED_ONLY --
per the corrected Phase 2 contract, that case is resolved purely from an
explicit repair policy supplied in the policy config, never guessed.

CONTRACT
--------
MIXED_SITE_CONFLICT       -> UNSUPPORTED_REQUIRES_MANUAL_REVIEW.
                              No constraint emitted. Generator reports
                              and continues (does not silently drop it),
                              but produces no XDC action for it.
UNCLASSIFIED_CELL_PRESENT -> assign to the site's unanimous classified
                              side. If the site's classified members are
                              not unanimous, FAIL LOUDLY (should not
                              happen if MIXED_SITE_CONFLICT sites are
                              excluded first, but checked defensively).
UNCLASSIFIED_ONLY          -> resolved ONLY via the explicit repair
                              policy from the policy config. If no
                              policy rule matches, FAIL LOUDLY rather
                              than guess.
OK_SAME_SIDE / OK_SINGLE_CELL -> no constraint generated.

POLICY CONFIG FORMAT (JSON)
----------------------------
{
  "pblocks": {
    "sh0": "pblock_share0",
    "sh1": "pblock_share1"
  },
  "unclassified_only_policy": {
    "type": "SEPARATE_CROSS_TERMS",
    "groups": [
      {"pattern": "*cross01*", "side": "sh1"},
      {"pattern": "*cross10*", "side": "sh0"}
    ]
  }
}

The "groups" list is matched against unclassified cell NAMES using the
same glob semantics as the classifier, but this matching lives in the
POLICY CONFIG, not in generator code -- swapping the policy for a
different design means editing the config, not this script.

OUTPUT
------
- <output_xdc>: add_cells_to_pblock statements only (assumes pblocks
  already exist in the base XDC -- this generator emits the repair
  DELTA, not a full replacement XDC, so it can be layered onto an
  existing constraint set).
- <output_log_json>: one entry per watched cell that required a
  decision, with classification, assigned side, rule fired, and reason.
  Entries for MIXED_SITE_CONFLICT cells are included with
  action="NONE_UNSUPPORTED" so nothing is silently dropped from the record.

USAGE:
    python generate_constraints.py <classifier_json> <policy_json> <output_xdc> <output_log_json>
"""

import sys
import json
import fnmatch


def fail(msg):
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def load_json(path, label):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        fail(f"{label} not found: {path}")
    except json.JSONDecodeError as e:
        fail(f"{label} is not valid JSON: {path} -- {e}")


def main():
    if len(sys.argv) != 5:
        fail("usage: generate_constraints.py <classifier_json> <policy_json> <output_xdc> <output_log_json>")

    classifier_path, policy_path, out_xdc_path, out_log_path = sys.argv[1:5]

    classifier = load_json(classifier_path, "classifier JSON")
    policy = load_json(policy_path, "policy JSON")

    for req in ("cells", "sites", "summary"):
        if req not in classifier:
            fail(f"classifier JSON missing required field: {req}")
    for req in ("pblocks", "unclassified_only_policy"):
        if req not in policy:
            fail(f"policy JSON missing required field: {req}")
    for req in ("sh0", "sh1"):
        if req not in policy["pblocks"]:
            fail(f"policy JSON pblocks missing required side: {req}")

    pblock_sh0 = policy["pblocks"]["sh0"]
    pblock_sh1 = policy["pblocks"]["sh1"]
    pblock_of = {"sh0": pblock_sh0, "sh1": pblock_sh1}

    uo_policy = policy["unclassified_only_policy"]
    if uo_policy.get("type") != "SEPARATE_CROSS_TERMS":
        fail(f"unsupported unclassified_only_policy type: {uo_policy.get('type')!r} "
             f"(only SEPARATE_CROSS_TERMS is implemented in this generator version)")
    policy_groups = uo_policy.get("groups", [])
    if not policy_groups:
        fail("unclassified_only_policy.groups is empty -- no rule to resolve UNCLASSIFIED_ONLY cells")

    site_by_name = {s["site"]: s for s in classifier["sites"]}
    cell_side = {c["name"]: c["side"] for c in classifier["cells"]}

    unclassified_present_sites = sorted(
        (s for s in classifier["sites"] if s["classification"] == "UNCLASSIFIED_CELL_PRESENT"),
        key=lambda s: s["site"]
    )
    unclassified_only_sites = sorted(
        (s for s in classifier["sites"] if s["classification"] == "UNCLASSIFIED_ONLY"),
        key=lambda s: s["site"]
    )
    mixed_sites = sorted(
        (s for s in classifier["sites"] if s["classification"] == "MIXED_SITE_CONFLICT"),
        key=lambda s: s["site"]
    )

    log_entries = []
    assignments = []  # (cell_name, side, rule, reason)

    for site in mixed_sites:
        for member in site["members"]:
            log_entries.append({
                "cell": member,
                "site": site["site"],
                "classification": "MIXED_SITE_CONFLICT",
                "assigned_side": None,
                "rule": "NONE",
                "action": "NONE_UNSUPPORTED",
                "reason": "Site contains both sh0- and sh1-classified cells. This is a "
                          "placement collision, not a coverage gap -- requires manual review, "
                          "not an automated pblock-membership addition."
            })

    for site in unclassified_present_sites:
        classified_sides = {cell_side[m] for m in site["members"] if cell_side[m] in ("sh0", "sh1")}
        unclassified_members = [m for m in site["members"] if cell_side[m] == "unclassified"]

        if len(classified_sides) != 1:
            fail(f"site {site['site']} classified UNCLASSIFIED_CELL_PRESENT but its classified "
                 f"members are not unanimous ({classified_sides}) -- refusing to guess. "
                 f"This should not happen unless a MIXED_SITE_CONFLICT site was misclassified.")

        inferred_side = next(iter(classified_sides))
        for member in unclassified_members:
            assignments.append((member, inferred_side, "SITE_UNANIMOUS_INFERENCE",
                                 f"Site {site['site']} contains only {inferred_side}-classified "
                                 f"cells alongside this unclassified cell; inferred by unanimous "
                                 f"site membership, no policy needed."))

    for site in unclassified_only_sites:
        for member in site["members"]:
            matched = None
            for group in policy_groups:
                if fnmatch.fnmatch(member, group["pattern"]):
                    matched = group
                    break
            if matched is None:
                fail(f"cell {member!r} at site {site['site']} is UNCLASSIFIED_ONLY and does not "
                     f"match any pattern in unclassified_only_policy.groups -- refusing to guess "
                     f"a side. Add an explicit policy rule for this cell/pattern.")
            assignments.append((member, matched["side"], "EXPLICIT_POLICY",
                                 f"No site-level evidence (cell is alone at {site['site']}). "
                                 f"Resolved via configured policy '{uo_policy['type']}': "
                                 f"pattern {matched['pattern']!r} -> {matched['side']}."))

    assignments.sort(key=lambda a: a[0])

    for cell, side, rule, reason in assignments:
        log_entries.append({
            "cell": cell,
            "site": next((c["site"] for c in classifier["cells"] if c["name"] == cell), ""),
            "classification": "UNCLASSIFIED_CELL_PRESENT" if rule == "SITE_UNANIMOUS_INFERENCE" else "UNCLASSIFIED_ONLY",
            "assigned_side": side,
            "rule": rule,
            "action": "ADD_CELLS_TO_PBLOCK",
            "target_pblock": pblock_of[side],
            "reason": reason
        })

    log_entries.sort(key=lambda e: (e["classification"] != "MIXED_SITE_CONFLICT", e["cell"]))

    by_side = {"sh0": [], "sh1": []}
    for cell, side, rule, reason in assignments:
        by_side[side].append(cell)

    xdc_lines = []
    xdc_lines.append("# Auto-generated by generate_constraints.py -- DO NOT HAND-EDIT.")
    xdc_lines.append(f"# Source classifier JSON: {classifier_path}")
    xdc_lines.append(f"# Source policy JSON: {policy_path}")
    xdc_lines.append("# This file adds pblock-membership constraints for cells the classifier")
    xdc_lines.append("# found unclassified. It assumes pblock_share0 / pblock_share1 (or the")
    xdc_lines.append("# configured pblock names) already exist -- apply AFTER the base")
    xdc_lines.append("# share-separation XDC that creates and sizes the pblocks.")
    xdc_lines.append("")

    if mixed_sites:
        xdc_lines.append("# NOTE: the following sites were classified MIXED_SITE_CONFLICT and")
        xdc_lines.append("# are NOT addressed by this generated file -- they require manual")
        xdc_lines.append("# review, not an automated pblock-membership fix:")
        for site in mixed_sites:
            xdc_lines.append(f"#   {site['site']}: {', '.join(site['members'])}")
        xdc_lines.append("")

    for side in ("sh0", "sh1"):
        cells = sorted(by_side[side])
        if not cells:
            continue
        xdc_lines.append(f"# {len(cells)} cell(s) assigned to {side} ({pblock_of[side]})")
        for cell in cells:
            entry = next(e for e in log_entries if e["cell"] == cell)
            xdc_lines.append(f"#   {cell}: {entry['rule']} -- {entry['reason']}")
        cell_filter = " || ".join(f"NAME =~ {c}" for c in cells)
        xdc_lines.append(
            f"add_cells_to_pblock {pblock_of[side]} "
            f"[get_cells -hierarchical -filter {{{cell_filter}}}]"
        )
        xdc_lines.append("")

    if not by_side["sh0"] and not by_side["sh1"]:
        xdc_lines.append("# No repair constraints generated -- classifier reported no")
        xdc_lines.append("# UNCLASSIFIED_CELL_PRESENT or UNCLASSIFIED_ONLY sites.")

    with open(out_xdc_path, "w") as f:
        f.write("\n".join(xdc_lines) + "\n")

    with open(out_log_path, "w") as f:
        json.dump({
            "classifier_input": classifier_path,
            "policy_input": policy_path,
            "mixed_site_conflict_count": len(mixed_sites),
            "assignments_generated": len(assignments),
            "entries": log_entries
        }, f, indent=2)

    print("=== Generation complete ===")
    print(f"MIXED_SITE_CONFLICT sites (unsupported, reported only): {len(mixed_sites)}")
    print(f"Assignments generated: {len(assignments)}")
    print(f"  via SITE_UNANIMOUS_INFERENCE: {sum(1 for a in assignments if a[2]=='SITE_UNANIMOUS_INFERENCE')}")
    print(f"  via EXPLICIT_POLICY: {sum(1 for a in assignments if a[2]=='EXPLICIT_POLICY')}")
    print(f"XDC written to: {out_xdc_path}")
    print(f"Log written to: {out_log_path}")


if __name__ == "__main__":
    main()
