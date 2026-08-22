proc quote_join {lst} {
    set parts {}
    foreach item $lst {
        lappend parts "\"$item\""
    }
    return [join $parts ", "]
}

proc classify_side {cellname sh0_patterns sh1_patterns} {
    foreach p $sh0_patterns {
        if {[string match $p $cellname]} { return "sh0" }
    }
    foreach p $sh1_patterns {
        if {[string match $p $cellname]} { return "sh1" }
    }
    return "unclassified"
}

if {[llength $argv] < 1} {
    puts "ERROR: usage: detect_classify.tcl <config_file_path>"
    exit 1
}

set config_path [lindex $argv 0]
if {![file exists $config_path]} {
    puts "ERROR: config file not found: $config_path"
    exit 1
}

array set cfg {}
set cf [open $config_path r]
while {[gets $cf line] >= 0} {
    set line [string trim $line]
    if {$line == "" || [string index $line 0] == "#"} { continue }
    set eq_pos [string first "=" $line]
    if {$eq_pos < 0} { continue }
    set key [string range $line 0 [expr {$eq_pos - 1}]]
    set val [string range $line [expr {$eq_pos + 1}] end]
    set cfg($key) $val
}
close $cf

foreach req {DCP SH0 SH1 WATCH OUT} {
    if {![info exists cfg($req)]} {
        puts "ERROR: config file missing required key: $req"
        exit 1
    }
}

set dcp             $cfg(DCP)
set sh0_patterns    [split $cfg(SH0) "|"]
set sh1_patterns    [split $cfg(SH1) "|"]
set watch_patterns  [split $cfg(WATCH) "|"]
set out_json        $cfg(OUT)

puts "=== Config loaded ==="
puts "DCP: $dcp"
puts "SH0 patterns ([llength $sh0_patterns]): $sh0_patterns"
puts "SH1 patterns ([llength $sh1_patterns]): $sh1_patterns"
puts "WATCH patterns ([llength $watch_patterns]): $watch_patterns"
puts "OUT: $out_json"
puts "======================"

open_checkpoint $dcp

set watched_cells {}
foreach pat $watch_patterns {
    set cells [get_cells -quiet -hierarchical -filter "NAME =~ ${pat}"]
    foreach c $cells {
        if {[lsearch -exact $watched_cells $c] < 0} {
            lappend watched_cells $c
        }
    }
}

array set site_of {}
array set side_of {}
array set bel_of {}
foreach c $watched_cells {
    set site_of($c) [get_property -quiet SITE $c]
    set bel_of($c)  [get_property -quiet BEL $c]
    set side_of($c) [classify_side $c $sh0_patterns $sh1_patterns]
}

array set site_sides {}
foreach c $watched_cells {
    set site $site_of($c)
    if {$site == ""} { continue }
    if {![info exists site_sides($site)]} { set site_sides($site) {} }
    lappend site_sides($site) $c
}

set fh [open $out_json w]
puts $fh "\{"
puts $fh "  \"checkpoint\": \"$dcp\","
puts $fh "  \"sh0_patterns\": \[[quote_join $sh0_patterns]\],"
puts $fh "  \"sh1_patterns\": \[[quote_join $sh1_patterns]\],"
puts $fh "  \"watch_patterns\": \[[quote_join $watch_patterns]\],"

puts $fh "  \"cells\": \["
set n [llength $watched_cells]
set i 0
foreach c $watched_cells {
    incr i
    set comma [expr {$i < $n ? "," : ""}]
    puts $fh "    \{\"name\": \"$c\", \"site\": \"$site_of($c)\", \"bel\": \"$bel_of($c)\", \"side\": \"$side_of($c)\"\}$comma"
}
puts $fh "  \],"

puts $fh "  \"sites\": \["
set site_names [array names site_sides]
set ns [llength $site_names]
set si 0
set mixed_count 0
set unclassified_present_count 0
set unclassified_only_count 0
foreach site $site_names {
    incr si
    set members $site_sides($site)
    set has_sh0 0
    set has_sh1 0
    set has_unclassified 0
    foreach m $members {
        set s $side_of($m)
        if {$s == "sh0"} { set has_sh0 1 }
        if {$s == "sh1"} { set has_sh1 1 }
        if {$s == "unclassified"} { set has_unclassified 1 }
    }
    if {$has_sh0 && $has_sh1} {
        set classification "MIXED_SITE_CONFLICT"
        incr mixed_count
    } elseif {$has_unclassified && ($has_sh0 || $has_sh1)} {
        set classification "UNCLASSIFIED_CELL_PRESENT"
        incr unclassified_present_count
    } elseif {$has_unclassified} {
        set classification "UNCLASSIFIED_ONLY"
        incr unclassified_only_count
    } elseif {[llength $members] > 1} {
        set classification "OK_SAME_SIDE"
    } else {
        set classification "OK_SINGLE_CELL"
    }
    set comma [expr {$si < $ns ? "," : ""}]
    puts $fh "    \{\"site\": \"$site\", \"members\": \[[quote_join $members]\], \"classification\": \"$classification\"\}$comma"
}
puts $fh "  \],"

set unclassified_cells {}
foreach c $watched_cells {
    if {$side_of($c) == "unclassified"} { lappend unclassified_cells $c }
}

puts $fh "  \"summary\": \{"
puts $fh "    \"total_watched_cells\": $n,"
puts $fh "    \"mixed_site_conflicts\": $mixed_count,"
puts $fh "    \"sites_with_unclassified_cell_present\": $unclassified_present_count,"
puts $fh "    \"sites_unclassified_only\": $unclassified_only_count,"
puts $fh "    \"unclassified_cell_count\": [llength $unclassified_cells],"
puts $fh "    \"unclassified_cells\": \[[quote_join $unclassified_cells]\]"
puts $fh "  \}"
puts $fh "\}"
close $fh

puts "=== Classification complete ==="
puts "Watched cells: $n"
puts "MIXED_SITE_CONFLICT sites: $mixed_count"
puts "UNCLASSIFIED_CELL_PRESENT sites: $unclassified_present_count"
puts "UNCLASSIFIED_ONLY sites: $unclassified_only_count"
puts "Unclassified cells total: [llength $unclassified_cells]"
puts "Output written to: $out_json"
