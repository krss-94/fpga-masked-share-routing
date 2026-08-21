// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2026 Advanced Micro Devices, Inc. All Rights Reserved.
// --------------------------------------------------------------------------------
// Tool Version: Vivado v.2026.1 (win64) Build 6511674 Tue Jun 16 11:02:23 MDT 2026
// Date        : Thu Aug 20 13:11:56 2026
// Host        : KRSSEFD5 running 64-bit major release  (build 9200)
// Command     : write_verilog -force -mode timesim -file ./test5_gatelevel_out/masked_and_gadget_timesim_nosdf.v
// Design      : masked_and_gadget
// Purpose     : This verilog netlist is a timing simulation representation of the design and should not be modified or
//               synthesized. Please ensure that this netlist is used with the corresponding SDF file.
// Device      : xc7a100tcsg324-1
// --------------------------------------------------------------------------------
`timescale 1 ps / 1 ps
`define XIL_TIMING

module LUT2_and_cross01
   (a,
    b,
    y);
  input a;
  input b;
  output y;

  wire a;
  wire b;
  wire y;

  LUT2 #(
    .INIT(4'h8)) 
    y_INST_0
       (.I0(a),
        .I1(b),
        .O(y));
endmodule

module LUT2_and_cross10
   (a,
    b,
    y);
  input a;
  input b;
  output y;

  wire a;
  wire b;
  wire y;

  LUT2 #(
    .INIT(4'h8)) 
    y_INST_0
       (.I0(a),
        .I1(b),
        .O(y));
endmodule

module LUT2_and_sh0
   (a,
    b,
    y);
  input a;
  input b;
  output y;

  wire a;
  wire b;
  wire y;

  LUT2 #(
    .INIT(4'h8)) 
    y_INST_0
       (.I0(a),
        .I1(b),
        .O(y));
endmodule

module LUT2_and_sh1
   (a,
    b,
    y);
  input a;
  input b;
  output y;

  wire a;
  wire b;
  wire y;

  LUT2 #(
    .INIT(4'h8)) 
    y_INST_0
       (.I0(a),
        .I1(b),
        .O(y));
endmodule

(* ECO_CHECKSUM = "1b3a9d04" *) (* \and  = "1" *) (* place = "1" *) 
(* NotValidForBitStream *)
(* \DesignAttr:ENABLE_NOC_NETLIST_VIEW  *) 
(* \DesignAttr:ENABLE_AIE_NETLIST_VIEW  *) 
(* \DesignAttr:TELEMETRY_DATA  = "{\n  \"Design Flow Data\": {\n    \"Implementation\": {\n      \"Opt Design\": {\n        \"Run Time\": \"15 seconds\"\n      },\n      \"Place Design\": {\n        \"Run Time\": \"5.820000 seconds\"\n      },\n      \"Route Design\": {\n        \"Run Time\": \"62.176000 seconds\"\n      }\n    }\n  }\n}" *) 
module masked_and_gadget
   (clk,
    rst,
    a_sh0,
    a_sh1,
    b_sh0,
    b_sh1,
    r,
    q_sh0,
    q_sh1);
  input clk;
  input rst;
  input a_sh0;
  input a_sh1;
  input b_sh0;
  input b_sh1;
  input r;
  output q_sh0;
  output q_sh1;

  wire a_sh0;
  (* DONT_TOUCH *) wire a_sh0_r;
  wire a_sh1;
  (* DONT_TOUCH *) wire a_sh1_r;
  wire b_sh0;
  (* DONT_TOUCH *) wire b_sh0_r;
  wire b_sh1;
  (* DONT_TOUCH *) wire b_sh1_r;
  wire clk;
  (* DONT_TOUCH *) wire q_sh0_reg;
  (* DONT_TOUCH *) wire q_sh1_reg;
  wire r;
  (* DONT_TOUCH *) wire r_r;
  wire rst;
  (* DONT_TOUCH *) wire t0_sh0;
  wire t0_sh0_reg0;
  (* DONT_TOUCH *) wire t0_sh1;
  wire t0_sh1_reg0;
  wire term_cross01;
  wire term_cross10;
  wire term_sh0;
  wire term_sh1;

  assign q_sh0 = q_sh0_reg;
  assign q_sh1 = q_sh1_reg;
  (* DONT_TOUCH *) 
  (* KEEP = "yes" *) 
  FDRE #(
    .INIT(1'b0)) 
    a_sh0_r_reg
       (.C(clk),
        .CE(1'b1),
        .D(a_sh0),
        .Q(a_sh0_r),
        .R(rst));
  (* DONT_TOUCH *) 
  (* KEEP = "yes" *) 
  FDRE #(
    .INIT(1'b0)) 
    a_sh1_r_reg
       (.C(clk),
        .CE(1'b1),
        .D(a_sh1),
        .Q(a_sh1_r),
        .R(rst));
  (* DONT_TOUCH *) 
  (* KEEP = "yes" *) 
  FDRE #(
    .INIT(1'b0)) 
    b_sh0_r_reg
       (.C(clk),
        .CE(1'b1),
        .D(b_sh0),
        .Q(b_sh0_r),
        .R(rst));
  (* DONT_TOUCH *) 
  (* KEEP = "yes" *) 
  FDRE #(
    .INIT(1'b0)) 
    b_sh1_r_reg
       (.C(clk),
        .CE(1'b1),
        .D(b_sh1),
        .Q(b_sh1_r),
        .R(rst));
  (* DONT_TOUCH *) 
  (* KEEP = "yes" *) 
  FDRE #(
    .INIT(1'b0)) 
    q_sh0_reg_reg
       (.C(clk),
        .CE(1'b1),
        .D(t0_sh0),
        .Q(q_sh0_reg),
        .R(rst));
  (* DONT_TOUCH *) 
  (* KEEP = "yes" *) 
  FDRE #(
    .INIT(1'b0)) 
    q_sh1_reg_reg
       (.C(clk),
        .CE(1'b1),
        .D(t0_sh1),
        .Q(q_sh1_reg),
        .R(rst));
  (* DONT_TOUCH *) 
  (* KEEP = "yes" *) 
  FDRE #(
    .INIT(1'b0)) 
    r_r_reg
       (.C(clk),
        .CE(1'b1),
        .D(r),
        .Q(r_r),
        .R(rst));
  LUT2 #(
    .INIT(4'h6)) 
    t0_sh0_i_1
       (.I0(r_r),
        .I1(term_sh0),
        .O(t0_sh0_reg0));
  (* DONT_TOUCH *) 
  (* KEEP = "yes" *) 
  FDRE #(
    .INIT(1'b0)) 
    t0_sh0_reg
       (.C(clk),
        .CE(1'b1),
        .D(t0_sh0_reg0),
        .Q(t0_sh0),
        .R(rst));
  LUT4 #(
    .INIT(16'h6996)) 
    t0_sh1_i_1
       (.I0(term_cross10),
        .I1(term_cross01),
        .I2(term_sh1),
        .I3(r_r),
        .O(t0_sh1_reg0));
  (* DONT_TOUCH *) 
  (* KEEP = "yes" *) 
  FDRE #(
    .INIT(1'b0)) 
    t0_sh1_reg
       (.C(clk),
        .CE(1'b1),
        .D(t0_sh1_reg0),
        .Q(t0_sh1),
        .R(rst));
  (* DONT_TOUCH *) 
  LUT2_and_cross01 u_and_cross01
       (.a(a_sh0_r),
        .b(b_sh1_r),
        .y(term_cross01));
  (* DONT_TOUCH *) 
  LUT2_and_cross10 u_and_cross10
       (.a(a_sh1_r),
        .b(b_sh0_r),
        .y(term_cross10));
  (* DONT_TOUCH *) 
  LUT2_and_sh0 u_and_sh0
       (.a(a_sh0_r),
        .b(b_sh0_r),
        .y(term_sh0));
  (* DONT_TOUCH *) 
  LUT2_and_sh1 u_and_sh1
       (.a(a_sh1_r),
        .b(b_sh1_r),
        .y(term_sh1));
endmodule
`ifndef GLBL
`define GLBL
`timescale  1 ps / 1 ps

module glbl ();

    parameter ROC_WIDTH = 100000;
    parameter TOC_WIDTH = 0;
    parameter GRES_WIDTH = 10000;
    parameter GRES_START = 10000;

//--------   STARTUP Globals --------------
    wire GSR;
    wire GTS;
    wire GWE;
    wire PRLD;
    wire GRESTORE;
    tri1 p_up_tmp;
    tri (weak1, strong0) PLL_LOCKG = p_up_tmp;

    wire PROGB_GLBL;
    wire CCLKO_GLBL;
    wire FCSBO_GLBL;
    wire [3:0] DO_GLBL;
    wire [3:0] DI_GLBL;
   
    reg GSR_int;
    reg GTS_int;
    reg PRLD_int;
    reg GRESTORE_int;

//--------   JTAG Globals --------------
    wire JTAG_TDO_GLBL;
    wire JTAG_TCK_GLBL;
    wire JTAG_TDI_GLBL;
    wire JTAG_TMS_GLBL;
    wire JTAG_TRST_GLBL;

    reg JTAG_CAPTURE_GLBL;
    reg JTAG_RESET_GLBL;
    reg JTAG_SHIFT_GLBL;
    reg JTAG_UPDATE_GLBL;
    reg JTAG_RUNTEST_GLBL;

    reg JTAG_SEL1_GLBL = 0;
    reg JTAG_SEL2_GLBL = 0 ;
    reg JTAG_SEL3_GLBL = 0;
    reg JTAG_SEL4_GLBL = 0;

    reg JTAG_USER_TDO1_GLBL = 1'bz;
    reg JTAG_USER_TDO2_GLBL = 1'bz;
    reg JTAG_USER_TDO3_GLBL = 1'bz;
    reg JTAG_USER_TDO4_GLBL = 1'bz;

    assign (strong1, weak0) GSR = GSR_int;
    assign (strong1, weak0) GTS = GTS_int;
    assign (weak1, weak0) PRLD = PRLD_int;
    assign (strong1, weak0) GRESTORE = GRESTORE_int;

    initial begin
	GSR_int = 1'b1;
	PRLD_int = 1'b1;
	#(ROC_WIDTH)
	GSR_int = 1'b0;
	PRLD_int = 1'b0;
    end

    initial begin
	GTS_int = 1'b1;
	#(TOC_WIDTH)
	GTS_int = 1'b0;
    end

    initial begin 
	GRESTORE_int = 1'b0;
	#(GRES_START);
	GRESTORE_int = 1'b1;
	#(GRES_WIDTH);
	GRESTORE_int = 1'b0;
    end

endmodule
`endif
