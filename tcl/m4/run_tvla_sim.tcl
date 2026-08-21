create_project tvla_sim C:/vivado_work/milestone0/tvla_sim -part xc7a100tcsg324-1 -force

add_files C:/vivado_work/milestone0/masked_and_gadget.v
add_files C:/vivado_work/milestone0/tb_masked_and_gadget.v

set_property top tb_masked_and_gadget [get_filesets sim_1]

launch_simulation -simset sim_1 -mode behavioral

# Add the DUT internals that represent share-dependent activity.
add_wave /tb_masked_and_gadget/dut/clk
add_wave /tb_masked_and_gadget/dut/rst
add_wave /tb_masked_and_gadget/dut/a_sh0_r
add_wave /tb_masked_and_gadget/dut/a_sh1_r
add_wave /tb_masked_and_gadget/dut/b_sh0_r
add_wave /tb_masked_and_gadget/dut/b_sh1_r
add_wave /tb_masked_and_gadget/dut/r_r
add_wave /tb_masked_and_gadget/dut/term_sh0
add_wave /tb_masked_and_gadget/dut/term_cross01
add_wave /tb_masked_and_gadget/dut/term_cross10
add_wave /tb_masked_and_gadget/dut/term_sh1
add_wave /tb_masked_and_gadget/dut/t0_sh0
add_wave /tb_masked_and_gadget/dut/t0_sh1
add_wave /tb_masked_and_gadget/dut/q_sh0_reg
add_wave /tb_masked_and_gadget/dut/q_sh1_reg

run all

close_sim
exit
