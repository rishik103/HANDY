#include <Arduino.h>
#define SERIAL_BAUD 115200
#define MAX_JOINTS 6

double joint_angles[MAX_JOINTS];
double velocities[MAX_JOINTS];
uint8_t joint_count = 0;
String rx_buffer = "";

void parseTokens(const String &segment, double *arr, uint8_t &count) {
  count = 0;
  int start = 0;
  while (start < (int)segment.length() && count < MAX_JOINTS) {
    int comma = segment.indexOf(',', start);
    String token;
    if (comma == -1) {
      token = segment.substring(start);
      start = segment.length();
    } else {
      token = segment.substring(start, comma);
      start = comma + 1;
    }
    arr[count++] = token.toDouble();
  }
}

void parseLine(const String &line) {
  int sep = line.indexOf('|');
  if (sep == -1) {
    Serial.println("Error: no '|' separator found.");
    return;
  }

  String pos_seg = line.substring(0, sep);
  String vel_seg = line.substring(sep + 1);

  uint8_t pos_count = 0, vel_count = 0;
  parseTokens(pos_seg, joint_angles, pos_count);
  parseTokens(vel_seg, velocities,   vel_count);
  joint_count = pos_count;

  Serial.print("Received ");
  Serial.print(joint_count);
  Serial.println(" joints:");
  for (uint8_t i = 0; i < joint_count; i++) {
    Serial.print("  joint["); Serial.print(i); Serial.print("] angle=");
    Serial.print(joint_angles[i], 4);
    Serial.print(" deg  vel=");
    Serial.print(velocities[i], 4);
    Serial.println(" deg/s");
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(1000);
  Serial.println("ESP32 ready. Waiting for joint data...");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      rx_buffer.trim();
      if (rx_buffer.length() > 0) {
        parseLine(rx_buffer);
      }
      rx_buffer = "";
    } else {
      rx_buffer += c;
    }
  }
}