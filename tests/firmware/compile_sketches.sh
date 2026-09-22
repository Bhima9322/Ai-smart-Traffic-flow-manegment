#!/usr/bin/env bash
# Syntax-only host check for Arduino sketches. This checks C++ structure but
# does not replace compiling/uploading with the Espressif Arduino core.
set -euo pipefail

readonly STUB_HEADER="tests/firmware/arduino_stubs/Arduino.h"
readonly COMMON_FLAGS=(
  -std=c++17
  -Wall
  -Wextra
  -Werror
  -fsyntax-only
  -x c++
  -I tests/firmware/arduino_stubs
  -include "$STUB_HEADER"
)

g++ "${COMMON_FLAGS[@]}" firmware/esp32_signal_a/esp32_signal_a.ino
g++ "${COMMON_FLAGS[@]}" firmware/esp32_signal_b/esp32_signal_b.ino
printf 'ESP32 sketch syntax checks passed\n'
