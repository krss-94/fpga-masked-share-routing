open_checkpoint placed_routed_and_placement_only.dcp
puts "--- pblock_share0_hard members ---"
set c0 [get_cells -of_objects [get_pblocks pblock_share0_hard]]
puts "Count: [llength $c0]"
foreach c $c0 { puts "  [get_property NAME $c]" }

puts "--- pblock_share1_hard members ---"
set c1 [get_cells -of_objects [get_pblocks pblock_share1_hard]]
puts "Count: [llength $c1]"
foreach c $c1 { puts "  [get_property NAME $c]" }