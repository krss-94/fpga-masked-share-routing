// SHARE_TAGGING_CONVENTION v1
// Shares: 2
// Inputs:  a_sh0, a_sh1, b_sh0, b_sh1
// Outputs: q_sh0, q_sh1
// Randomness: none (XOR is linear, no randomness required)
//
// Masked XOR gadget. Because XOR is linear, each share is computed
// independently with no cross-share term and no fresh randomness -
// this is a real, textbook-correct masked linear gadget, not a
// simplification. Registered outputs to mirror the structure of
// masked_and_gadget.v (Milestone 0) so the two are directly comparable
// in coverage results.

module masked_xor_gadget(
    input        clk,
    input        a_sh0,
    input        a_sh1,
    input        b_sh0,
    input        b_sh1,
    output reg   q_sh0,
    output reg   q_sh1
);
    always @(posedge clk) begin
        q_sh0 <= a_sh0 ^ b_sh0;
        q_sh1 <= a_sh1 ^ b_sh1;
    end
endmodule
