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
//   _sh0 / _sh1  suffix marks which share a wire, register, or instance
//   belongs to. This revision (v2) makes that convention CONSISTENT across
//   every register and every instance name -- v1 only tagged some signals
//   (t0_sh0/t0_sh1, and the module *type* of the AND instances) while
//   leaving others (a0_r, b1_r, q1_reg, instance names u_and00 etc.)
//   using a bare-digit convention the coverage heuristic's regex could not
//   recognize. That inconsistency, not a physical-implementation failure,
//   was the actual cause of Milestone 0's first low-coverage reading --
//   caught during the mandatory manual coverage.csv inspection, per Stage 1.
//
// Fresh randomness (r / r_sh_r) is deliberately left UNTAGGED with any
// share label. It is not a share of a, b, or q -- it is mask randomness
// that appears, by construction, in both share expressions. Tagging it
// sh0/sh1/cross to inflate the coverage number would be a fabricated
// mapping, which this project's editorial constraint explicitly forbids.
// Its "unmapped" status in coverage.csv is correct and expected, not a bug.
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
    // of a/b in any real use -- for Milestone 0 this is just an input pin).
    // Deliberately left without a share tag -- see module docstring.
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
    //
    // Registers renamed from v1 (a0_r -> a_sh0_r, q1_reg -> q_sh1_reg,
    // etc.) so every share-bearing register carries the sh0/sh1 substring
    // literally, matching the coverage heuristic's regex. r_r intentionally
    // left untagged -- see module docstring.
    // ------------------------------------------------------------------
    (* dont_touch = "true" *) reg a_sh0_r, a_sh1_r, b_sh0_r, b_sh1_r, r_r;
    (* dont_touch = "true" *) reg t0_sh0, t0_sh1;   // intermediate cross terms
    (* dont_touch = "true" *) reg q_sh0_reg, q_sh1_reg;

    always @(posedge clk) begin
        if (rst) begin
            a_sh0_r <= 1'b0; a_sh1_r <= 1'b0;
            b_sh0_r <= 1'b0; b_sh1_r <= 1'b0;
            r_r     <= 1'b0;
        end else begin
            a_sh0_r <= a_sh0; a_sh1_r <= a_sh1;
            b_sh0_r <= b_sh0; b_sh1_r <= b_sh1;
            r_r     <= r;
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
    // in BOTH the module type AND the instance name (v1 only tagged
    // the module type -- RapidWright/Vivado report the instance name
    // on physical cells, e.g. "u_and_sh0/y_INST_0", so the instance
    // name is what the coverage heuristic actually needs to match).

    wire term_sh0, term_cross01, term_cross10, term_sh1;

    (* dont_touch = "true" *) LUT2_and_sh0     u_and_sh0     (.a(a_sh0_r), .b(b_sh0_r), .y(term_sh0));
    (* dont_touch = "true" *) LUT2_and_cross01 u_and_cross01 (.a(a_sh0_r), .b(b_sh1_r), .y(term_cross01));
    (* dont_touch = "true" *) LUT2_and_cross10 u_and_cross10 (.a(a_sh1_r), .b(b_sh0_r), .y(term_cross10));
    (* dont_touch = "true" *) LUT2_and_sh1     u_and_sh1     (.a(a_sh1_r), .b(b_sh1_r), .y(term_sh1));

    always @(posedge clk) begin
        if (rst) begin
            t0_sh0     <= 1'b0;
            t0_sh1     <= 1'b0;
            q_sh0_reg  <= 1'b0;
            q_sh1_reg  <= 1'b0;
        end else begin
            t0_sh0    <= term_sh0 ^ r_r;
            t0_sh1    <= term_sh1 ^ term_cross01 ^ term_cross10 ^ r_r;
            q_sh0_reg <= t0_sh0;
            q_sh1_reg <= t0_sh1;
        end
    end

    assign q_sh0 = q_sh0_reg;
    assign q_sh1 = q_sh1_reg;

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
