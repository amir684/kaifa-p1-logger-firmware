# P1 Logger

**A long-term logger for Israeli IEC smart meters (Kaifa), on an ESP32-S3.**

It reads the meter's P1 port every second and keeps everything on a microSD card for years. It shows live values on an ST7567 LCD and reports to Home Assistant over outgoing MQTT, so it also works from a remote site with no open ports.

![version](https://img.shields.io/badge/firmware-0.1.4-blue)
![platform](https://img.shields.io/badge/ESP32--S3-N16R8%20%7C%20N16R2%20%7C%20Super%20Mini-red)
![meters](https://img.shields.io/badge/meters-MA110M%20%7C%20MA309M-orange)

[עברית](README.md) · **[⚡ Install from the browser](https://amir684.github.io/kaifa-p1-logger-firmware/)** · [Downloads](../../releases) · The detailed docs in [docs/](docs/) are in Hebrew.

## Features

| Feature | Details |
|---|---|
| **P1** | Auto-detects baud rate, inversion and meter type. CRC-checks every telegram. Knows the Israeli tariff codes (`1.8.11`–`1.8.13`, `96.14.1`). Unknown codes are still logged and published. |
| **Load profile** | Decodes `1-0:99.1.0`, the meter's official 15-minute energy. |
| **Logging** | Per-minute avg/min/max kept forever, per-second rows for 60 days, an event log, and raw telegram capture on request. |
| **Survives card faults** | Minutes and events go to the controller's internal flash first and are copied to the card once a day. A hung card gets its power cycled automatically. |
| **Costs** | Today, yesterday, this month and a month-end forecast. Each tariff register is priced separately; VAT, discount, fixed fee and export price are supported. |
| **Charts** | A full day: power, phases, voltage, current and hourly energy, with min/max bands, zoom and a daily summary. |
| **Home Assistant** | MQTT Discovery creates entities, alert binary sensors and buttons from the fields the meter actually sends. |
| **UI** | A bilingual (Hebrew/English) web UI with every setting, a live telegram view, file browser, OTA and backup/restore. The LCD has 8 pages and a full menu driven by the BOOT button alone. |
| **Status LED** | The on-board WS2812: a green blink per telegram, red patterns for faults, blue for setup mode. |
| **WireGuard** | Connects a remote site to Home Assistant at home. |
| **UPS** | Detects power loss, flushes to the card cleanly, and deep-sleeps when the battery is low. |

## Verified Israeli P1 facts

From real MA110M and MA309M meters (hundreds of consecutive telegrams, all CRCs valid):

- **Protocol:** DSMR 5.0, header `/KFM5KAIFA-METER`, 115200 8N1 **inverted**.
- **Timing:** one telegram every second.
- **CRC16:** polynomial 0xA001 (reflected), init 0, computed over `/` .. `!` including the CRLFs.
- **Israeli-specific codes:** tariffs are `1.8.11/12/13` and `2.8.11/12/13`, not `1.8.1/2`. The active tariff is `96.14.1`. The meter ID is plain ASCII, not hex, and is not unique.
- **Real resolution:** power 10 W, voltage 1 V, current 0.1 A, energy 1 Wh.

More detail is in [docs/p1-israel.md](docs/p1-israel.md).

## Install

| Board | Image |
|---|---|
| ESP32-S3-DevKitC-1 **N16R8** | `p1logger-<version>-full.bin` |
| ESP32-S3 **N16R2** | `p1logger-<version>-r2-full.bin` |
| ESP32-S3 **Super Mini** (N4R2) | `p1logger-<version>-mini-full.bin` |

1. **Flash:** open the **[install page](https://amir684.github.io/kaifa-p1-logger-firmware/)** in Chrome or Edge on a computer, plug the board in over USB, pick the board and press Install. Or by hand: `esptool.py --chip esp32s3 write_flash 0x0 p1logger-0.1.4-full.bin`.
2. **Join the setup network:** connect to the `P1-Logger-xxxxxx` Wi-Fi (password `p1logger`). The setup page opens on its own.
3. **Network:** add your Wi-Fi. **System:** set an admin password and an entity prefix such as `home` or `farm`. **MQTT:** enter your broker.

**Updates:** upload the `-ota.bin` from [Releases](../../releases) in the web UI's **System** tab. Settings and data are kept. The install page and the `-full.bin` image erase the whole flash, settings included.

## BOOT button

| Press | Action |
|---|---|
| Short | Next page. In the menu: next item |
| 1–3 s | Open the menu. In the menu: select |
| 3 s | Setup mode |
| 10 s | Factory reset |

## Wiring (DevKit, short)

| Signal | ESP32-S3 |
|---|---|
| P1 Data (RJ12 pin 5) | GPIO39 + 1 kΩ pull-up to 3V3 |
| P1 Request (pin 2) | 1 kΩ to pin 1 (+5 V). **Not** to a GPIO. |
| SD | CLK 12, CMD 13, D0 11, D1 10, D2 9, D3 14 (or SPI: SCK 12, MOSI 13, MISO 11, CS 14) |
| LCD | SCK 5, MOSI 6, CS 7, A0 15, RST 16, backlight 18 |

The Super Mini uses other pins. The full wiring is in [docs/hardware.md](docs/hardware.md).

**Power:** DSMR allows only **250 mA** from the P1 +5 V, and an ESP32-S3 on Wi-Fi peaks higher. Use a current-limited charger with a battery (such as a BQ24074), bulk capacitors at the SD module, and a lower Wi-Fi TX power.

## Docs

| File | Contents |
|---|---|
| [hardware.md](docs/hardware.md) | Parts, wiring, UPS and current budget |
| [p1-israel.md](docs/p1-israel.md) | The P1 protocol on Israeli meters |
| [api.md](docs/api.md) | REST, MQTT and every setting |
| [troubleshooting.md](docs/troubleshooting.md) | Problems seen on the hardware and how to fix them |
| [esp32-pitfalls.md](docs/esp32-pitfalls.md) | ESP32-S3 traps found along the way |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## Source code

The firmware is distributed as prebuilt images only; the source is not open. Questions, bugs and new meters: [Issues](../../issues).

## Credits

Builds on the knowledge in [klimofey/iec-p1-esphome](https://github.com/klimofey/iec-p1-esphome) and [mp3llll/iec-p1-esphome-3phase](https://github.com/mp3llll/iec-p1-esphome-3phase). Third-party licenses: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

© 2026 amir684. You may download the firmware and use it on your own devices for personal use. Redistribution, sale or bundling with a product requires written permission. See [LICENSE](LICENSE).
