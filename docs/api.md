# API, ‏MQTT והגדרות

## REST

**אבטחה:** כל הנתיבים מוגנים ב-HTTP Basic, עם משתמש `admin` וסיסמת המנהל. כל עוד לא הוגדרה סיסמה, הגישה פתוחה, והממשק מציג אזהרה.

### קריאה

| נתיב | תוכן |
|---|---|
| `GET /api/status` | מצב כללי: גרסה, uptime, זיכרון, WiFi (כולל `tx_power`), ‏VPN, מונה, P1 (מברקים, שגיאות CRC), SD (כולל `lost_lines`, `mounts`, `mount_failures`, `power_cycles`, `last_error`, `op`, `op_result`, `test`), שעון, חשמל, התראות |
| `GET /api/live` | הערכים האחרונים מהמונה |
| `GET /api/fields` | רשימת השדות: מפתח, קוד OBIS, שם, יחידה, סוג |
| `GET /api/history` | הספק בקפיצות של 5 שניות, מהזיכרון, לגרף בממשק: `{"step":5,"end":<epoch>,"p":[...]}` |
| `GET /api/raw` | המברק הגולמי האחרון |
| `GET /api/events` | האירועים האחרונים |
| `GET /api/log` | יומן המערכת האחרון (כמו בפלט הסריאלי) |
| `GET /api/scan` | סריקת רשתות WiFi |
| `GET /api/files?dir=/sec` | תוכן תיקייה בכרטיס. עם `&src=flash`: קבצים בזיכרון הפנימי שממתינים לכרטיס (רק `/spool`) |
| `GET /api/sd/info` | פרטי הכרטיס: סוג, מערכת קבצים, גודל אשכול, תפוסה לפי תיקייה (`folders`), גידול ממוצע ליום (`sec_day`, `min_day`) |
| `GET /api/download?path=/sec/2026-11-04.csv` | הורדת קובץ (גם `&src=flash`) |
| `GET /api/day?d=2026-11-04` | יום שלם של סיכומי דקה, מאוחד מהכרטיס ומהזיכרון הפנימי, כולל קבצי `_2`, `_3`, עם כותרת אחת. מזה הגרפים נטענים |
| `GET /api/config` | ההגדרות. הסיסמאות מוסתרות |
| `GET /api/backup` | גיבוי מלא של ההגדרות, כולל הסיסמאות |

### פעולות

| נתיב | |
|---|---|
| `POST /api/config` | JSON חלקי, למשל `{"wifi":{"tx_power":44}}`. רק השדות שנשלחו משתנים |
| `POST /api/restore` | שחזור מקובץ גיבוי |
| `POST /api/delete?path=...` | מחיקת קובץ בכרטיס |
| `POST /api/ota` | עדכון קושחה, `multipart` עם שדה `file` |
| `POST /api/cmd?do=...` | פקודה, ראו הטבלה הבאה |

| `do=` | |
|---|---|
| `reboot` | אתחול מסודר: כתיבה לכרטיס ואז אתחול |
| `flush` | כתיבה מיידית של כל מה שבזיכרון לכרטיס |
| `sync` | העתקה מיידית של הזיכרון הפנימי לכרטיס (`log.flash`) |
| `eject` / `mount` | ניתוק / חיבור הכרטיס |
| `capture&min=10` | הקלטת מברקים גולמיים ל-`/raw/` |
| `setup_ap` | פתיחת רשת ההגדרה |
| `rediscover` | שליחה מחדש של Discovery ל-HA |
| `factory` | איפוס להגדרות יצרן |
| `sd_test` | בדיקת כרטיס: כתיבה של 1MB, קריאה ובדיקה. התוצאה ב-`sd.op_result` וב-`sd.test` |
| `sd_format&confirm=FORMAT` | פרמוט ל-FAT32 עם אשכול של 32KB. **מוחק את כל הקבצים.** נתונים שעוד בזיכרון נכתבים אחר כך. בלי `confirm=FORMAT` הבקשה נדחית |

### דוגמאות

```bash
curl http://<ip>/api/status
curl -X POST "http://<ip>/api/cmd?do=flush"
curl -F "file=@p1logger-<version>-ota.bin" http://<ip>/api/ota
curl -o today.csv "http://<ip>/api/download?path=/sec/2026-11-04.csv"
```

עם סיסמה מוסיפים `-u admin:<סיסמה>`.

## MQTT

**Base topic:** ‏`p1logger/<id>`, או הערך של `mqtt.base`. ה-`<id>` הוא 6 התווים האחרונים של כתובת ה-MAC.

