#!/usr/bin/env python3
"""Check and summarise a raw P1 capture (the /raw/*.txt files the logger writes).

    python tools/p1_check.
    python tools/p1_check.py capture.txt --codes      # also list every OBIS code seen
    python tools/p1_check.py capture.txt --lp         # also print each load-profile change

For every telegram it checks the CRC16 (poly 0xA001, reflected, init 0, over '/' .. '!'
with CRLF line ends), then prints the meter header, the codes, which of them the firmware
does not know yet, and the 15-minute load-profile entries (1-0:99.1.0).

Lines starting with '#' are the logger's own timestamps and are ignored. Captures saved
with LF or CRLF both work, because the CRC is computed over CRLF as the meter sends it.
Standard library only.
"""
import argparse
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path


def crc16(data: bytes) -> int:
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def known_codes(root: Path) -> set:
    """OBIS codes listed in src/obis.cpp, so the report can flag new ones."""
    src = root / "src" / "obis.cpp"
    if not src.exists():
        return set()
    return set(re.findall(r'^\s*\{"(\d+-\d+:[\d.]+)"', src.read_text(encoding="utf-8"), re.M))


def telegrams(text: str):
    """Yields (lines, crc_text) for each '/'...'!XXXX' block."""
    cur = None
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        if line.startswith("#"):
            continue
        if line.startswith("/"):
            cur = [line]
        elif cur is not None:
            if line.startswith("!"):
                yield cur, line[1:5]
                cur = None
            else:
                cur.append(line)


LINE = re.compile(r"^(\d+-\d+:[\d.]+)(\(.*\))$")


def parse_lp(groups):
    """1-0:99.1.0(N)(status code)(code)...(time)(status)(v)... -> newest (time, {code: value})."""
    codes = [g for g in groups[1:] if ":" in g]
    values = len(codes) - 1
    entries = groups[1 + len(codes):]
    width = 2 + values
    if values < 1 or not entries or len(entries) % width:
        return None
    last = entries[-width:]
    return last[0], {codes[1 + k]: last[2 + k] for k in range(values)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("capture", type=Path)
    ap.add_argument("--codes", action="store_true", help="list every code with its first and last value")
    ap.add_argument("--lp", action="store_true", help="print every load-profile entry change")
    args = ap.parse_args()

    known = known_codes(Path(__file__).resolve().parent.parent)
    text = args.capture.read_text(encoding="ascii", errors="replace")

    total = bad = 0
    headers = Counter()
    seen = OrderedDict()  # code -> [first, last, count]
    lp_seen = OrderedDict()
    for lines, crc_text in telegrams(text):
        total += 1
        body = ("\r\n".join(lines) + "\r\n!").encode("ascii", errors="replace")
        try:
            ok = int(crc_text, 16) == crc16(body)
        except ValueError:
            ok = False
        if not ok:
            bad += 1
            continue
        headers[lines[0]] += 1
        for line in lines[1:]:
            m = LINE.match(line)
            if not m:
                continue
            code, rest = m.groups()
            groups = re.findall(r"\(([^)]*)\)", rest)
            value = groups[0] if len(groups) == 1 else rest
            if code in seen:
                seen[code][1] = value
                seen[code][2] += 1
            else:
                seen[code] = [value, value, 1]
            if code == "1-0:99.1.0":
                lp = parse_lp(groups)
                if lp and lp[0] not in lp_seen:
                    lp_seen[lp[0]] = lp[1]

    if not total:
        sys.exit("no telegrams found")
    print(f"telegrams: {total}, CRC ok: {total - bad}, CRC bad: {bad}")
    for h, n in headers.items():
        print(f"header:    {h}  ({n})")
    print(f"codes:     {len(seen)}")
    unknown = [c for c in seen if known and c not in known]
    print("unknown:   " + (", ".join(unknown) if unknown else "none (all codes are in src/obis.cpp)"))

    if args.codes:
        print()
        width = max(len(c) for c in seen)
        for code, (first, last, n) in seen.items():
            mark = " " if not known or code in known else "*"
            change = "" if first == last else f"  ->  {last}"
            print(f"{mark} {code:<{width}}  x{n:<5} {first}{change}")

    if lp_seen:
        print(f"\nload profile entries: {len(lp_seen)} (timestamp = END of the 15-minute period)")
        rows = list(lp_seen.items()) if args.lp else list(lp_seen.items())[-3:]
        for t, vals in rows:
            print(f"  {t}  " + "  ".join(f"{c}={v}" for c, v in vals.items()))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
