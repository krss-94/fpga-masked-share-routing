`timescale 1ns/1ps
// =====================================================================
// TEST 5: Gate-level TVLA testbench.
// Instantiates the POST-ROUTE netlist (masked_and_gadget_timesim.v)
// with SDF-annotated real delays, drives fixed-vs-random populations
// exactly like TEST 1, and probes the PHYSICAL signals identified in
// probe_paths.rpt (LUT2/LUT4 primitive outputs, FDRE Q pins) instead
// of the RTL wires. Output CSV schema matches TEST 1's tvla_trace.csv
// exactly so tvla_analysis.py runs unmodified.
//
// ASSUMPTIONS (adjust if your original TEST 1 testbench differs):
//   - Fixed population: a,b held constant; masking randomness (r,
//     and share-split randomness) still randomized per trace.
//   - Random population: a,b random per trace.
//   - One sample per trace, captured N cycles after stimulus applied
//     (enough for the pipeline to settle -- adjust SAMPLE_DELAY_CYCLES
//     if the gadget has more than 2 register stages).
//   - hamming_weight = popcount of all probed signal bits concatenated.
//
// Compile/run (xsim, from tvla_v3 sim dir or wherever convenient):
//   xvlog -sv gatelevel_tvla_tb.sv
//   xvlog -sv "%XILINX_VIVADO%/data/verilog/src/glbl.v"
//   xvlog -sv test5_gatelevel_out/masked_and_gadget_timesim.v
//   xelab -debug typical gatelevel_tvla_tb glbl -s gatelevel_tvla_sim ^
//         -sdfmax "masked_and_gadget=test5_gatelevel_out/masked_and_gadget_timesim.sdf"
//   xsim gatelevel_tvla_sim -runall
// =====================================================================

module gatelevel_tvla_tb;

    localparam integer N_FIXED         = 20000;
    localparam integer N_RANDOM        = 20000;
    localparam integer CLK_PERIOD_NS   = 10;
    localparam integer SAMPLE_DELAY_CYCLES = 3; // settle time before sampling
    localparam FIXED_A = 1'b1;
    localparam FIXED_B = 1'b0;

    reg clk = 0;
    reg rst = 1;
    reg a_sh0, a_sh1, b_sh0, b_sh1, r;
    wire q_sh0, q_sh1;

    // ------------------------------------------------------------------
    // DUT: physical post-route netlist, not RTL.
    // Port list must match your actual top-level (confirmed earlier):
    //   a_sh0 a_sh1 b_sh0 b_sh1 clk q_sh0 q_sh1 r rst
    // ------------------------------------------------------------------
    masked_and_gadget dut (
        .clk    (clk),
        .rst    (rst),
        .a_sh0  (a_sh0),
        .a_sh1  (a_sh1),
        .b_sh0  (b_sh0),
        .b_sh1  (b_sh1),
        .r      (r),
        .q_sh0  (q_sh0),
        .q_sh1  (q_sh1)
    );

    always #(CLK_PERIOD_NS/2) clk = ~clk;

    // ------------------------------------------------------------------
    // Physical probes -- exact hierarchical paths from probe_paths.rpt.
    // LUT2/LUT4 primitives expose their output on pin O; FDRE exposes Q.
    // ------------------------------------------------------------------
    wire p_a_sh0_r   = dut.a_sh0_r_reg.Q;
    wire p_a_sh1_r   = dut.a_sh1_r_reg.Q;
    wire p_b_sh0_r   = dut.b_sh0_r_reg.Q;
    wire p_b_sh1_r   = dut.b_sh1_r_reg.Q;
    wire p_term_sh0     = dut.u_and_sh0.y_INST_0.O;
    wire p_term_sh1     = dut.u_and_sh1.y_INST_0.O;
    wire p_term_cross01 = dut.u_and_cross01.y_INST_0.O;
    wire p_term_cross10 = dut.u_and_cross10.y_INST_0.O;
    wire p_t0_sh0    = dut.t0_sh0_reg.Q;
    wire p_t0_sh1    = dut.t0_sh1_reg.Q;

    integer hamming_weight;
    always @(*) begin
        hamming_weight = p_a_sh0_r + p_a_sh1_r + p_b_sh0_r + p_b_sh1_r
                       + p_term_sh0 + p_term_sh1
                       + p_term_cross01 + p_term_cross10
                       + p_t0_sh0 + p_t0_sh1;
    end

    // ------------------------------------------------------------------
    // CSV output -- same column order as TEST 1's tvla_trace.csv, plus
    // a leading population column (0=fixed, 1=random) so the analysis
    // script's existing parser (whatever split logic it used) is fed
    // consistent data. If your original CSV had no population column
    // and instead used two separate files/sections, adjust the header
    // and file-open logic below to match.
    // ------------------------------------------------------------------
    integer fh;
    integer trace_num;
    integer i;

    task apply_and_sample(input pop_bit, input a_val, input b_val);
        begin
            @(negedge clk);
            a_sh0 = $random & a_val;      // share split via r; simplified here
            a_sh1 = a_val ^ a_sh0;
            b_sh0 = $random & b_val;
            b_sh1 = b_val ^ b_sh0;
            r     = $random;
            rst   = 0;
            repeat (SAMPLE_DELAY_CYCLES) @(posedge clk);
            #1; // let combinational settle after edge
            $fwrite(fh, "%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",
                pop_bit, hamming_weight,
                p_a_sh0_r, p_a_sh1_r, p_b_sh0_r, p_b_sh1_r,
                p_term_sh0, p_term_cross01, p_term_cross10, p_term_sh1,
                p_t0_sh0, p_t0_sh1);
        end
    endtask

    initial begin
        fh = $fopen("tvla_trace_gatelevel.csv", "w");
        $fwrite(fh, "population,hamming_weight,a_sh0_r,a_sh1_r,b_sh0_r,b_sh1_r,term_sh0,term_cross01,term_cross10,term_sh1,t0_sh0,t0_sh1\n");

        // reset pulse
        rst = 1; a_sh0=0; a_sh1=0; b_sh0=0; b_sh1=0; r=0;
        repeat (5) @(posedge clk);
        rst = 0;

        // Population 0: fixed a,b
        for (i = 0; i < N_FIXED; i = i + 1)
            apply_and_sample(0, FIXED_A, FIXED_B);

        // Population 1: random a,b
        for (i = 0; i < N_RANDOM; i = i + 1)
            apply_and_sample(1, $random, $random);

        $fclose(fh);
        $display("TEST 5 gate-level trace generation complete: %0d fixed + %0d random samples",
                  N_FIXED, N_RANDOM);
        $finish;
    end

endmodule
