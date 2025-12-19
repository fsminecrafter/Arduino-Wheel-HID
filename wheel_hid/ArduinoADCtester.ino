#include <Wire.h>

#define ADS1115_ADDR 0x48
#define REG_CONVERSION 0x00
#define REG_CONFIG     0x01

#define SERIAL_BAUD 115200
#define CONV_DELAY_MS 8

int16_t observedMin = 32767;
int16_t observedMax = -32768;
float smoothing = 0.2;      // smoothing factor
float smoothedValue = 0.0;  // smoothed scaled value

bool writeConfig(uint16_t config) {
  Wire.beginTransmission(ADS1115_ADDR);
  Wire.write(REG_CONFIG);
  Wire.write(config >> 8);
  Wire.write(config & 0xFF);
  uint8_t err = Wire.endTransmission();

  if (err != 0) {
    Serial.print("I2C ERROR writing config: ");
    Serial.println(err);
    return false;
  }
  return true;
}

bool readConversion(int16_t &out) {
  Wire.beginTransmission((uint8_t)ADS1115_ADDR);
  Wire.write(REG_CONVERSION);
  uint8_t err = Wire.endTransmission();

  if (err != 0) {
    Serial.print("I2C ERROR selecting conversion register: ");
    Serial.println(err);
    return false;
  }

  uint8_t count = Wire.requestFrom((uint8_t)ADS1115_ADDR, (uint8_t)2);
  if (count != 2) {
    Serial.print("I2C ERROR: expected 2 bytes, got ");
    Serial.println(count);
    return false;
  }

  uint8_t msb = Wire.read();
  uint8_t lsb = Wire.read();
  out = (int16_t)((msb << 8) | lsb);
  return true;
}

bool readADS1115(int16_t &value) {
  uint16_t config =
      0x8000 | // Start conversion
      0x4000 | // AIN0 vs GND
      0x0200 | // ±2.048V
      0x0100 | // Single-shot
      0x0080 | // 128 SPS
      0x0003;  // Comparator disabled

  if (!writeConfig(config)) return false;
  delay(CONV_DELAY_MS);
  return readConversion(value);
}

// Map value to full range -32767..32767
int16_t mapToFullRange(int16_t raw) {
  if (raw < observedMin) observedMin = raw;
  if (raw > observedMax) observedMax = raw;

  if (observedMax == observedMin) return 0;

  int32_t mapped = (int32_t)(raw - observedMin) * 65534L / (observedMax - observedMin) - 32767L;
  return (int16_t)mapped;
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(200);
  Serial.println();
  Serial.println("=== ADS1115 SAFE TEST WITH AUTO-SCALE ===");

  Wire.begin();

  Wire.beginTransmission(ADS1115_ADDR);
  uint8_t err = Wire.endTransmission();
  if (err != 0) {
    Serial.print("FATAL: ADS1115 not responding at 0x");
    Serial.println(ADS1115_ADDR, HEX);
    while (1);
  }

  Serial.println("ADS1115 detected on I2C bus.");
}

void loop() {
  int16_t adc;
  if (readADS1115(adc)) {
    int16_t scaled = mapToFullRange(adc);

    // Apply simple smoothing
    smoothedValue = smoothedValue * smoothing + scaled * (1.0 - smoothing);

    // Print only the smoothed value for Serial Plotter
    Serial.println((int)smoothedValue);
  } else {
    Serial.println("READ FAILED");
  }

  delay(1); // 100ms = 10Hz sample rate
}
