create_project tvla_v3 C:/vivado_work/milestone0/tvla_v3 -part xc7a100tcsg324-1 -force
add_files C:/vivado_work/milestone0/masked_and_gadget.v
add_files C:/vivado_work/milestone0/tb_masked_and_gadget_tvla_v3.v
set_property top tb_masked_and_gadget_tvla_v3 [get_filesets sim_1]
launch_simulation -simset sim_1 -mode behavioral
run all
close_sim -force
exit
