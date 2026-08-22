open_checkpoint ./test3_place_route_v2_out/post_route.dcp
puts "v2 LUT count: [llength [get_cells -hierarchical -filter {REF_NAME =~ LUT*}]]"
