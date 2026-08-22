# NOTE: SDF post-route timing simulation requires simprims_ver

Does not modify any existing .tcl/.v file. This is a companion note.

## Symptom
ERROR: [XSIM 43-3462] Unable to annotate SDF delays in the design.
preceded by warnings for every FDRE/LUT instance, when running xelab
with -L unisims_ver -L unifast_ver (the library set documented in
tb_masked_and_gadget_tvla_gatelevel.v's own header comment) against a
post-route timing netlist plus its companion .sdf file.

## Root cause
unisims_ver / unifast_ver are behavioral/functional simulation
libraries -- no specify timing-check blocks for SDF back-annotation.
simprims_ver is the library built for post-route SDF-annotated timing
simulation. This matches what Vivado's own launch_simulation -mode
post-implementation -type timing generates automatically
(-L xil_defaultlib -L simprims_ver -L secureip) when it has a valid
implementation run.

Two other candidates were tested and ruled out first:
- unimacro_ver vs unifast_ver swap: no effect, identical failure.
- The xil_defaultlib.glbl elaboration failure in run_post_impl_timing.tcl
  is a SEPARATE issue (missing implementation-run context for
  project-mode auto-discovery of glbl.v), not the SDF annotation cause.

## Working command (confirmed 2026-08-21/22)
xvlog -sv tb_<name>.v
xvlog <path>/masked_and_gadget_timesim.v
xvlog "<vivado_install>/data/verilog/src/glbl.v"
xelab --relax -debug typical tb_<name> glbl -s <snapshot> -L simprims_ver -L secureip
xsim <snapshot> -runall -log <log>.log

Result: SDF backannotation was successful, ran to $finish, no errors.

## Recommendation
Update tb_masked_and_gadget_tvla_gatelevel.v's header-comment recipe to
use -L simprims_ver -L secureip instead of
-L unisims_ver -L unifast_ver -L secureip, and fix
run_post_impl_timing.tcl to call open_run before launch_simulation.