| Topic | כיוון | תוכן |
|---|---|---|
| `<base>/status` | יוצא | `online` / `offline`, retained ו-LWT |
| `<base>/state` | יוצא | JSON עם כל הערכים, כל `mqtt.interval` שניות (ברירת מחדל 10) |
| `<base>/live` | יוצא | `p_in` ו-`p_out`, כל `mqtt.live_interval` שניות (ברירת מחדל 2, ‏0 = כבוי) |
| `<base>/event` | יוצא | JSON לכל אירוע |
| `<base>/cmd` | נכנס | `reboot`, `flush`, `discovery`, `capture:<דקות>` |

**Home Assistant Discovery:**
- **ישויות** נוצרות תחת `<discovery_prefix>/<component>/p1l_<id>/<key>/config`, רק לשדות שהמונה שולח בפועל.
- **שמות הישויות:** ‏`sensor.<entity_prefix>_<key>`, למשל `sensor.home_p_in`.
- **מה מתפרסם:** שדות המונה, עלויות, התראות (`binary_sensor`) וכפתורים (`button`).

## הגדרות

כל ההגדרות נשמרות ב-`/config.json` ב-LittleFS. השם המלא של כל הגדרה הוא `<חלק>.<מפתח>`, כמו ב-JSON.

| חלק | מפתח | ברירת מחדל | |
|---|---|---|---|
| general | `name` | | שם המכשיר |
| | `lang` | `he` | `he` / `en` |
| | `admin_pass` | ריק | סיסמת הממשק |
| | `entity_prefix` | `p1logger` | קידומת לישויות HA (`home`, `farm`) |
| wifi | `ssid1..3`, `pass1..3` | | עד 3 רשתות, לפי הסדר |
| | `hostname` | `p1logger-<id>` | גם `<hostname>.local` |
| | `static_ip`, `ip`, `gateway`, `mask`, `dns` | DHCP | |
| | `ap_pass` | `p1logger` | סיסמת רשת ההגדרה |
| | `tx_power` | `78` | עוצמת שידור ביחידות של 0.25dBm: ‏78 = ‏19.5dBm, ‏44 = ‏11dBm |
| meter | `profile` | `auto` | `auto` / `kaifa_1ph` / `kaifa_3ph` / `generic` |
| | `serial_mode` | `-1` | ‏-1 = זיהוי אוטומטי |
| | `publish_unknown` | `true` | לפרסם גם קודים לא מוכרים |
| | `sim` | `0` | סימולטור: 1 חד-פאזי, 2 תלת-פאזי + סולארי, 3 שידור חוזר של MA110M |
| mqtt | `enabled`, `host`, `port`, `user`, `pass` | `1883` | |
| | `tls`, `insecure`, `ca` | | TLS. ‏`insecure` = בלי בדיקת תעודה |
| | `base`, `discovery`, `discovery_prefix` | `homeassistant` | |
| | `interval`, `live_interval` | `10`, `2` | שניות |
| log | `enabled`, `seconds` | `true` | |
| | `sec_retention_days` | `60` | |
| | `flush_sec` | `60` | כל כמה זמן כותבים לכרטיס |
| | `delete_minutes_when_full` | `false` | |
| | `sd_mode` | `mmc4` | `mmc4` / `mmc1` / `spi`. דורש אתחול |
| time | `ntp1`, `ntp2` | `pool.ntp.org`, `time.google.com` | |
| | `tz` | `IST-2IDT,M3.4.4/26,M10.5.0` | ישראל |
| tariff | `mode` | `flat` | `flat` / `tou` |
| | `flat`, `t1`, `t2`, `t3` | `0.6352` | ₪ לקוט"ש |
| | `include_vat`, `vat_pct` | `true`, `18` | |
| | `discount_pct`, `fixed_monthly`, `export_price` | `0` | |
| alerts | `v_high`, `v_low` | `253`, `207` | V |
| | `power_high_kw` | `0` | ‏0 = כבוי |
| | `no_export` | `false` | התראה על היעדר ייצוא סולארי בצהריים |
| | `no_data_sec` | `60` | |
| display | `model` | `jlx12864` | `jlx12864` / `os12864` / `dg128064` / `dg128064i` / `none`. דורש אתחול |
| | `contrast` | `120` | |
| | `flip` | `true` | סיבוב 180° |
| | `backlight`, `backlight_timeout` | `80`, `60` | ‏%, שניות |
| | `page_rotate` | `0` | שניות. ‏0 = ידני |
| power | `vbus_divider`, `vbat_divider` | `2.0` | ‏0 = אין מדידה |
| | `battery_low_v` | `3.3` | מתחת לזה: שינה עמוקה |
