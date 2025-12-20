#include <Wire.h>

/* ---------------- CONFIG ---------------- */

#define ADS1115_ADDR     0x48
#define REG_CONVERSION   0x00
#define REG_CONFIG       0x01

#define SERIAL_BAUD      115200
#define CONV_DELAY_MS    8

#define PAIRING_CODE     "FSMINEWHEEL123"
#define PAIR_INTERVAL_MS 1000
#define STREAM_INTERVAL  10   // ~100 Hz

/* ---------------- STATE ---------------- */

bool paired = false;

int16_t observedMin = 32767;
int16_t observedMax = -32768;

float smoothing = 0.2f;
float smoothedValue = 0.0f;

unsigned long lastPairSend = 0;
unsigned long lastStream = 0;

/* Serial RX buffer (UNO-safe) */
char rxBuf[64];
uint8_t rxPos = 0;

/* ---------------- I2C / ADC ---------------- */

bool writeConfig(uint16_t config) {
  Wire.beginTransmission(ADS1115_ADDR);
  Wire.write(REG_CONFIG);
  Wire.write(config >> 8);
  Wire.write(config & 0xFF);
  return Wire.endTransmission() == 0;
}

bool readConversion(int16_t &out) {
  Wire.beginTransmission(ADS1115_ADDR);
  Wire.write(REG_CONVERSION);
  if (Wire.endTransmission() != 0) return false;

  if (Wire.requestFrom(ADS1115_ADDR, (uint8_t)2) != 2) return false;

  out = (int16_t)((Wire.read() << 8) | Wire.read());
  return true;
}

bool readADS1115(int16_t &value) {
  uint16_t config =
    0x8000 | // Start conversion
    0x4000 | // AIN0 vs GND
    0x0200 | // ±2.048V
    0x0100 | // Single-shot
    0x0080 | // 128 SPS
    0x0003;  // Comparator off

  if (!writeConfig(config)) return false;
  delay(CONV_DELAY_MS);
  return readConversion(value);
}

/* ---------------- MAPPING ---------------- */

int16_t mapToFullRange(int16_t raw) {
  if (raw < observedMin) observedMin = raw;
  if (raw > observedMax) observedMax = raw;

  if (observedMax == observedMin) return 0;

  return (int32_t)(raw - observedMin) * 65534L /
         (observedMax - observedMin) - 32767L;
}

/* ---------------- SERIAL HANDLING ---------------- */

void handleSerial() {
  while (Serial.available()) {
    char c = Serial.read();
      
    if (c == '\n' || c == '\r') {
      rxBuf[rxPos] = 0;

      if (strcmp(rxBuf, "PAIRING_OK") == 0) {
        paired = true;
        Serial.println("PAIRING_CONFIRMED");
      }
      else if (strcmp(rxBuf, "RESET_PAIRING") == 0) {
        paired = false;
        Serial.println("PAIRING_RESET");
      }

      rxPos = 0;
    }
    else if (rxPos < sizeof(rxBuf) - 1) {
      rxBuf[rxPos++] = c;
    }
  }
}

/* ---------------- SETUP ---------------- */

void setup() {
  Serial.begin(SERIAL_BAUD);
  Wire.begin();

  delay(300); // USB settle (UNO safe)

  Serial.println("BOOT_OK");
}

/* ---------------- LOOP ---------------- */

void loop() {
  handleSerial();

  /* Send pairing request periodically until paired */
  if (!paired && millis() - lastPairSend > PAIR_INTERVAL_MS) {
    Serial.print("PAIRING_REQUEST:");
    Serial.println(PAIRING_CODE);
    lastPairSend = millis();
  }

  if (!paired) return;

  /* Stream ADC */
  if (millis() - lastStream >= STREAM_INTERVAL) {
    lastStream = millis();

    int16_t raw;
    if (!readADS1115(raw)) {
      Serial.println("ERROR:ADC_READ_FAILED");
      return;
    }

    int16_t scaled = mapToFullRange(raw);
    smoothedValue = smoothedValue * smoothing +
                    scaled * (1.0f - smoothing);

    Serial.println((int)smoothedValue);
  }
}
