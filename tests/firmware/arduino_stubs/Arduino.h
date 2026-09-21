#pragma once

#include <stdint.h>

constexpr uint8_t HIGH = 0x1;
constexpr uint8_t LOW = 0x0;
constexpr uint8_t INPUT_PULLUP = 0x2;
constexpr uint8_t INPUT = 0x0;
constexpr uint8_t OUTPUT = 0x1;

class HardwareSerial {
 public:
  void begin(unsigned long) {}
  int available() { return 0; }
  int read() { return -1; }
  void print(const char*) {}
  void print(uint8_t) {}
  void print(uint32_t) {}
  void println(const char*) {}
  void println(uint32_t) {}
  int printf(const char*, ...) { return 0; }
};

extern HardwareSerial Serial;

void pinMode(uint8_t pin, uint8_t mode);
void digitalWrite(uint8_t pin, uint8_t value);
int digitalRead(uint8_t pin);
uint32_t millis();

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
using byte = uint8_t;

class EspClass {
 public:
  uint64_t getEfuseMac() const { return 0; }
};
extern EspClass ESP;
