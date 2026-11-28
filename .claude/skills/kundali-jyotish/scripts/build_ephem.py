#!/usr/bin/env python3
"""Build scripts/data/ephem.bin - the built-in ephemeris used when pyswisseph is missing.

Needs pyswisseph. Samples daily at 0h UT from 1900-01-01 to 2100-12-31:
tropical apparent longitudes of Sun..Saturn, mean node and true node, plus the effective
Lahiri ayanamsa (tropical minus sidereal Sun) and yearly offsets of the other ayanamsas.
Longitudes are unwrapped, stored as 1e-7 degree integers, delta-encoded and LZMA-compressed.
"""
import array
import json
import lzma
import os
import struct
import sys

import swisseph as swe

BODIES = [("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS), ("Mercury", swe.MERCURY),
          ("Jupiter", swe.JUPITER), ("Venus", swe.VENUS), ("Saturn", swe.SATURN),
          ("MeanNode", swe.MEAN_NODE), ("TrueNode", swe.TRUE_NODE)]
AYAN = {"lahiri": swe.SIDM_LAHIRI, "kp": swe.SIDM_KRISHNAMURTI, "raman": swe.SIDM_RAMAN,
        "yukteshwar": swe.SIDM_YUKTESHWAR, "true_chitra": swe.SIDM_TRUE_CITRA}
SCALE = 1e7


def unwrap(vals):
    out, off, prev = [], 0.0, None
    for v in vals:
        if prev is not None:
            d = v - prev
            if d > 180:
                off -= 360
            elif d < -180:
                off += 360
        out.append(v + off)
        prev = v
    return out


def encode(vals):
    ints = [int(round(v * SCALE)) for v in vals]
    first = ints[0]
    diffs = array.array("q", [ints[i] - ints[i - 1] for i in range(1, len(ints))])
    return first, diffs


def main(out_path):
    jd0 = swe.julday(1900, 1, 1, 0.0)
    jd1 = swe.julday(2101, 1, 1, 0.0)
    n = int(jd1 - jd0) + 1
    flags = swe.FLG_MOSEPH
    series = {}
    for name, pid in BODIES:
        series[name] = unwrap([swe.calc_ut(jd0 + i, pid, flags)[0][0] for i in range(n)])
    swe.set_sid_mode(AYAN["lahiri"])
    sid = [swe.calc_ut(jd0 + i, swe.SUN, flags | swe.FLG_SIDEREAL)[0][0] for i in range(n)]
    trop = [swe.calc_ut(jd0 + i, swe.SUN, flags)[0][0] for i in range(n)]
    series["AyanLahiri"] = [((t - s) % 360) for t, s in zip(trop, sid)]
    yearly = {}
    for key, mode in AYAN.items():
        swe.set_sid_mode(mode)
        vals = []
        for y in range(1900, 2102):
            j = swe.julday(y, 1, 1, 0.0)
            t = swe.calc_ut(j, swe.SUN, flags)[0][0]
            s = swe.calc_ut(j, swe.SUN, flags | swe.FLG_SIDEREAL)[0][0]
            vals.append((t - s) % 360)
        yearly[key] = vals
    header = {"jd0": jd0, "n": n, "scale": SCALE, "series": [], "yearly_ayanamsa": yearly,
              "source": f"Swiss Ephemeris {swe.version} (Moshier), daily 0h UT"}
    blobs = []
    for name, vals in series.items():
        first, diffs = encode(vals)
        header["series"].append({"name": name, "first": first})
        blobs.append(diffs.tobytes())
    hb = json.dumps(header).encode()
    raw = struct.pack("<I", len(hb)) + hb + b"".join(blobs)
    data = lzma.compress(raw, preset=9 | lzma.PRESET_EXTREME)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as fh:
        fh.write(data)
    print(f"wrote {out_path}: {len(data) / 1e6:.2f} MB, {n} days x {len(series)} series")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "data", "ephem.bin"))
