# dextrems user study independency

Capture camera images for trials stimulating 4 fingers (without thumb) x 2 joints (MCP, PIP) with EMS and dextrems exoskeleton.

## software dependency

python 3 with opencv and pyserial

```
pip install opencv-python pyserial
```

## hardware

- dextrems exo wired version (Arduino MEGA)
- rehastim EMS device (8-channel)
- two webcams (should be calibrated first)
    - lowres 720p (should be number 0)
    - fhd 1080p (should be number 1)

## what this program does in steps:

1. check arduino exo
2. calibrate ems
3. read/generate user study order
4. run user study
