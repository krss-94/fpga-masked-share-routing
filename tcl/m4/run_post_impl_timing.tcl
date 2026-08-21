open_checkpoint C:/vivado_work/milestone0/test3_place_route_out/post_route.dcp
create_project -force tvla_timing C:/vivado_work/milestone0/tvla_timing -part xc7a100tcsg324-1
add_files C:/vivado_work/milestone0/tb_masked_and_gadget_tvla_gatelevel.v
set_property top tb_masked_and_gadget_tvla_gatelevel [get_filesets sim_1]

launch_simulation -mode post-implementation -type timing

run all

close_sim -force
exit
