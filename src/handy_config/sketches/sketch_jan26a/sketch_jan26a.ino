#include <Arduino.h>

#define SERIAL_BAUD 115200
#define MAX_JOINTS 6   // you are sending 6 joints

double joint_angles[MAX_JOINTS];
uint8_t joint_count = 0;

String rx_buffer = "";

void parseAngles(const String &line)
{
  joint_count = 0;

  int start = 0;

  while (start < line.length() && joint_count < MAX_JOINTS) {
    int comma = line.indexOf(',', start);

    String token;
    if (comma == -1) {
      token = line.substring(start);
      start = line.length();
    } else {
      token = line.substring(start, comma);
      start = comma + 1;
    }

    joint_angles[joint_count] = token.toDouble();  // float64
    joint_count++;
  }

  // Debug output
  Serial.print("Received ");
  Serial.print(joint_count);
  Serial.println(" joint angles:");

  for (uint8_t i = 0; i < joint_count; i++) {
    Serial.print("joint[");
    Serial.print(i);
    Serial.print("] = ");
    Serial.println(joint_angles[i], 4);
  }
}

void setup()
{
  Serial.begin(SERIAL_BAUD);
  delay(1000);
  Serial.println("ESP32 ready. Waiting for joint angles...");
}
          
void loop()
{
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      rx_buffer.trim();
      parseAngles(rx_buffer);
      rx_buffer = "";
    } else {
      rx_buffer += c;
    }
  }
}
