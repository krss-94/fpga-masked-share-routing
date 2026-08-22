`timescale 1ns/1ps
module tb_functional_exhaustive;
    localparam HOLD_CYCLES = 6;
    reg clk = 0;
    reg rst = 1;
    reg a_sh0, a_sh1, b_sh0, b_sh1, r;
    wire q_sh0, q_sh1;
    integer vec;
    integer errors;
    integer checks;
    reg expected_a, expected_b, expected_q, actual_q;

    masked_and_gadget dut (
        .clk(clk), .rst(rst),
        .a_sh0(a_sh0), .a_sh1(a_sh1),
        .b_sh0(b_sh0), .b_sh1(b_sh1),
        .r(r), .q_sh0(q_sh0), .q_sh1(q_sh1)
    );

    always #5 clk = ~clk;

    task apply_and_check(input [4:0] bits);
        begin
            a_sh0 = bits[0]; a_sh1 = bits[1];
            b_sh0 = bits[2]; b_sh1 = bits[3];
            r     = bits[4];
            repeat (HOLD_CYCLES) @(posedge clk);
            expected_a = a_sh0 ^ a_sh1;
            expected_b = b_sh0 ^ b_sh1;
            expected_q = expected_a & expected_b;
            actual_q   = q_sh0 ^ q_sh1;
            checks = checks + 1;
            if (actual_q !== expected_q) begin
                errors = errors + 1;
                $display("FAIL vec=%0d a_sh0=%b a_sh1=%b b_sh0=%b b_sh1=%b r=%b | expected_q=%b | q_sh0=%b q_sh1=%b actual_q=%b",
                          bits, a_sh0, a_sh1, b_sh0, b_sh1, r, expected_q, q_sh0, q_sh1, actual_q);
            end
        end
    endtask

    initial begin
        errors = 0;
        checks = 0;
        a_sh0 = 0; a_sh1 = 0; b_sh0 = 0; b_sh1 = 0; r = 0;
        repeat (4) @(posedge clk);
        rst = 0;
        repeat (4) @(posedge clk);
        for (vec = 0; vec < 32; vec = vec + 1) begin
            apply_and_check(vec[4:0]);
        end
        $display("========================================");
        $display("EXHAUSTIVE FUNCTIONAL CHECK COMPLETE");
        $display("Total vectors checked: %0d / 32", checks);
        $display("Errors: %0d", errors);
        if (errors == 0)
            $display("RESULT: PASS - q_sh0^q_sh1 == a&b for all 32 input combinations");
        else
            $display("RESULT: FAIL - see FAIL lines above");
        $display("========================================");
        $finish;
    end
endmodule
