`timescale 1ns/1ps
//
// TVLA-instrumented testbench for masked_and_gadget -- v3.
//
// v1/v2 called Vivado xsim's $urandom_range directly, which turned out
// to have detectable low-bit serial correlation between nearby calls
// (a known weakness of simple LCG-based PRNGs). Three rounds of fixes
// inside the testbench (seeding, matching RNG call-counts between
// populations) failed to eliminate a spurious "leak" in term_cross01 --
// it got STRONGER after matching call counts, which ruled out unequal
// counts as the cause and pointed at the underlying PRNG itself.
//
// v3 sidesteps the problem entirely: all randomness is generated
// externally by gen_tvla_stimulus.py using numpy's PCG64 (a modern,
// well-vetted PRNG with no known low-bit correlation issues -- verified
// directly: a t-test on the exact same bit combination that flagged at
// t=-7.850 under $urandom_range showed t=-0.381 under PCG64). This
// testbench just reads pre-generated rows sequentially from stimulus_v2_fixed11.mem.
// There is no in-simulator call-ordering left to get wrong.
//
// Real TVLA needs physical power/EM traces. Without hardware, this uses
// the standard simulation-based proxy from the side-channel literature:
// Hamming weight (bit-toggle count) of the gadget's internal registers
// each cycle, as a stand-in for switching-activity power draw. This is
// NOT a measured leak -- it's a structural leakage indicator. Label it
// as such in any writeup.
//
// stimulus_v2_fixed11.mem bit layout (MSB to LSB): [population][a_sh0][a_sh1][b_sh0][b_sh1][r]
// Output: tvla_trace_v2_nondegenerate.csv, one row per clock cycle.

module tb_tvla_v2_nondegenerate;

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

    always #5 clk = ~clk;

    task compute_and_log;
        begin
            hw = dut.a_sh0_r + dut.a_sh1_r + dut.b_sh0_r + dut.b_sh1_r
               + dut.term_sh0 + dut.term_cross01 + dut.term_cross10 + dut.term_sh1
               + dut.t0_sh0 + dut.t0_sh1
               + dut.q_sh0_reg + dut.q_sh1_reg;

            $fwrite(logfile, "%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",
                pop_label, cycle_count, hw,
                dut.a_sh0_r, dut.a_sh1_r, dut.b_sh0_r, dut.b_sh1_r,
                dut.term_sh0, dut.term_cross01, dut.term_cross10, dut.term_sh1,
                dut.t0_sh0, dut.t0_sh1);
            cycle_count = cycle_count + 1;
        end
    endtask

    initial begin
        $readmemb("C:/vivado_work/milestone0/security_tests/stimulus_v2_fixed11.mem", stim_mem);

        logfile = $fopen("tvla_trace_v2_nondegenerate.csv", "w");
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
