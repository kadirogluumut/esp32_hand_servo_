# Hand-Controlled Servo (Python + ESP32 + MG90S)



Your webcam tracks your hand, Python calculates the hand angle and sends it over USB serial to an ESP32, and the ESP32 rotates an MG90S servo to match.

```
Camera → Python (MediaPipe) → USB Serial → ESP32 → MG90S Servo
```

## Features
- Real-time hand tracking with MediaPipe
- Two control modes:
  - **Tilt:** Rotate your hand left and right like a steering wheel. The servo moves between 0° and 180°, and sits at 90° when your hand is upright.
  - **Pinch:** The distance between your thumb and index finger sets the angle.
- Smooth motion: angle filtering in Python plus step-by-step movement on the ESP32
- Live angle readout on the camera window

## Files

| File | Description |
|---|---|
| `hand_servo.py` | Runs on your computer. Tracks the hand and sends the angle to the ESP32. |
| `hand_servo_esp32.ino` | Uploaded to the ESP32. Receives the angle and drives the servo. |

## Hardware
- ESP32 Lite V1 (WEMOS LOLIN32 Lite)
- MG90S servo motor
- USB **data** cable (charge-only cables will not work)
- Webcam (a laptop camera is enough)
- 5V supply for the servo (Arduino Uno 5V pin, external adapter, or 4×AA batteries)

## Wiring

| MG90S wire | Connect to |
|---|---|
| Signal (orange/yellow) | ESP32 **GPIO 13** |
| VCC (red) | **5V** supply |
| GND (brown/black) | **GND** (must be shared with the ESP32 GND) |

> Do **not** power the servo from the ESP32 3.3V pin. Under load it cannot supply enough current, so the servo will not move, will buzz, or the board will reset. If you use an external 5V supply, connect its GND to the ESP32 GND.

## Setup

### 1. ESP32
1. In Arduino IDE, select **Tools → Board → WEMOS LOLIN32 Lite**.
2. Install the **ESP32Servo** library from the Library Manager.
3. Upload `hand_servo_esp32.ino`. You should see `Done uploading`.
4. Open the Serial Monitor at 115200 baud with **Newline** line ending. You should see `Hand servo ready`. Send `0`, `90` and `180` to test the servo.
5. **Close the Serial Monitor and Arduino IDE.** Python cannot open the port while it is in use.

### 2. Python
Python **3.9 - 3.12** is required (MediaPipe may fail to install on newer versions).

```bash
pip3 install opencv-python mediapipe pyserial
```

Edit `PORT` at the top of `hand_servo.py` to match your device:

```python
PORT = "/dev/cu.wchusbserial130"   # e.g. "COM3" on Windows
```

On macOS, list available ports with `ls /dev/cu.*`.

## Usage

```bash
cd path/to/project
python3 hand_servo.py
```

The first line in the terminal should read `Connected to ...`. When the camera window opens, show your hand:

| Key | Action |
|---|---|
| `m` | Switch between Tilt and Pinch mode |
| `q` | Quit |

On macOS you will be asked for **camera permission** on first run. If you denied it, enable it under `System Settings → Privacy & Security → Camera` for Terminal (or VS Code).

## Configuration

### `hand_servo.py`
| Setting | Default | Description |
|---|---|---|
| `SMOOTHING` | `0.3` | Angle filter. Higher = faster but jittery, lower = smoother but slower. |
| `SEND_INTERVAL` | `0.05` | Seconds between serial messages. |
| `CAMERA_INDEX` | `0` | Change if you have more than one camera. |

### `hand_servo_esp32.ino`
| Setting | Default | Description |
|---|---|---|
| `SERVO_PIN` | `13` | Servo signal pin. |
| `STEP_DEG` | `3` | Degrees moved per step. Increase for a faster servo. |
| `STEP_MS` | `15` | Time between steps in milliseconds. |

To make it faster, raise `SMOOTHING` to 0.5-0.6 and `STEP_DEG` to 6-8. If something breaks, go back to the defaults. Remember to re-upload the sketch after changing ESP32 values.

## Troubleshooting

| Problem | Fix |
|---|---|
| `camera access has been denied` | Grant camera permission in macOS, then restart Terminal. |
| `Could not open serial port, preview mode only` | Close Arduino IDE and the Serial Monitor, and check `PORT`. |
| Camera works but the servo does not move | Check that the terminal says `Connected to ...`. Test the servo separately by sending `0/90/180` from the Serial Monitor. Check power and the shared GND. |
| Hand not detected | Improve lighting and keep your hand 30-60 cm from the camera. Green landmarks should appear on the hand. |
| Servo buzzes | Limit the range with `constrain(..., 10, 170)`, power the servo from 5V, and add a 100-470 µF capacitor between the red and brown wires. |
| Servo is too slow | Increase `SMOOTHING` and `STEP_DEG`. |
| `Failed to connect to ESP32` while uploading | Close Python and the Serial Monitor, use a data cable, and hold the BOOT button during upload (or connect GPIO 0 to GND). |
| Angle direction is reversed | Change the last line of `tilt_angle` to `return clamp(90 - deg, 0, 180)`. |

## How It Works
- **Tilt mode:** Computes the angle of the line from the wrist (landmark 0) to the middle finger base (landmark 9) relative to vertical, then maps it to 0-180°.
- **Pinch mode:** Measures the distance between the thumb tip (4) and index fingertip (8) relative to hand size, so the result barely changes whether you are close to or far from the camera.
- Python sends the angle as a text line such as `135\n` over serial. The ESP32 reads it and moves the servo toward the target in small steps.

## License
Free to use and modify.
