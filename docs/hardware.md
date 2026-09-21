# Phase 1 hardware: two ESP32 traffic signal controllers

## Scope and safety boundary

This low-voltage firmware adds Phase 3 Wi-Fi/MQTT communication and two local
IR-presence inputs to the Phase 1 signal head: LEDs, a buzzer, a manual
**all-red** button, serial diagnostics, and fixed-time sequencing. It does
**not** implement AI, a website, or a database.
This is a supervised 3.3 V/USB-powered laboratory demonstrator—never connect
it to mains-powered lamps or use it on a public road.

The controlled sequence is:

```text
startup all-red -> A green -> A yellow + buzzer -> all-red ->
B green -> B yellow + buzzer -> all-red -> repeat
```

A green is clamped between the configured 10-second minimum and 60-second
maximum (Phase 1 requests 30 seconds). Yellow is 3 seconds and each clearance
all-red is 1.5 seconds. Holding either board's button produces local all-red;
releasing it restarts that controller with a 2-second all-red phase.

> **Coordination warning:** two standalone ESP32 timers are not a
> safety-certified intersection controller. Their clocks/boot times can differ.
> Upload both sketches and reset both boards together only for a visual bench
demonstration. A future physical fail-safe interlock/synchronization channel
must de-energize green outputs on lost coordination. MQTT is supervisory only,
not a safety interlock.

## Firmware structure

```text
firmware/
├── common/traffic_light_state_machine.h     # shared safety/timing model
├── esp32_signal_a/esp32_signal_a.ino        # ESP32-A local lamps/button/buzzer
└── esp32_signal_b/esp32_signal_b.ino        # ESP32-B local lamps/button/buzzer
```

## Exact wiring (repeat for each board)

Use one ESP32 development board per approach. The GPIO numbers repeat because
the boards are electrically separate.

| Board | GPIO | Connect to | Exact connection |
| --- | ---: | --- | --- |
| ESP32-A | 25 | A red LED | GPIO25 -> 220 Ω resistor -> LED anode; LED cathode -> GND |
| ESP32-A | 26 | A yellow LED | GPIO26 -> 220 Ω resistor -> LED anode; LED cathode -> GND |
| ESP32-A | 27 | A green LED | GPIO27 -> 220 Ω resistor -> LED anode; LED cathode -> GND |
| ESP32-A | 14 | A active buzzer | GPIO14 -> buzzer signal/+; buzzer GND -> ESP32 GND |
| ESP32-A | 13 | A manual button | GPIO13 -> one button terminal; other terminal -> GND |
| ESP32-A | 32 | A sensor 1 | 3.3 V active-LOW digital sensor output -> GPIO32; sensor GND -> ESP32 GND |
| ESP32-A | 33 | A sensor 2 | 3.3 V active-LOW digital sensor output -> GPIO33; sensor GND -> ESP32 GND |
| ESP32-B | 25 | B red LED | GPIO25 -> 220 Ω resistor -> LED anode; LED cathode -> GND |
| ESP32-B | 26 | B yellow LED | GPIO26 -> 220 Ω resistor -> LED anode; LED cathode -> GND |
| ESP32-B | 27 | B green LED | GPIO27 -> 220 Ω resistor -> LED anode; LED cathode -> GND |
| ESP32-B | 14 | B active buzzer | GPIO14 -> buzzer signal/+; buzzer GND -> ESP32 GND |
| ESP32-B | 13 | B manual button | GPIO13 -> one button terminal; other terminal -> GND |
| ESP32-B | 32 | B sensor 1 | 3.3 V active-LOW digital sensor output -> GPIO32; sensor GND -> ESP32 GND |
| ESP32-B | 33 | B sensor 2 | 3.3 V active-LOW digital sensor output -> GPIO33; sensor GND -> ESP32 GND |

GPIO13 uses the firmware's `INPUT_PULLUP`: it reads HIGH when the button is
open and LOW when pressed, so do not add a pull-down resistor. A 40 ms software
debounce is used. The buzzer output is HIGH only during yellow. Use a 3.3 V
**active** buzzer whose current is within the ESP32 GPIO drive limit. For a 5 V
or higher-current buzzer, drive it through a suitable transistor/MOSFET stage
with a common ground; never feed 5 V into GPIO14. A passive buzzer requires a
PWM/tone driver and is not supported by this Phase 1 sketch.

GPIO25, GPIO26, GPIO27, GPIO14, and GPIO13 are used as 3.3 V digital GPIO.
ESP32 GPIOs are not 5 V tolerant. Every LED needs its own 220 Ω series
resistor. Keep the LED current modest and use a transistor driver for larger
lamps or loads. Do not connect a 5 V sensor output directly to GPIO32/GPIO33; use a proper
level shifter, transistor stage, or a sensor with a guaranteed 3.3 V output.

## Upload and bench-test procedure

1. Optionally run `tests/firmware/compile_sketches.sh` from the repository
   root. It checks both sketches' C++ syntax with Arduino API stubs; it does
   not replace an ESP32 core compile or a physical wiring test.
2. Install the ESP32 board package in Arduino IDE.
3. Wire both boards exactly as in the table, then connect each by USB.
4. Upload `firmware/esp32_signal_a/esp32_signal_a.ino` to ESP32-A and
   `firmware/esp32_signal_b/esp32_signal_b.ino` to ESP32-B.
5. Open each serial monitor at **115200 baud**. Phase transitions and button
   actions are printed as diagnostics. Send `F` to latch that controller in
   `FAILSAFE_ALL_RED`; send `R` to reset it into the 2-second startup all-red.
6. Reset both boards together. Verify both red LEDs for 2 seconds, A green for
   30 seconds, A yellow/buzzer for 3 seconds, both red for 1.5 seconds, then B
   green for 30 seconds, B yellow/buzzer for 3 seconds, and both red for 1.5
   seconds before repeating.
7. Hold a manual button: its board must show red only. Release it: that board
   must stay red for 2 seconds before rejoining its local automatic sequence.
8. If any unexpected lamp state occurs, disconnect USB power and correct the
   wiring. Do not continue to subsequent phases until this bench test passes.

The code has no `delay()` calls; timing, button debounce, buzzer control, and
serial reporting remain responsive. Send `F` through the serial monitor to
exercise the latched `FAILSAFE_ALL_RED` state; `R` resets it safely through the
startup all-red interval. Future watchdog/communication fault handlers call
the same failsafe method.
