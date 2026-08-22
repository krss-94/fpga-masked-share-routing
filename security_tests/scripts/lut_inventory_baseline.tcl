open_checkpoint ../test3_place_route_out/post_route.dcp
set fh [open "./lut_inventory_baseline.rpt" w]
puts $fh "cell,ref_name,site,bel"
foreach c [get_cells -hierarchical -filter {REF_NAME == LUT1 || REF_NAME == LUT2 || REF_NAME == LUT3 || REF_NAME == LUT4 || REF_NAME == LUT5 || REF_NAME == LUT6}] {
    puts $fh "${c},[get_property REF_NAME $c],[get_property SITE $c],[get_property BEL $c]"
}
close $fh
puts "Baseline LUT count: [llength [get_cells -hierarchical -filter {REF_NAME =~ LUT*}]]"
