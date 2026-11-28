"""Pure-Python ephemeris backend (no pyswisseph needed).

Reads data/ephem.bin (daily Swiss Ephemeris samples 1900-2100, built by build_ephem.py) and
interpolates with 6-point Lagrange polynomials. Ascendant, MC and sunrise/sunset are computed
from sidereal time with IAU formulas and a 4-term nutation. Accuracy versus pyswisseph:
planets well under 1 arc-second, ascendant within a few arc-seconds, sunrise within ~1 minute.
Limitations: no eclipses; house cusps are Porphyry (Placidus needs pyswisseph).
"""
import array
import json
import lzma
import math
import os
import struct
from itertools import accumulate

_DATA = None
_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ephem.bin")
BODY_KEY = {"Sun": "Sun", "Moon": "Moon", "Mars": "Mars", "Mercury": "Mercury",
            "Jupiter": "Jupiter", "Venus": "Venus", "Saturn": "Saturn"}
D2R = math.pi / 180


def _load():
    global _DATA
    if _DATA is None:
        raw = lzma.decompress(open(_PATH, "rb").read())
        hlen = struct.unpack("<I", raw[:4])[0]
        hdr = json.loads(raw[4:4 + hlen])
        pos = 4 + hlen
        n = hdr["n"]
        series = {}
        for s in hdr["series"]:
            diffs = array.array("q")
            nbytes = (n - 1) * 8
            diffs.frombytes(raw[pos:pos + nbytes])
            pos += nbytes
            ints = accumulate(diffs, initial=s["first"])
            series[s["name"]] = array.array("d", (v / hdr["scale"] for v in ints))
        _DATA = {"jd0": hdr["jd0"], "n": n, "series": series, "yearly": hdr["yearly_ayanamsa"],
                 "source": hdr["source"]}
    return _DATA


def _interp(name, jd):
    d = _load()
    x = jd - d["jd0"]
    i = int(math.floor(x))
    if i < 2 or i > d["n"] - 4:
        raise SystemExit("Built-in ephemeris covers 1900-2100 only; install pyswisseph for other dates.")
    ys = d["series"][name]
    xs = range(i - 2, i + 4)
    tot = 0.0
    for a in xs:
        w = 1.0
        for b in xs:
            if b != a:
                w *= (x - b) / (a - b)
        tot += w * ys[a]
    return tot


def _ayan(jd, mode):
    d = _load()
    lah = _interp("AyanLahiri", jd)
    if mode == "lahiri":
        return lah % 360
    yr = d["yearly"]
    t = 1900 + (jd - 2415020.5) / 365.2425
    k = min(max(int(t) - 1900, 0), len(yr[mode]) - 2)
    f = t - (1900 + k)
    off = lambda m: yr[m][k] + (yr[m][k + 1] - yr[m][k]) * f
    return (lah + off(mode) - off("lahiri")) % 360


def _nutation(jd):
    T = (jd - 2451545.0) / 36525
    om = (125.04452 - 1934.136261 * T) * D2R
    L = (280.4665 + 36000.7698 * T) * D2R
    Lm = (218.3165 + 481267.8813 * T) * D2R
    dpsi = (-17.20 * math.sin(om) - 1.32 * math.sin(2 * L) - 0.23 * math.sin(2 * Lm)
            + 0.21 * math.sin(2 * om)) / 3600
    deps = (9.20 * math.cos(om) + 0.57 * math.cos(2 * L) + 0.10 * math.cos(2 * Lm)
            - 0.09 * math.cos(2 * om)) / 3600
    eps0 = 23.439291111 - (46.8150 * T + 0.00059 * T * T - 0.001813 * T ** 3) / 3600
    return dpsi, eps0 + deps


def _lst(jd, lon):
    T = (jd - 2451545.0) / 36525
    gmst = (280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T * T
            - T ** 3 / 38710000)
    dpsi, eps = _nutation(jd)
    return (gmst + dpsi * math.cos(eps * D2R) + lon) % 360, eps


class LiteEphem:
    engine = "built-in (1900-2100)"

    def __init__(self, ayanamsa="lahiri", node="mean", hindu_sunrise=False):
        _load()
        self.ayanamsa = ayanamsa
        self.node = node
        self.h0 = 0.0 if hindu_sunrise else -0.8333

    def _trop(self, jd, p):
        if p in ("Rahu", "Ketu"):
            v = _interp("MeanNode" if self.node == "mean" else "TrueNode", jd)
            return (v + (180 if p == "Ketu" else 0)) % 360
        return _interp(BODY_KEY[p], jd) % 360

    def lon(self, jd, p):
        return (self._trop(jd, p) - _ayan(jd, self.ayanamsa)) % 360

    def lon_speed(self, jd, p):
        h = 0.01
        a = self.lon(jd - h, p)
        b = self.lon(jd + h, p)
        sp = (((b - a + 180) % 360) - 180) / (2 * h)
        return self.lon(jd, p), sp

    def planets(self, jd):
        out = {}
        for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
            lon, sp = self.lon_speed(jd, p)
            out[p] = {"lon": lon, "speed": sp}
        return out

    def ayanamsa_value(self, jd):
        """Mean ayanamsa (as pyswisseph reports it); positions use the true value internally."""
        return (_ayan(jd, self.ayanamsa) - _nutation(jd)[0]) % 360

    def asc_mc(self, jd, lat, lon):
        ramc, eps = _lst(jd, lon)
        th, e, ph = ramc * D2R, eps * D2R, lat * D2R
        asc = math.degrees(math.atan2(math.cos(th), -(math.sin(th) * math.cos(e) + math.tan(ph) * math.sin(e)))) % 360
        mc = math.degrees(math.atan2(math.sin(th), math.cos(th) * math.cos(e))) % 360
        ay = _ayan(jd, self.ayanamsa)
        asc, mc = (asc - ay) % 360, (mc - ay) % 360
        ic, desc = (mc + 180) % 360, (asc + 180) % 360
        arc = lambda a, b: (b - a) % 360
        cusps = [0.0] * 12
        for i0, a, b in ((0, asc, ic), (3, ic, desc), (6, desc, mc), (9, mc, asc)):
            span = arc(a, b)
            for k in range(3):
                cusps[i0 + k] = (a + k * span / 3) % 360
        return asc, mc, cusps, "Porphyry (built-in ephemeris; Placidus needs pyswisseph)"

    def asc(self, jd, lat, lon):
        return self.asc_mc(jd, lat, lon)[0]

    def _sun_alt(self, jd, lat, lon):
        lst, eps = _lst(jd, lon)
        dpsi, _ = _nutation(jd)
        lam = (self._trop(jd, "Sun")) * D2R
        e = eps * D2R
        ra = math.atan2(math.cos(e) * math.sin(lam), math.cos(lam))
        dec = math.asin(math.sin(e) * math.sin(lam))
        H = lst * D2R - ra
        ph = lat * D2R
        return math.degrees(math.asin(math.sin(ph) * math.sin(dec) + math.cos(ph) * math.cos(dec) * math.cos(H)))

    def sun_event(self, jd_start, lat, lon, rise=True):
        f = lambda j: self._sun_alt(j, lat, lon) - self.h0
        step = 5 / 1440
        t, fa = jd_start, f(jd_start)
        while t < jd_start + 1.5:
            t2 = t + step
            fb = f(t2)
            if (rise and fa < 0 <= fb) or (not rise and fa > 0 >= fb):
                a, b = t, t2
                for _ in range(30):
                    m = (a + b) / 2
                    if (f(m) < 0) == (fa < 0):
                        a = m
                    else:
                        b = m
                return b
            t, fa = t2, fb
        return None
