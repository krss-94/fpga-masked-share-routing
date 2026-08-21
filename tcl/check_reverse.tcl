open_checkpoint placed_routed_and_placement_only.dcp
set c [get_cells a_sh1_r_reg]
puts "Cell: [get_property NAME $c]"
puts "Site: [get_property SITE $c]"
puts "Pblock (reverse lookup): [get_pblocks -of_objects $c]"
puts "IS_SOFT on share1: [get_property IS_SOFT [get_pblocks pblock_share1_hard]]"
puts "EXCLUDE_PLACEMENT on share1: [get_property EXCLUDE_PLACEMENT [get_pblocks pblock_share1_hard]]"