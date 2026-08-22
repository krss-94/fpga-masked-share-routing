create_pblock pblock_share0
create_pblock pblock_share1

resize_pblock pblock_share0 -add {SLICE_X0Y0:SLICE_X30Y99}
resize_pblock pblock_share1 -add {SLICE_X60Y0:SLICE_X90Y99}

add_cells_to_pblock pblock_share0 [get_cells -hierarchical -filter {NAME =~ *_sh0* || NAME =~ *cross10*}]
add_cells_to_pblock pblock_share1 [get_cells -hierarchical -filter {NAME =~ *_sh1* || NAME =~ *cross01*}]

set_property CONTAIN_ROUTING true [get_pblocks pblock_share0]
set_property CONTAIN_ROUTING true [get_pblocks pblock_share1]
