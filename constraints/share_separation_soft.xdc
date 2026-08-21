# share_separation_soft.xdc
#
# Soft version of share_separation.xdc. The original (hard, CONTAIN_ROUTING
# true) version successfully separated XOR and NAND but caused a routing
# FAILURE on the AND gadget, because AND's cross-share term (cross01/
# cross10) survives synthesis as a distinct signal that must physically
# connect share-0 and share-1 territory -- a hard containment boundary
# makes that provably impossible to route.
#
# This version marks both pblocks IS_SOFT true instead of using
# CONTAIN_ROUTING. A soft pblock is a strong placement PREFERENCE, not an
# absolute prohibition: Vivado will still try hard to keep cells inside
# their assigned region, but is permitted to place/route outside it if
# the alternative is an unroutable design. This should let AND's
# cross-share wire actually route while still meaningfully separating
# everything else.

create_pblock pblock_share0_soft
create_pblock pblock_share1_soft

resize_pblock pblock_share0_soft -add {SLICE_X0Y0:SLICE_X30Y99}
resize_pblock pblock_share1_soft -add {SLICE_X60Y0:SLICE_X90Y99}

add_cells_to_pblock pblock_share0_soft [get_cells -hierarchical *_sh0*]
add_cells_to_pblock pblock_share1_soft [get_cells -hierarchical *_sh1*]

set_property IS_SOFT true [get_pblocks pblock_share0_soft]
set_property IS_SOFT true [get_pblocks pblock_share1_soft]
