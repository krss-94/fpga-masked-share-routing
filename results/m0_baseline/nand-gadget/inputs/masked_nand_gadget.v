// SHARE_TAGGING_CONVENTION v1
// Shares: 2
// Inputs:  a_sh0, a_sh1, b_sh0, b_sh1
// Outputs: q_sh0, q_sh1
// Randomness: r_r (fresh mask, required - NAND is nonlinear like AND)
//
// Masked NAND gadget. NAND = NOT(AND), so this reuses the same
// Boolean-masked-AND structure as masked_and_gadget.v (Milestone 0),
// then inverts one share to fold in the NOT for free (inverting a
// single share inverts the reconstructed secret: if q = q_sh0 XOR q_sh1,
// then NOT(q) = NOT(q_sh0) XOR q_sh1 - only one share needs the invert,
// not both, so masking security is unaffected).
//
// This lets us test whether the AND gadget's physical-mapping pattern
// (cross-share term present, fresh randomness required, full coverage)
// generalizes to a second nonlinear gate, or was AND-specific.

module masked_nand_gadget(
    input        clk,
    input        a_sh0,
    input        a_sh1,
    input        b_sh0,
    input        b_sh1,
    input        r_r,       // fresh randomness for the AND-gadget core
    output reg   q_sh0,
    output reg   q_sh1
);
    wire and_sh0, and_sh1;
    wire cross01, cross10;

    // Same domain-oriented masked-AND core as Milestone 0:
    // and_sh0 = (a_sh0 & b_sh0) ^ r_r
    // and_sh1 = (a_sh1 & b_sh1) ^ (cross01 ^ cross10 correction) ^ r_r
    assign cross01 = a_sh0 & b_sh1;
    assign cross10 = a_sh1 & b_sh0;

    assign and_sh0 = (a_sh0 & b_sh0) ^ r_r;
    assign and_sh1 = (a_sh1 & b_sh1) ^ cross01 ^ cross10 ^ r_r;

    always @(posedge clk) begin
        // NAND = NOT(AND). Invert only share 0's register input -
        // reconstruction NOT(q_sh0 XOR q_sh1) = (~q_sh0) XOR q_sh1 holds,
        // so this single-share invert is sufficient and does not
        // require additional randomness or break masking security.
        q_sh0 <= ~and_sh0;
        q_sh1 <= and_sh1;
    end
endmodule
