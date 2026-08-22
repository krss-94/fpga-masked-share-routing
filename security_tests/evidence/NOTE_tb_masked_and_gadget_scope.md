# NOTE: tb_masked_and_gadget.v - scope clarification

Does not modify tb_masked_and_gadget.v. This is a companion note.

tb_masked_and_gadget.v's name suggests it is the functional-correctness
testbench for masked_and_gadget.v. As written, it is not: it contains
two stimulus loops (fixed-secret and random-secret populations, 5000
cycles each) with no checker -- no comparison of q_sh0 ^ q_sh1 against
the expected a & b, no $display of pass/fail, no assertion. It only
drives the DUT and calls $finish.

This means: prior to this security investigation, functional correctness
of the masked AND gadget had never actually been verified by simulation
in this repository, despite the presence of a file whose name implies
otherwise.

Resolution: security_tests/tb_functional_exhaustive.v (new, added
during this investigation) provides an exhaustive (32/32, 2^5 input
space) self-checking functional test. Result: PASS, 0 errors.

Recommendation for a future edit of the real file (not performed here,
since the task scope for this investigation excludes modifying existing
artifacts): either (a) rename tb_masked_and_gadget.v to something that
reflects its actual purpose (it is closer to a manual/smoke-test
stimulus driver than a correctness check), or (b) add a checker to it
directly so the name and behavior match.
