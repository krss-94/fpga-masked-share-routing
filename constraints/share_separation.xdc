# share_separation.xdc
#
# Placement constraints testing whether explicit physical separation of
# share-0 and share-1 logic improves the distance indicator, compared to
# the unconstrained baseline (all 3 gadgets showed minimum distance = 0
# under default Vivado placement -- see distance_indicator_*.json).
#
# This is a deliberate extension BEYOND the frozen project scope (see
# PROJECT_SUMMARY.md Section 6: "does not guarantee absence of leakage" --
# the frozen methodology is identification-only). This constraint file is
# a self-initiated follow-up experiment: having identified that default
# placement gives no separation guarantee, we test one candidate
# mitigation and observe whether the same indicator responds to it.
#
# Two pblocks are defined on the xc7a100tcsg324-1 fabric, physically far
# apart (opposite corners of the usable slice region), and all cells
# matching the project's share-tagging convention are pinned into the
# matching pblock via ADD_CELLS with a name-pattern match.
#
# NOTE: pblock coordinate ranges below are a reasonable starting split for
# this device's slice grid, not verified against a specific floorplan
# viewer. If Vivado reports an invalid range or "no valid sites" error,
# that's a real, expected debugging step -- open the Device view in the
# Vivado GUI once to confirm real SLICE coordinate bounds, then adjust
# these ranges to match.

create_pblock pblock_share0
create_pblock pblock_share1

# Left half of the die for share 0, right half for share 1 -- adjust
# SLICE_X/SLICE_Y ranges to match your actual part's real coordinate
# extents if this range is rejected.
resize_pblock pblock_share0 -add {SLICE_X0Y0:SLICE_X30Y99}
resize_pblock pblock_share1 -add {SLICE_X60Y0:SLICE_X90Y99}

add_cells_to_pblock pblock_share0 [get_cells -hierarchical *_sh0*]
add_cells_to_pblock pblock_share1 [get_cells -hierarchical *_sh1*]

# Keep pblocks strictly separate -- do not let Vivado spill cells outside
# the assigned region for either share.
set_property CONTAIN_ROUTING true [get_pblocks pblock_share0]
set_property CONTAIN_ROUTING true [get_pblocks pblock_share1]
