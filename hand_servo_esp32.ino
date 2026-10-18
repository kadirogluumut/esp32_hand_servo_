#include <ESP32Servo.h>


#define SERVO_PIN   13    // MG90S signal wire
#define STEP_DEG     8    // Max degrees moved per update (smooths the motion)
#define STEP_MS     15    // Time between steps

Servo servo;
int currentAngle = 90;
int targetAngle = 90;
unsigned long lastStep = 0;

void setup() {
  Serial.begin(115200);

  servo.setPeriodHertz(50);
  servo.attach(SERVO_PIN, 500, 2400);   // MG90S pulse range
  servo.write(currentAngle);

  Serial.println("Hand servo ready");
}

void loop() {
  // Read angle sent from Python, e.g. "135\n"
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() > 0) {
      targetAngle = constrain(line.toInt(), 0, 180);
    }
  }

  // Move toward the target in small steps
  if (millis() - lastStep >= STEP_MS && currentAngle != targetAngle) {
    lastStep = millis();

    if (abs(targetAngle - currentAngle) <= STEP_DEG) {
      currentAngle = targetAngle;
    } else if (targetAngle > currentAngle) {
      currentAngle += STEP_DEG;
    } else {
      currentAngle -= STEP_DEG;
    }
    servo.write(currentAngle);
  }
}
