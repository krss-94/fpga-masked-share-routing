`timescale 1ns/1ps
//
// TVLA-instrumented testbench for masked_and_gadget.
//
// Real TVLA needs physical power/EM traces. Without hardware, this uses
// the standard simulation-based proxy from the side-channel literature:
// the Hamming weight (bit-toggle count) of the gadget's internal
// share-bearing registers each cycle, as a stand-in for switching-activity
// power draw. This is NOT a measured leak -- it's a structural leakage
// indicator, same caveat as the switchbox_conflict_detector.py results
// earlier in this project. Label it as such in any writeup.
//
// Two populations, per standard fixed-vs-random TVLA:
//   population 0 (fixed):  logical a=0, b=0, shares randomized
//   population 1 (random): logical a,b independently randomized
//
// Output: tvla_trace.csv, one row per clock cycle, columns:
//   population,cycle,hamming_weight,a_sh0_r,a_sh1_r,b_sh0_r,b_sh1_r,
//   term_sh0,term_cross01,term_cross10,term_sh1,t0_sh0,t0_sh1,
//   q_sh0_reg,q_sh1_reg

module tb_masked_and_gadget_tvla;

    reg clk = 0;
    reg rst = 1;

    reg a_sh0, a_sh1;
    reg b_sh0, b_sh1;
    reg r;
    reg discard_a1, discard_b1;  // RNG-call-count equalizer, see population 0 loop below

    wire q_sh0, q_sh1;

    integer logfile;
    integer cycle_count;
    integer pop_label;
    integer hw;

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

    // Hamming weight of the internal share-bearing signals this cycle --
    // the leakage proxy. Computed after each posedge settles.
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

    integer i;

    initial begin
        logfile = $fopen("tvla_trace.csv", "w");
        $fwrite(logfile, "population,cycle,hamming_weight,a_sh0_r,a_sh1_r,b_sh0_r,b_sh1_r,term_sh0,term_cross01,term_cross10,term_sh1,t0_sh0,t0_sh1\n");
        cycle_count = 0;

        // Explicit seed -- without this, xsim's default $urandom sequence
        // is deterministic and can carry short-range correlation across
        // thousands of sequential calls.
        $srandom(42);

        a_sh0 = 0; a_sh1 = 0;
        b_sh0 = 0; b_sh1 = 0;
        r     = 0;

        #20;
        rst = 0;

        // ------------------------------------------------------------
        // Population 0 (fixed): logical a=0, b=0. Shares randomized,
        // constrained so a_sh0 XOR a_sh1 = 0 and b_sh0 XOR b_sh1 = 0.
        //
        // CRITICAL: draws the exact same 5 $urandom_range calls, in the
        // exact same order, as population 1's loop below -- even though
        // 2 of them (discard_a1, discard_b1) are thrown away. Two runs
        // earlier, population 0 called $urandom_range 3x/cycle while
        // population 1 called it 5x/cycle, so the two populations landed
        // on different phase offsets of the same PRNG stream. Any weak
        // serial correlation in that stream then showed up as a spurious,
        // asymmetric "leak" (once in term_cross01, once in t0_sh1 -- two
        // different signals across two runs, itself a sign of an
        // unstable artifact rather than a real, reproducible effect).
        // Equal RNG call count/order removes that confound entirely.
        // ------------------------------------------------------------
        pop_label = 0;
        for (i = 0; i < 20000; i = i + 1) begin
            @(negedge clk);
            a_sh0      = $urandom_range(0,1);
            discard_a1 = $urandom_range(0,1);
            a_sh1      = a_sh0;
            b_sh0      = $urandom_range(0,1);
            discard_b1 = $urandom_range(0,1);
            b_sh1      = b_sh0;
            r          = $urandom_range(0,1);
            @(posedge clk);
            #1;
            compute_and_log;
        end

        // ------------------------------------------------------------
        // Population 1 (random): a and b independently randomized.
        // ------------------------------------------------------------
        pop_label = 1;
        for (i = 0; i < 20000; i = i + 1) begin
            @(negedge clk);
            a_sh0 = $urandom_range(0,1);
            a_sh1 = $urandom_range(0,1);
            b_sh0 = $urandom_range(0,1);
            b_sh1 = $urandom_range(0,1);
            r     = $urandom_range(0,1);
            @(posedge clk);
            #1;
            compute_and_log;
        end

        $fclose(logfile);
        #20;
        $finish;
    end

endmodule
