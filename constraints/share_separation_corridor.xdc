# share_separation_corridor.xdc
#
# "Quarantined crossing corridor" constraint (v1) -- a new construction,
# not copied from an existing paper, though inspired by the isolation
# philosophy in FPGAPRO's compensation-zone approach (ACM TODAES,
# https://dl.acm.org/doi/10.1145/3491214), which addresses a DIFFERENT
# threat model (cross-tenant crosstalk in cloud FPGAs) using a similar
# idea: a dedicated zone for wires that cannot be perfectly isolated.
#
# THE PROBLEM THIS SOLVES:
#   Hard containment (share_separation.xdc, CONTAIN_ROUTING true) gives
#   strong separation but breaks routing outright for the AND gadget,
#   because its cross-share signals (cross01/cross10) must physically
#   connect share-0 and share-1 territory -- a genuine, unavoidable
#   requirement of the masking mechanism itself.
#
#   Soft containment (share_separation_soft.xdc, IS_SOFT true) restores
#   routability but gives up almost all separation guarantee -- and,
#   worse, gives it up in an UNCONTROLLED way (the placer chose to let
#   randomness registers end up adjacent, not because it needed to, just
#   because nothing constrained it not to).
#
# THE NEW IDEA:
#   Keep share-0 and share-1 regions under HARD containment (no
#   compromise, no accidental leaks) for everything EXCEPT the genuine
#   cross-share cells. Carve out a third, small, explicitly quarantined
#   pblock -- physically positioned between the two share regions --
#   whose ONLY legal occupants are the cross-share cells that must exist
#   for the masking math to work. EXCLUDE_PLACEMENT forbids any other
#   cell (share-specific or otherwise) from also being placed in this
#   corridor, so it cannot become an uncontrolled leak point the way the
#   soft-pblock version was.
#
#   This should give: (a) successful routing, because the one genuinely
#   necessary crossing wire has a legal path, and (b) a MUCH stronger,
#   deliberate separation guarantee than the soft version, because
#   nothing except the required crossing signal is permitted anywhere
#   near the boundary.

create_pblock pblock_share0_hard
create_pblock pblock_share1_hard
create_pblock pblock_crossing

# Share-0 and share-1 regions, hard-contained, with a deliberate gap
# between them (X31-X59) reserved for the crossing corridor.
resize_pblock pblock_share0_hard -add {SLICE_X0Y0:SLICE_X30Y99}
resize_pblock pblock_share1_hard -add {SLICE_X60Y0:SLICE_X89Y99}

# The crossing corridor: small, centered in the gap between the two
# hard regions. This is the ONLY physical territory where a share-0/
# share-1 crossing wire is permitted to exist.
resize_pblock pblock_crossing -add {SLICE_X40Y40:SLICE_X50Y60}

# Assign cells. Cross-share cells are matched by name (cross01/cross10,
# per the RTL's naming convention) BEFORE the general _sh0/_sh1 match,
# so they land in the corridor, not in either hard region.
add_cells_to_pblock pblock_crossing [get_cells -hierarchical *cross01*]
add_cells_to_pblock pblock_crossing [get_cells -hierarchical *cross10*]
add_cells_to_pblock pblock_share0_hard [get_cells -hierarchical *_sh0*]
add_cells_to_pblock pblock_share1_hard [get_cells -hierarchical *_sh1*]

# Hard containment for the two share regions: nothing assigned to them
# may route outside.
set_property CONTAIN_ROUTING true [get_pblocks pblock_share0_hard]
set_property CONTAIN_ROUTING true [get_pblocks pblock_share1_hard]

# Quarantine the corridor: ONLY the cross-share cells may be placed
# here. This is the key property that makes this different from simply
# loosening the boundary -- nothing else can hide in this corridor.
set_property EXCLUDE_PLACEMENT true [get_pblocks pblock_crossing]
