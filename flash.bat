echo "Press any key to start flashing your device"
pause
esptool.py --chip esp32 --port COM6 erase_flash
esptool.py --chip esp32 --port COM6 --baud 460800 write_flash -z 0x1000 .\esp32-20230221-unstable-v1.19.1-887-gb11026689.bin
echo "Flash completed"
pause