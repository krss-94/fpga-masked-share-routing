open_checkpoint ./test3_place_route_out/post_route.dcp
write_verilog -force -mode timesim -file ./test5_gatelevel_out/masked_and_gadget_timesim_nosdf.v
puts "Done: masked_and_gadget_timesim_nosdf.v written, no embedded SDF annotation."
