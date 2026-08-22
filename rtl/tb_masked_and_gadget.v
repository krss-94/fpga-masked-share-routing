`timescale 1ns/1ps

module tb_masked_and_gadget;

    reg clk = 0;
    reg rst = 1;

    reg a_sh0, a_sh1;
    reg b_sh0, b_sh1;
    reg r;

    wire q_sh0, q_sh1;

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

    integer i;

    initial begin
        a_sh0 = 0;
        a_sh1 = 0;
        b_sh0 = 0;
        b_sh1 = 0;
        r     = 0;

        #20;
        rst = 0;

        // ------------------------------------------------------------
        // TVLA population 1: fixed secret
        //
        // Fixed logical values:
        //   a = 0
        //   b = 0
        //
        // Shares are randomized while preserving the logical value.
        // ------------------------------------------------------------
        for (i = 0; i < 5000; i = i + 1) begin
            @(negedge clk);

            a_sh0 = $urandom_range(0,1);
            a_sh1 = a_sh0;       // a_sh0 XOR a_sh1 = 0

            b_sh0 = $urandom_range(0,1);
            b_sh1 = b_sh0;       // b_sh0 XOR b_sh1 = 0

            r = $urandom_range(0,1);
        end

        // ------------------------------------------------------------
        // TVLA population 2: random secret
        //
        // Logical a and b are randomized independently.
        // Shares remain properly randomized.
        // ------------------------------------------------------------
        for (i = 0; i < 5000; i = i + 1) begin
            @(negedge clk);

            a_sh0 = $urandom_range(0,1);
            a_sh1 = $urandom_range(0,1);

            b_sh0 = $urandom_range(0,1);
            b_sh1 = $urandom_range(0,1);

            r = $urandom_range(0,1);
        end

        #20;
        $finish;
    end

endmodule
