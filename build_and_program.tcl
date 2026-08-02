# Open the Vivado project
open_project {c:/Users/skali/ricscv/ricscv.xpr}

# Reset both runs to ensure clean build
set_property AUTO_INCREMENTAL_CHECKPOINT 0 [get_runs synth_1]
reset_run synth_1
reset_run impl_1

# Launch Synthesis, Implementation, and Bitstream Generation
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1

# Check if implementation succeeded
if {[get_property PROGRESS [get_runs impl_1]] != "100%"} {
    puts "ERROR: Implementation failed!"
    exit 1
}

puts "SUCCESS: Bitstream generated successfully. Programming FPGA..."

# Program the FPGA
open_hw_manager
connect_hw_server -url localhost:3121
open_hw_target

# Select device
set device [lindex [get_hw_devices] 0]
current_hw_device $device

# Set programming bitstream
set_property PROGRAM.FILE {c:/Users/skali/ricscv/ricscv.runs/impl_1/fpga_top.bit} $device

# Program and refresh
program_hw_devices $device
refresh_hw_device $device

close_hw_target
disconnect_hw_server
close_hw_manager

puts "FPGA programmed successfully!"
exit
