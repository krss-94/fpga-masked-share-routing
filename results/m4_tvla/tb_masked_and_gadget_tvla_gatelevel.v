`timescale 1ns/1ps
//
// TEST 5: Gate-level TVLA testbench.
//
// Direct adaptation of tb_masked_and_gadget_tvla_v3.v. The ONLY changes
// from the original are:
//   1. DUT instantiation points at the post-route netlist
//      (masked_and_gadget_timesim.v) instead of RTL, with glbl added
//      (required for Unisim FDRE/LUT primitives).
//   2. Internal probes (dut.a_sh0_r etc, which were flat RTL wires)
//      are remapped to the physical pin paths confirmed in TEST 3/4:
//      register Q pins and LUT O pins, per probe_paths.rpt.
// Stimulus reading, population labeling, sampling edges, hamming_weight
// composition (12 terms including q_sh0_reg/q_sh1_reg), and CSV schema
// are UNCHANGED -- this reads the SAME stimulus.mem as TEST 1 so the
// two runs are a controlled comparison (same stimulus, different
// physical implementation), not two different experiments.
//
// Compile/elaborate/run (adjust glbl.v path to your Vivado install):
//   xvlog -sv tb_masked_and_gadget_tvla_gatelevel.v
//   xvlog test5_gatelevel_out/masked_and_gadget_timesim.v
//   xvlog "C:/AMDDesignTools/2026.1/Vivado/data/verilog/src/glbl.v"
//   xelab -debug typical tb_masked_and_gadget_tvla_gatelevel glbl ^
//         -s gatelevel_tvla_sim -L unisims_ver -L unifast_ver -L secureip ^
//         -sdfmax "tb_masked_and_gadget_tvla_gatelevel.dut=test5_gatelevel_out/masked_and_gadget_timesim.sdf"
//   xsim gatelevel_tvla_sim -runall
//
// NOTE: the -sdfmax instance path (tb...gatelevel.dut) must match your
// actual DUT instance name below. If xelab complains it can't find the
// instance to annotate, run without -sdfmax first to confirm functional
// correctness, then fix the instance path and re-add SDF annotation.

module tb_masked_and_gadget_tvla_gatelevel;

    reg clk = 0;
    reg rst = 1;

    reg a_sh0, a_sh1;
    reg b_sh0, b_sh1;
    reg r;

    wire q_sh0, q_sh1;

    integer logfile;
    integer cycle_count;
    integer pop_label;
    integer hw;
    integer i;

    parameter NUM_ROWS = 40000;
    reg [5:0] stim_mem [0:NUM_ROWS-1];

    // ------------------------------------------------------------------
    // DUT: post-route physical netlist (module name unchanged by
    // write_verilog -mode timesim -- still masked_and_gadget).
    // ------------------------------------------------------------------
    masked_and_gadget dut (
        .clk(clk),
        .rst(rst),
        .a_sh0(a_sh0),
        .a_sh1(a_sh1),
        .b_sh0(b_sh0),
        .b_sh1(b_sh1),
        .r(r),
        .q_sh0(q_sh0),
        .q_sh1(q_sh1)
    );

    // Required for Unisim primitive simulation (FDRE/LUT reference
    // global set/reset internally even when unused by the design).
    glbl glbl();

    always #5 clk = ~clk;

    // ------------------------------------------------------------------
    // Physical probes, confirmed paths from TEST 3/4 (not guessed):
    //   register outputs -> .Q pin
    //   LUT2 outputs (term_* combinational terms) -> .O pin
    // ------------------------------------------------------------------
    task compute_and_log;
        begin
            hw = dut.a_sh0_r_reg.Q + dut.a_sh1_r_reg.Q
               + dut.b_sh0_r_reg.Q + dut.b_sh1_r_reg.Q
               + dut.u_and_sh0.y_INST_0.O + dut.u_and_cross01.y_INST_0.O
               + dut.u_and_cross10.y_INST_0.O + dut.u_and_sh1.y_INST_0.O
               + dut.t0_sh0_reg.Q + dut.t0_sh1_reg.Q
               + dut.q_sh0_reg_reg.Q + dut.q_sh1_reg_reg.Q;

            $fwrite(logfile, "%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",
                pop_label, cycle_count, hw,
                dut.a_sh0_r_reg.Q, dut.a_sh1_r_reg.Q,
                dut.b_sh0_r_reg.Q, dut.b_sh1_r_reg.Q,
                dut.u_and_sh0.y_INST_0.O, dut.u_and_cross01.y_INST_0.O,
                dut.u_and_cross10.y_INST_0.O, dut.u_and_sh1.y_INST_0.O,
                dut.t0_sh0_reg.Q, dut.t0_sh1_reg.Q);
            cycle_count = cycle_count + 1;
        end
    endtask

    initial begin
        // SAME stimulus file as TEST 1 -- controlled comparison.
        $readmemb("C:/vivado_work/milestone0/stimulus.mem", stim_mem);

        logfile = $fopen("tvla_trace_gatelevel.csv", "w");
        $fwrite(logfile, "population,cycle,hamming_weight,a_sh0_r,a_sh1_r,b_sh0_r,b_sh1_r,term_sh0,term_cross01,term_cross10,term_sh1,t0_sh0,t0_sh1\n");
        cycle_count = 0;

        a_sh0 = 0; a_sh1 = 0;
        b_sh0 = 0; b_sh1 = 0;
        r     = 0;

        #20;
        rst = 0;

        for (i = 0; i < NUM_ROWS; i = i + 1) begin
            @(negedge clk);
            pop_label = stim_mem[i][5];
            a_sh0     = stim_mem[i][4];
            a_sh1     = stim_mem[i][3];
            b_sh0     = stim_mem[i][2];
            b_sh1     = stim_mem[i][1];
            r         = stim_mem[i][0];
            @(posedge clk);
            #1;
            compute_and_log;
        end

        $fclose(logfile);
        #20;
        $finish;
    end

endmodule
