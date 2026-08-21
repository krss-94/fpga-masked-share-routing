link_design -part xc7a100tcsg324-1
set all_slices [get_sites -filter {SITE_TYPE =~ SLICE*}]
puts "Total slices: [llength $all_slices]"

set xs {}
set ys {}
foreach s $all_slices {
    set nm [get_property NAME $s]
    if {[regexp {SLICE_X([0-9]+)Y([0-9]+)} $nm -> xval yval]} {
        lappend xs $xval
        lappend ys $yval
    }
}

set xs [lsort -integer -unique $xs]
set ys [lsort -integer -unique $ys]

puts "SLICE_X min: [lindex $xs 0]  max: [lindex $xs end]"
puts "SLICE_Y min: [lindex $ys 0]  max: [lindex $ys end]"