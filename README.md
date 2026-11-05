# FlexVoice 2.3 — FLEX + POT + MPU6050

Hardware: ESP32 GPIO32 = flex sensor divider midpoint, GPIO34 = potentiometer middle/wiper, 3.3V and GND = potentiometer outer terminals, MPU6050 SDA GPIO21, SCL GPIO22. Never connect the pot middle pin to GND while outer pin is at 3.3V. Unplug USB when rewiring. Pot must stay on 3.3V, **never 5V** to GPIO34.

## First run
1. Upload `FlexVoice_2_3_ESP32.ino` in Arduino IDE, board ESP32 Dev Module, 115200 baud.
2. Open Serial Monitor. Expected: `208,820,-0.74,-0.07,0.66,1.44,2.07,0.82,OK`. Turn potentiometer to see the SECOND number change; bend flex to see FIRST number change. Close Serial Monitor before Python.
3. In this extracted directory, run:

```cmd
py -m pip install -r requirements.txt
py collect_v23.py --port COM7 --audit
py collect_v23.py --port COM7
py train_v23.py
py live_v23.py --port COM7 --name "Your Name" --debug
```

This is a NEW dataset `phrase_data_v23.csv`. Old v2.2 data are intentionally not mixed because the sensor arrangement changed. Each of 11 classes (10 phrases + REST) needs **4 independent trials x 25 samples** (1,100 readings total). Stop and resume safely with Ctrl+C; completed trials remain saved. To redo one class, use `py collect_v23.py --port COM7 --redo INTRO` (backs up current CSV first).

## Physical gesture states
- REST: FLEX straight (~190–210), POT at minimum (~820), wrist neutral.
- FLEX gestures: FLEX bent (>=245), POT minimum (<=1400); five different wrist orientations.
- POT gestures: FLEX straight (<=235), POT high (>=2400); five wrist orientations.
- Five positions: LEFT, UP, DOWN, RIGHT, CENTER. Hold MPU6050 mounted consistently. Rotate knob to high **before** posing wrist for POT gestures. Return to REST (flex straight + pot low) before each new phrase.

**Important:** `POT high` is an intentional knob selection, not a second finger flex sensor. This is a proof-of-concept / assisted communication demonstrator, not a clinically validated wearable. The flex signal has a relatively narrow range (~190–250+); if it is unstable, improve the divider/sensor contact before training. The current thresholds (REST <=235, BENT >=245, POT high >=2400) are **starting values**, not proven optimal. Avoid ambiguous poses; LEFT/RIGHT/UP/DOWN should differ in MPU gravity-vector readings. Training prints held-out-trial accuracy; it is not a guarantee of live reliability.

## Troubleshooting
- `Only 0/25`: check 9-field CSV with OK, correct port and 115200 baud; close Serial Monitor.
- `CHECK_ADC`: investigate saturated ADC and pot wiring. At full high the firmware flags 4095; turn knob slightly back until the output ends in `OK` and POT remains >=2400.
- `Wrong control state`: make sure POT low for REST/FLEX gestures and high for POT gestures. For FLEX, bend until >=245. Keep wrist steady during the 25-sample capture.
- If one pose sounds like another, collect four cleaner trials with distinct orientations, and train again.
- For high-stakes use, add independent usability testing, fail-safe output suppression, and improved sensor hardware.