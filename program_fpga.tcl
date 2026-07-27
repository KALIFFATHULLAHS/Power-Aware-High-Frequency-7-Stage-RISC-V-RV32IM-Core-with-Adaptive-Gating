open_hw_manager
connect_hw_server -url localhost:3121
open_hw_target

# Select the Artix-7 device
set device [lindex [get_hw_devices] 0]
current_hw_device $device

# Set the bitstream file
set_property PROGRAM.FILE {c:/Users/skali/ricscv/ricscv.runs/impl_1/fpga_top.bit} $device

# Program the device
program_hw_devices $device
refresh_hw_device $device

close_hw_target
disconnect_hw_server
close_hw_manager
exit
