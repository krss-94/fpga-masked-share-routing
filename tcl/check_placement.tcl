open_checkpoint placed_routed_and_placement_only.dcp
set cells [get_cells -hierarchical {b_sh0_r_reg b_sh1_r_reg a_sh0_r_reg a_sh1_r_reg}]
foreach c $cells {
    set site [get_property SITE $c]
    puts "[get_property NAME $c] -> $site"
}