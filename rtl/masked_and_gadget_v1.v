// ============================================================================
// Milestone 0 test artifact: minimal 2-share, first-order masked AND gadget
// (Trichina-style ISW AND gate, single fresh mask bit per evaluation)
//
// Purpose: smallest possible design that exercises the share-boundary ->
// physical-object mapping problem identified in Phase 13.0, Decision 3.
// Deliberately NOT part of a full ML-KEM/ML-DSA design -- this exists only
// to measure Share Mapping Coverage before committing to the full pipeline.
//
// Shares are tagged in signal/instance names by convention:
//   _sh0 / _sh1  suffix marks which share a wire or register belongs to.
//
// IMPORTANT: this naming convention is TEST INSTRUMENTATION for
// Milestone 0, not a property the methodology (Phase 11/12) depends
// on. The eventual M2 Share Correlator should exploit hierarchical
// netlist/proof metadata directly where available; naming should
// only ever serve as a fallback or benchmark convenience, never the
// mechanism itself. Do not let this convention silently become the
// permanent share-correlation strategy.
// ============================================================================

module masked_and_gadget (
    input  wire clk,
    input  wire rst,

    // Secret input shares: a = a_sh0 XOR a_sh1, b = b_sh0 XOR b_sh1
    input  wire a_sh0,
    input  wire a_sh1,
    input  wire b_sh0,
    input  wire b_sh1,

    // Fresh randomness for this AND gadget (must be uniform, independent
    // of a/b in any real use -- for Milestone 0 this is just an input pin)
    input  wire r,

    // Output shares: q = a AND b = q_sh0 XOR q_sh1
    output wire q_sh0,
    output wire q_sh1
);

    // ------------------------------------------------------------------
    // DONT_TOUCH applied at the module boundary and at internal
    // share-critical registers, per Decision 3: KEEP_HIERARCHY alone
    // would not survive routing, DONT_TOUCH persists through both
    // synthesis and place-and-route.
    // ------------------------------------------------------------------
    (* dont_touch = "true" *) reg a0_r, a1_r, b0_r, b1_r, r_r;
    (* dont_touch = "true" *) reg t0_sh0, t0_sh1;   // intermediate cross terms
    (* dont_touch = "true" *) reg q0_reg, q1_reg;

    always @(posedge clk) begin
        if (rst) begin
            a0_r <= 1'b0; a1_r <= 1'b0;
            b0_r <= 1'b0; b1_r <= 1'b0;
            r_r  <= 1'b0;
        end else begin
            a0_r <= a_sh0; a1_r <= a_sh1;
            b0_r <= b_sh0; b1_r <= b_sh1;
            r_r  <= r;
        end
    end

    // Trichina AND gadget, expanded explicitly (no resource sharing
    // implied in RTL -- whether the synthesizer preserves this
    // structure is exactly what Milestone 0 measures):
    //
    //   q_sh0 = (a0 & b0) ^ r
    //   q_sh1 = (a1 & b1) ^ ((a0 & b1) ^ (a1 & b0) ^ r)
    //
    // Each product term below is tagged by which shares it touches,
    // in the *instance* name (not just the signal name), so that
    // LUT-level RapidWright cells retain traceable provenance.

    wire term_00, term_01, term_10, term_11;

    (* dont_touch = "true" *) LUT2_and_sh0 u_and00 (.a(a0_r), .b(b0_r), .y(term_00));
    (* dont_touch = "true" *) LUT2_and_cross01 u_and01 (.a(a0_r), .b(b1_r), .y(term_01));
    (* dont_touch = "true" *) LUT2_and_cross10 u_and10 (.a(a1_r), .b(b0_r), .y(term_10));
    (* dont_touch = "true" *) LUT2_and_sh1 u_and11 (.a(a1_r), .b(b1_r), .y(term_11));

    always @(posedge clk) begin
        if (rst) begin
            t0_sh0 <= 1'b0;
            t0_sh1 <= 1'b0;
            q0_reg <= 1'b0;
            q1_reg <= 1'b0;
        end else begin
            t0_sh0 <= term_00 ^ r_r;
            t0_sh1 <= term_11 ^ term_01 ^ term_10 ^ r_r;
            q0_reg <= t0_sh0;
            q1_reg <= t0_sh1;
        end
    end

    assign q_sh0 = q0_reg;
    assign q_sh1 = q1_reg;

endmodule

// ----------------------------------------------------------------------
// Named leaf primitives so RapidWright/Vivado cell names carry explicit
// share-boundary information all the way to the physical netlist.
// Naming convention: "sh0"/"sh1" = single-share term (safe to merge
// with same-share logic), "cross01"/"cross10" = cross-share term
// (must remain traceable -- these are the highest-risk structures
// for Decision 3's injective-mapping requirement).
// ----------------------------------------------------------------------
module LUT2_and_sh0(input a, input b, output y);
    assign y = a & b;
endmodule

module LUT2_and_sh1(input a, input b, output y);
    assign y = a & b;
endmodule

module LUT2_and_cross01(input a, input b, output y);
    assign y = a & b;
endmodule

module LUT2_and_cross10(input a, input b, output y);
    assign y = a & b;
endmodule
