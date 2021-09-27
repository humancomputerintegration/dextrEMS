# Communicating with the wireless exoskeleton

The exoskeleton communicates only using BLE. We have implemented two scripts that allow to parse the commands via WiFi using Open Sound Control (OSC) protocol and translate it to BLE for the exoskeleton. 

- `osc_server.py` allows to connect a computer with the exoskeleton via BLE. It retrieves the commands from the `osc_client.py` and sends it to the exoskeleton.
- `osc_client.py` is used to send commands to the exoskeleton.

# Technical evaluation code

The two technical evaluation's source code described in the paper are using a wired version of dextrEMS using an Arduino Mega to control the motors.

- `dextrems-independence` evaluates the independence of each joints for dextrEMS VS EMS only

- `dextrems-pose-precision` evaluates the pose precision for dextrEMS VS EMS only

# nRF Firmware

- `nrf-firmware` contains the source code for dextrEMS' firmware

