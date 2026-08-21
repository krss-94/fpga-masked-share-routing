# share_separation_placement_only.xdc
#
# v2 of the corridor idea. v1 (hard CONTAIN_ROUTING on both share
# pblocks) failed routing on plain SAME-share signals (t0_sh1,
# u_and_sh1/y) even with correct, unclipped device coordinates --
# meaning CONTAIN_ROUTING forbids certain internal dedicated-path
# routes even for signals fully inside the pblock, not just the
# genuine cross-share signal.
#
# This version constrains PLACEMENT only (hard pblock membership),
# with NO CONTAIN_ROUTING and NO IS_SOFT. Cells are still forced into
# disjoint physical regions -- giving the same distance-indicator
# separation guarantee -- but the router is left completely free to
# route any net, including the genuine cross-share signal, however it
# needs to.

create_pblock pblock_share0_hard
create_pblock pblock_share1_hard

resize_pblock pblock_share0_hard -add {SLICE_X0Y0:SLICE_X30Y99}
resize_pblock pblock_share1_hard -add {SLICE_X60Y0:SLICE_X89Y99}

add_cells_to_pblock pblock_share0_hard [get_cells -hierarchical *_sh0*]
add_cells_to_pblock pblock_share1_hard [get_cells -hierarchical *_sh1*]

set_property IS_SOFT false [get_pblocks pblock_share0_hard]
set_property IS_SOFT false [get_pblocks pblock_share1_hard]
# No CONTAIN_ROUTING, no IS_SOFT, no EXCLUDE_PLACEMENT anywhere.
# Placement is still hard-constrained (cells MUST be inside their
# assigned pblock) -- only routing is left unconstrained.

