import math
import time

import cv2
import mediapipe as mp
import serial

# ================= SETTINGS =================
PORT = "/dev/cu.wchusbserial130"   # Change to your ESP32 port (Windows: "COM3")
BAUD = 115200
CAMERA_INDEX = 0

SMOOTHING = 0.3        # 0-1, lower = smoother but slower
SEND_INTERVAL = 0.05   # Seconds between serial messages (20 per second)

# Mode 1: hand tilt (rotate your hand left/right like a steering wheel)
# Mode 2: pinch distance (thumb and index finger apart = larger angle)
mode = 1

# ================= SERIAL =================
try:
    esp = serial.Serial(PORT, BAUD, timeout=0.1)
    time.sleep(2)   # ESP32 resets when the port opens
    print("Connected to", PORT)
except serial.SerialException as e:
    esp = None
    print("Could not open serial port, preview mode only:", e)

# ================= MEDIAPIPE =================
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6,
)

cap = cv2.VideoCapture(CAMERA_INDEX)


def clamp(value, low, high):
    return max(low, min(high, value))


def tilt_angle(lm):
    """Angle of the wrist -> middle finger base line. Hand upright = 90."""
    wrist, middle = lm[0], lm[9]
    dx = middle.x - wrist.x
    dy = wrist.y - middle.y   # image y points down, so flip it
    deg = math.degrees(math.atan2(dx, dy))   # 0 = pointing up, +right, -left
    return clamp(deg + 90, 0, 180)           # -90..90 -> 0..180


def pinch_angle(lm):
    """Distance between thumb tip and index tip, relative to hand size."""
    hand_size = math.hypot(lm[9].x - lm[0].x, lm[9].y - lm[0].y)
    pinch = math.hypot(lm[4].x - lm[8].x, lm[4].y - lm[8].y)
    ratio = pinch / hand_size if hand_size > 0 else 0
    # ratio about 0.1 (closed) to 1.0 (wide open)
    return clamp((ratio - 0.1) / 0.9 * 180, 0, 180)


smooth_angle = 90.0
last_sent = 0.0
last_value = -1

while True:
    ok, frame = cap.read()
    if not ok:
        print("Camera not available")
        break

    frame = cv2.flip(frame, 1)   # mirror view so left/right feels natural
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        hand = result.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

        lm = hand.landmark
        raw = tilt_angle(lm) if mode == 1 else pinch_angle(lm)
        smooth_angle += (raw - smooth_angle) * SMOOTHING
        angle = int(round(smooth_angle))

        # Send only when the value changed enough
        now = time.time()
        if now - last_sent >= SEND_INTERVAL and abs(angle - last_value) >= 2:
            if esp:
                esp.write(f"{angle}\n".encode())
            last_sent = now
            last_value = angle

        cv2.putText(frame, f"Servo angle: {angle}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    mode_name = "Tilt" if mode == 1 else "Pinch"
    cv2.putText(frame, f"Mode: {mode_name}  (m = switch, q = quit)", (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    cv2.imshow("Hand servo", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key == ord("m"):
        mode = 2 if mode == 1 else 1

cap.release()
cv2.destroyAllWindows()
if esp:
    esp.close()
