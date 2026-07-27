# open the project
open_project c:/Users/skali/ricscv/ricscv.xpr

# add fpga_top.v to design sources
add_files -norecurse c:/Users/skali/ricscv/ricscv.srcs/sources_1/new/fpga_top.v

# set fpga_top as the top module across fileset and active runs
set_property top fpga_top [current_fileset]
catch { set_property top fpga_top [get_runs synth_1] }
catch { set_property top fpga_top [get_runs impl_1] }
update_compile_order -fileset sources_1

# Run synthesis
puts "=== Running Synthesis ==="
reset_run synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1

# Run implementation and generate bitstream
puts "=== Running Implementation & Generating Bitstream ==="
reset_run impl_1
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1

puts "=== Bitstream Generated Successfully ==="
close_project
exit
