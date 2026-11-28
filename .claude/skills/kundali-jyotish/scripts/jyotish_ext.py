"""Extra commands for jyotish.py: saved profiles, birth-time rectification, kundali milan
(Ashtakoota) and a muhurta finder. Registered into jyotish.py's CLI by register()."""
import argparse
import importlib
import json
import os
import re
import sys
from datetime import datetime, timedelta

PROFILE_DIR = os.environ.get("KUNDALI_HOME", os.path.join(os.path.expanduser("~"), ".kundali"))
BIRTH_KEYS = ["date", "time", "tz", "lat", "lon", "place", "name", "sex"]


def _J():
    m = sys.modules.get("__main__")
    return m if hasattr(m, "Natal") else importlib.import_module("jyotish")


# --------------------------------------------------------------------------
# Profiles
# --------------------------------------------------------------------------

def _slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "profile"


def load_profile(name):
    path = os.path.join(PROFILE_DIR, _slug(name) + ".json")
    if not os.path.exists(path):
        raise SystemExit(f"No saved profile '{name}' in {PROFILE_DIR}. Use: profile list")
    with open(path) as fh:
        return json.load(fh)


def apply_profile(args):
    name = getattr(args, "profile", None)
    if not name or getattr(args, "cmd", None) == "profile":
        return
    prof = load_profile(name)
    for k in BIRTH_KEYS:
        if getattr(args, k, None) is None and k in prof:
            setattr(args, k, prof[k])


def cmd_profile(args):
    os.makedirs(PROFILE_DIR, exist_ok=True)
    if args.action == "list":
        files = sorted(f for f in os.listdir(PROFILE_DIR) if f.endswith(".json"))
        if not files:
            print(f"No profiles in {PROFILE_DIR}")
        for f in files:
            p = json.load(open(os.path.join(PROFILE_DIR, f)))
            print(f"{p.get('name', f[:-5])}: {p['date']} {p['time']} {p['tz']} "
                  f"({p.get('place') or str(p['lat']) + ',' + str(p['lon'])})")
        return
    if not args.profile:
        raise SystemExit("Give --profile NAME")
    path = os.path.join(PROFILE_DIR, _slug(args.profile) + ".json")
    if args.action == "show":
        print(json.dumps(load_profile(args.profile), indent=1, ensure_ascii=False))
    elif args.action == "delete":
        if os.path.exists(path):
            os.remove(path)
        print(f"deleted {path}")
    elif args.action == "save":
        missing = [k for k in ("date", "time", "tz", "lat", "lon") if getattr(args, k) is None]
        if missing:
            raise SystemExit(f"profile save needs {missing}")
        data = {k: getattr(args, k) for k in BIRTH_KEYS if getattr(args, k, None) is not None}
        data["name"] = args.name or args.profile
        if args.sex:
            data["sex"] = args.sex
        with open(path, "w") as fh:
            json.dump(data, fh, indent=1, ensure_ascii=False)
        print(f"saved {path}")


# --------------------------------------------------------------------------
# Birth-time rectification
# --------------------------------------------------------------------------

# event type -> (houses from Lagna, karakas, varga to check)
EVENT_RULES = {
    "marriage": ([7, 2, 11], ["Venus", "Jupiter"], 9),
    "engagement": ([7, 2, 11], ["Venus", "Jupiter"], 9),
    "divorce": ([6, 8, 12, 7], ["Venus", "Saturn", "Rahu"], 9),
    "child": ([5, 2, 11], ["Jupiter"], 7),
    "job": ([10, 6, 11, 2], ["Sun", "Saturn", "Mercury"], 10),
    "promotion": ([10, 11, 2], ["Sun", "Jupiter"], 10),
    "job_loss": ([12, 8, 5, 9], ["Saturn", "Rahu"], 10),
    "business": ([7, 10, 11], ["Mercury"], 10),
    "education": ([4, 5, 9, 11], ["Mercury", "Jupiter"], 24),
    "foreign": ([12, 9, 3, 7], ["Rahu", "Saturn"], None),
    "property": ([4, 11, 2], ["Mars", "Venus", "Saturn"], 4),
    "vehicle": ([4, 11], ["Venus"], 16),
    "accident": ([6, 8, 12, 1], ["Mars", "Rahu", "Saturn"], None),
    "illness": ([6, 8, 12, 1], ["Saturn", "Rahu", "Sun"], None),
    "father_loss": ([9, 10, 3, 4], ["Sun", "Saturn"], 12),
    "mother_loss": ([4, 5, 10, 11], ["Moon", "Saturn"], 12),
    "sibling": ([3, 11], ["Mars"], 3),
}


def _signifies(J, n, planet, houses, karakas):
    L = n.lagna
    base = J.SIGN_LORD[n.signs[planet]] if planet in ("Rahu", "Ketu") else planet
    owned = J.owned_houses(base, L)
    occ = J.house_from(n.signs[planet], L)
    star = J.nakshatra_info(n.lons[planet])["lord"]
    sbase = J.SIGN_LORD[n.signs[star]] if star in ("Rahu", "Ketu") else star
    s = 0.0
    s += 1.0 if set(owned) & set(houses) else 0
    s += 1.0 if occ in houses else 0
    s += 0.5 if (set(J.owned_houses(sbase, L)) & set(houses)
                 or J.house_from(n.signs[star], L) in houses) else 0
    s += 0.5 if planet in karakas else 0
    return s


def _event_score(J, n, jd, etype):
    houses, karakas, varga = EVENT_RULES[etype]
    e = n.eph
    path = n.dasha.path(jd, 3)
    lords = [p[0] for p in path]
    score = sum(w * _signifies(J, n, lord, houses, karakas) for (lord, _, _), w in zip(path, (3.0, 2.0, 1.0)))
    targets = {(n.lagna + h - 1) % 12 for h in houses[:2]}
    targets |= {n.signs[J.SIGN_LORD[t]] for t in list(targets)}
    for tp in ("Jupiter", "Saturn"):
        ts = J.sign_of(e.lon(jd, tp))
        if targets & ({ts} | set(J.aspected_signs(tp, ts))):
            score += 1.0
    if varga:
        vl = J.varga_sign(n.asc_lon, varga)
        vlord = J.SIGN_LORD[(vl + houses[0] - 1) % 12]
        if vlord in lords[:2]:
            score += 1.0
        if J.SIGN_LORD[vl] in lords[:2]:
            score += 0.5
    return score


def cmd_rectify(args):
    J = _J()
    events = []
    for ev in args.event or []:
        try:
            d, t = ev.split(":", 1)
            events.append((J.parse_date(d.strip()), t.strip().lower()))
        except ValueError:
            raise SystemExit(f"Bad --event '{ev}'. Use YYYY-MM-DD:type")
        if events[-1][1] not in EVENT_RULES:
            raise SystemExit(f"Unknown event type '{events[-1][1]}'. Types: {', '.join(EVENT_RULES)}")
    if len(events) < 2:
        raise SystemExit("Give at least 2 (ideally 4-6) --event YYYY-MM-DD:type entries.")
    h, m, sec = J.parse_time(args.time)
    base = J.parse_date(args.date).replace(hour=h, minute=m, second=sec)
    tz = J.TZ(args.tz)
    rows, best = [], []
    k = -args.window
    while k <= args.window:
        cand = base + timedelta(minutes=k)
        ns = argparse.Namespace(**vars(args))
        ns.date, ns.time = cand.strftime("%Y-%m-%d"), cand.strftime("%H:%M:%S")
        n = J.Natal(ns)
        ev_scores = []
        for d, etype in events:
            jd = J.jd_from_utc(tz.to_utc(d.replace(hour=12)))
            ev_scores.append(_event_score(J, n, jd, etype))
        tot = sum(ev_scores)
        mn = J.nakshatra_info(n.lons["Moon"])
        key = (J.SIGNS[n.lagna][:3], J.SIGNS[J.varga_sign(n.asc_lon, 9)][:3],
               J.SIGNS[J.varga_sign(n.asc_lon, 10)][:3])
        rows.append((k, cand, tot, ev_scores, key, f"{mn['name']}-{mn['pada']}", n.asc_lon))
        k += args.step
    top = max(r[2] for r in rows)
    out = [f"# Birth-time rectification ({base:%Y-%m-%d %H:%M} +/-{args.window} min, step {args.step} min)",
           "",
           "Events: " + "; ".join(f"{d:%Y-%m-%d} {t}" for d, t in events),
           "",
           "Score per event = dasha lords (MD x3, AD x2, PD x1) signifying the event houses/karakas "
           "+ Jupiter/Saturn transit on those houses + varga (D9/D10/D7...) lord in the dasha.",
           ""]
    seg_rows, prev, start = [], None, None
    for r in rows:
        if r[4] != prev:
            if prev is not None:
                seg_rows.append((start, last, prev, seg_best))
            prev, start, seg_best = r[4], r, r
        last = r
        if r[2] > seg_best[2]:
            seg_best = r
    seg_rows.append((start, last, prev, seg_best))
    out.append("## Segments (Lagna / D9 lagna / D10 lagna stay constant)\n")
    out.append(J.table(["From", "To", "Lagna", "D9", "D10", "Best time in segment", "Best score"],
                       [[f"{a[1]:%H:%M:%S}", f"{b[1]:%H:%M:%S}", key[0], key[1], key[2],
                         f"{sb[1]:%H:%M:%S}", f"{sb[2]:.1f}"] for a, b, key, sb in seg_rows]))
    out.append("\n## Top candidate times\n")
    ranked = sorted(rows, key=lambda r: (-r[2], abs(r[0])))[:args.top]
    out.append(J.table(["Time", "Offset", "Score", "Lagna (deg)", "D9", "D10", "Moon nak-pada"]
                       + [f"{t} {d:%Y}" for d, t in events],
                       [[f"{r[1]:%H:%M:%S}", f"{r[0]:+d} min", f"{r[2]:.1f}",
                         f"{J.SIGNS[J.sign_of(r[6])][:3]} {J.deg_in_sign(r[6]):.2f}", r[4][1], r[4][2], r[5]]
                        + [f"{s:.1f}" for s in r[3]] for r in ranked]))
    recorded = next(r for r in rows if r[0] == 0)
    out.append(f"\nRecorded time scores {recorded[2]:.1f}; best {top:.1f}. "
               "Prefer the segment that wins across most events, not a single spike; confirm with "
               "the native's appearance/temperament (Lagna) and spouse/career descriptions (D9/D10).")
    print("\n".join(out))


# --------------------------------------------------------------------------
# Kundali milan (Ashtakoota)
# --------------------------------------------------------------------------

VARNA_RANK = {3: 4, 7: 4, 11: 4, 0: 3, 4: 3, 8: 3, 1: 2, 5: 2, 9: 2, 2: 1, 6: 1, 10: 1}
VARNA_NAME = {4: "Brahmin", 3: "Kshatriya", 2: "Vaishya", 1: "Shudra"}
VASHYA_NAMES = ["Chatushpada", "Manava", "Jalachara", "Vanachara", "Keeta"]
# rows = bride, columns = groom (most common published grid)
VASHYA_PTS = [[2, 1, 1, 1.5, 1], [1, 2, 1.5, 0, 1], [1, 1.5, 2, 1, 1], [0, 0, 0, 2, 0], [1, 1, 1, 0, 2]]
YONI_ORDER = ["Horse", "Elephant", "Sheep", "Serpent", "Dog", "Cat", "Rat", "Cow", "Buffalo",
              "Tiger", "Deer", "Monkey", "Mongoose", "Lion"]
YONI_PTS = [
    [4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 3, 3, 2, 1],
    [2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0],
    [2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1],
    [3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2],
    [2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1],
    [2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1],
    [2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2],
    [1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1],
    [0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 1],
    [1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1],
    [3, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1],
    [3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2],
    [2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2],
    [1, 0, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 2, 4],
]
GANA_PTS = {("Deva", "Deva"): 6, ("Manushya", "Manushya"): 6, ("Rakshasa", "Rakshasa"): 6,
            ("Deva", "Manushya"): 5, ("Manushya", "Deva"): 5, ("Deva", "Rakshasa"): 1,
            ("Rakshasa", "Deva"): 0, ("Manushya", "Rakshasa"): 1, ("Rakshasa", "Manushya"): 0}
# keys are (groom gana, bride gana)


def _vashya(lon):
    s, d = int(lon // 30) % 12, lon % 30
    if s in (0, 1) or (s == 8 and d >= 15) or (s == 9 and d < 15):
        return 0
    if s in (2, 5, 6, 10) or (s == 8 and d < 15):
        return 1
    if s in (3, 11) or (s == 9 and d >= 15):
        return 2
    return 3 if s == 4 else 4


def manglik_status(J, n):
    S = n.signs
    refs = {"Lagna": n.lagna, "Moon": S["Moon"], "Venus": S["Venus"]}
    hits = [k for k, r in refs.items() if J.house_from(S["Mars"], r) in (1, 2, 4, 7, 8, 12)]
    canc = []
    dg = J.dignity("Mars", n.lons["Mars"], S)
    if dg.startswith("Exalted") or dg in ("Own sign", "Moolatrikona"):
        canc.append("Mars own/exalted")
    if S["Mars"] == S["Jupiter"] or S["Mars"] in J.aspected_signs("Jupiter", S["Jupiter"]):
        canc.append("Jupiter with/aspecting Mars")
    level = "none" if not hits else ("cancelled" if canc else ("full" if "Lagna" in hits else "partial"))
    return level, hits, canc


def _person(spec, base):
    J = _J()
    ns = argparse.Namespace(**vars(base))
    if "," in spec:
        parts = [x.strip() for x in spec.split(",")]
        if len(parts) < 5:
            raise SystemExit("Inline spec must be 'YYYY-MM-DD,HH:MM,TZ,LAT,LON[,Name]'")
        ns.date, ns.time, ns.tz = parts[0], parts[1], parts[2]
        ns.lat, ns.lon = float(parts[3]), float(parts[4])
        ns.name = parts[5] if len(parts) > 5 else None
    else:
        prof = load_profile(spec)
        for k in BIRTH_KEYS:
            setattr(ns, k, prof.get(k))
    return J.Natal(ns), ns.name or spec


def cmd_match(args):
    J = _J()
    boy, bname = _person(args.boy, args)
    girl, gname = _person(args.girl, args)
    bm, gm = boy.lons["Moon"], girl.lons["Moon"]
    bs, gs = J.sign_of(bm), J.sign_of(gm)
    bn, gn = J.nakshatra_info(bm), J.nakshatra_info(gm)
    rows, total, notes = [], 0.0, []
    # 1 Varna
    v = 1 if VARNA_RANK[bs] >= VARNA_RANK[gs] else 0
    rows.append(["Varna (1)", VARNA_NAME[VARNA_RANK[bs]], VARNA_NAME[VARNA_RANK[gs]], v])
    # 2 Vashya
    vb, vg = _vashya(bm), _vashya(gm)
    va = VASHYA_PTS[vg][vb]
    rows.append(["Vashya (2)", VASHYA_NAMES[vb], VASHYA_NAMES[vg], va])
    # 3 Tara
    def good(a, b):
        r = ((b - a) % 27 + 1) % 9
        return r not in (3, 5, 7)
    ta = 1.5 * good(gn["index"], bn["index"]) + 1.5 * good(bn["index"], gn["index"])
    rows.append(["Tara (3)", bn["name"], gn["name"], ta])
    # 4 Yoni
    yb, yg = J.YONI[bn["index"]], J.YONI[gn["index"]]
    yo = YONI_PTS[YONI_ORDER.index(yb)][YONI_ORDER.index(yg)]
    rows.append(["Yoni (4)", yb, yg, yo])
    # 5 Graha maitri
    lb, lg = J.SIGN_LORD[bs], J.SIGN_LORD[gs]
    if lb == lg:
        gmv = 5
    else:
        r1, r2 = J.natural_rel(lb, lg), J.natural_rel(lg, lb)
        pair = sorted([r1, r2])
        gmv = {("friend", "friend"): 5, ("friend", "neutral"): 4, ("neutral", "neutral"): 3,
               ("enemy", "friend"): 1, ("enemy", "neutral"): 0.5, ("enemy", "enemy"): 0}[tuple(pair)]
    rows.append(["Graha maitri (5)", lb, lg, gmv])
    # 6 Gana
    gab, gag = J.GANA[bn["index"]], J.GANA[gn["index"]]
    ga = GANA_PTS[(gab, gag)]
    rows.append(["Gana (6)", gab, gag, ga])
    # 7 Bhakoot
    d1, d2 = J.house_from(bs, gs), J.house_from(gs, bs)
    bad_bh = {d1, d2} in ({2, 12}, {6, 8}, {5, 9})
    bh = 0 if bad_bh else 7
    rows.append(["Bhakoot (7)", J.SIGNS[bs], J.SIGNS[gs], bh])
    # 8 Nadi
    nb, ng = J.NADI[bn["index"]], J.NADI[gn["index"]]
    na = 0 if nb == ng else 8
    rows.append(["Nadi (8)", nb, ng, na])
    total = sum(r[3] for r in rows)
    # exceptions
    if na == 0:
        if bs == gs and bn["index"] != gn["index"]:
            notes.append("Nadi dosha traditionally cancelled: same Moon sign, different nakshatra.")
        elif bn["index"] == gn["index"] and bs != gs:
            notes.append("Nadi dosha traditionally cancelled: same nakshatra, different Moon sign.")
        elif bn["index"] == gn["index"] and bn["pada"] != gn["pada"]:
            notes.append("Nadi dosha reduced (some traditions): same nakshatra, different pada.")
        else:
            notes.append("NADI DOSHA present (no standard cancellation) - the most weighted dosha in Ashtakoota.")
    if bh == 0:
        if lb == lg or (J.natural_rel(lb, lg) == "friend" and J.natural_rel(lg, lb) == "friend"):
            notes.append("Bhakoot dosha traditionally cancelled: Moon-sign lords same or mutual friends.")
        else:
            notes.append(f"BHAKOOT DOSHA present ({d1}/{d2} relation).")
    if ga <= 1 and (gmv >= 4 or bh == 7):
        notes.append("Gana mismatch eased by good Graha maitri / Bhakoot (traditional parihara).")
    verdict = ("excellent" if total >= 33 else "very good" if total >= 25 else
               "acceptable" if total >= 18 else "below the traditional minimum of 18")
    mb, mg = manglik_status(J, boy), manglik_status(J, girl)
    out = [f"# Kundali milan: {bname} (groom) & {gname} (bride)", "",
           J.table(["Koota (max)", "Groom", "Bride", "Points"], rows),
           f"\n**Total: {total:g} / 36 - {verdict}.**", ""]
    out += [f"- {x}" for x in notes]
    out.append("\n**Manglik comparison**\n")
    out.append(J.table(["", "Level", "Mars counts from", "Cancellations"],
                       [["Groom", mb[0], ", ".join(mb[1]) or "-", "; ".join(mb[2]) or "-"],
                        ["Bride", mg[0], ", ".join(mg[1]) or "-", "; ".join(mg[2]) or "-"]]))
    active = lambda m: m[0] in ("full", "partial")
    if active(mb) != active(mg):
        out.append("\nOnly one side is Manglik (uncancelled): traditional mismatch - remedies or matching advised.")
    elif active(mb):
        out.append("\nBoth Manglik: traditionally the doshas balance each other.")
    if args.system in ("south", "both"):
        import jyotish_more
        dk, goods = jyotish_more.dashakoota(J, boy, girl)
        out.append(f"\n**South Indian Dashakoota (10 poruthams): {goods}/10 good**\n")
        out.append(J.table(["Porutham", "Basis", "Result"], dk))
        out.append("Rajju and Vedha are decisive in South Indian practice; rules vary by region.")
    out.append("\nAlso compare: 7th houses and lords, Venus/Jupiter, D9 charts, and both running dashas "
               "for the planned marriage year (run `chart --profile` for each).")
    print("\n".join(out))


# --------------------------------------------------------------------------
# Muhurta finder
# --------------------------------------------------------------------------

ALL_GOOD_NAK = {0, 3, 4, 6, 7, 11, 12, 13, 14, 16, 20, 21, 22, 23, 25, 26}
PURPOSES = {
    "marriage": dict(nak={3, 4, 9, 11, 12, 14, 16, 18, 20, 25, 26}, days={0, 2, 3, 4},
                     chog={"Amrit", "Shubh", "Labh"}, lagna="fixed_dual", seasonal=True,
                     chog_required=False, night=True),
    "griha_pravesh": dict(nak={3, 4, 11, 13, 16, 20, 25, 26}, days={0, 2, 3, 4},
                          chog={"Amrit", "Shubh", "Labh"}, lagna="fixed", seasonal=True,
                          chog_required=False),
    "vehicle": dict(nak={0, 6, 7, 12, 13, 14, 16, 21, 22, 26}, days={0, 2, 3, 4},
                    chog={"Amrit", "Shubh", "Labh", "Chal"}, lagna="movable", seasonal=False),
    "business": dict(nak={0, 3, 7, 11, 12, 13, 16, 20, 21, 25, 26}, days={2, 3, 4},
                     chog={"Amrit", "Shubh", "Labh"}, lagna="fixed", seasonal=False),
    "travel": dict(nak={0, 4, 6, 7, 12, 16, 21, 22, 26}, days={0, 2, 3, 4, 6},
                   chog={"Amrit", "Shubh", "Labh", "Chal"}, lagna="movable", seasonal=False),
    "interview": dict(nak=ALL_GOOD_NAK, days={0, 1, 2, 3, 4, 5, 6},
                      chog={"Amrit", "Shubh", "Labh"}, lagna="any", seasonal=False),
    "general": dict(nak=ALL_GOOD_NAK, days={0, 1, 2, 3, 4, 5, 6},
                    chog={"Amrit", "Shubh", "Labh"}, lagna="any", seasonal=False),
}
BAD_YOGAS = {"Vishkambha", "Atiganda", "Shula", "Ganda", "Vyaghata", "Vajra", "Vyatipata",
             "Parigha", "Vaidhriti"}
RIKTA = {3, 8, 13, 18, 23, 28}
MONTHS = ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada", "Ashvin",
          "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna"]


def lunar_month(J, e, jd):
    """Amanta lunar month (index into MONTHS, adhik flag) for a moment."""
    elong = lambda j: (e.lon(j, "Moon") - e.lon(j, "Sun")) % 360
    t = jd - elong(jd) / 12.19
    for _ in range(4):
        t -= (((elong(t) + 180) % 360) - 180) / 12.19
    nxt = t + 29.53
    for _ in range(4):
        nxt -= (((elong(nxt) + 180) % 360) - 180) / 12.19
    s1, s2 = J.sign_of(e.lon(t, "Sun")), J.sign_of(e.lon(nxt, "Sun"))
    return (s1 + 1) % 12, s1 == s2


def cmd_muhurta(args):
    J = _J()
    rule = PURPOSES[args.purpose]
    person = None
    if args.date and args.time and args.tz and args.lat is not None:
        person = J.Natal(args)
    tz = J.TZ(args.at_tz or args.tz or "Asia/Kolkata")
    lat = args.at_lat if args.at_lat is not None else args.lat
    lon = args.at_lon if args.at_lon is not None else args.lon
    if lat is None or lon is None:
        raise SystemExit("Give the place: --at-lat --at-lon --at-tz (or a profile).")
    e = person.eph if person else J.make_ephem(args)
    natal_nak = J.nakshatra_info(person.lons["Moon"])["index"] if person else None
    d0, d1 = J.parse_date(getattr(args, "from")), J.parse_date(args.to)
    loc = lambda j: tz.from_utc(J.utc_from_jd(j))
    days, excluded = [], {}
    day = d0
    while day <= d1:
        jd_mid = J.jd_from_utc(tz.to_utc(day))
        sr = e.sun_event(jd_mid, lat, lon, True)
        ss = e.sun_event(sr, lat, lon, False)
        sr2 = e.sun_event(ss, lat, lon, True)
        wd = day.weekday()
        reason = None
        if wd not in rule["days"]:
            reason = "weekday"
        if rule["seasonal"] and not reason:
            sun_sign = J.sign_of(e.lon(sr, "Sun"))
            mi, adhik = lunar_month(J, e, sr)
            tithi = J.panchang_at(e, sr)["tithi_index"]
            if sun_sign in (8, 11):
                reason = "Kharmas (Sun in Dhanu/Meen)"
            elif adhik:
                reason = "Adhik maas"
            elif (mi == 3 and tithi >= 10) or mi in (4, 5, 6) or (mi == 7 and tithi < 10):
                reason = "Chaturmas"
            else:
                for pl in ("Jupiter", "Venus"):
                    if J.combustion(pl, e.lon(sr, pl), e.lon(sr, "Sun"), e.lon_speed(sr, pl)[1] < 0) is not None:
                        reason = f"{pl} combust (asta)"
        if reason:
            excluded[reason] = excluded.get(reason, 0) + 1
            day += timedelta(days=1)
            continue
        part = (ss - sr) / 8
        bad_win = [(sr + (k - 1) * part, sr + k * part) for k in
                   (J.RAHU_KAAL_PART[wd], J.YAMAGANDA_PART[wd], J.GULIKA_PART[wd])]
        idx = J.HORA_ORDER.index(J.WEEKDAY_LORD[wd])
        dpart, npart = (ss - sr) / 8, (sr2 - ss) / 8

        def chog_at(j):
            if j < ss:
                k = int((j - sr) / dpart)
                return J.CHOGHADIYA[J.HORA_ORDER[(idx + k) % 7]]
            k = int((j - ss) / npart)
            return J.CHOGHADIYA[J.HORA_ORDER[((idx + 5) - 2 * k) % 7]]
        end = sr2 if (args.include_night or rule.get("night")) else ss
        slots, j = [], sr
        step = 10 / 1440
        while j < end - 1e-9:
            mid = j + step / 2
            pan = J.panchang_at(e, mid)
            ok = (pan["nak_index"] in rule["nak"] and pan["tithi_index"] not in RIKTA
                  and pan["tithi_index"] != 29 and pan["yoga"] not in BAD_YOGAS
                  and not pan["karana"].startswith("Vishti")
                  and not any(a <= mid < b for a, b in bad_win)
                  and (chog_at(mid) in rule["chog"] or not rule.get("chog_required", True)))
            moon_lon = e.lon(mid, "Moon")
            if ok and moon_lon >= 300 and args.purpose in ("griha_pravesh", "travel"):
                ok = False    # Panchak: Moon in Aquarius/Pisces (Dhanishta 3rd pada to Revati)
            asg = J.sign_of(e.asc(mid, lat, lon))
            mod = asg % 3
            if ok and rule["lagna"] == "fixed" and mod != 1:
                ok = False
            if ok and rule["lagna"] == "fixed_dual" and mod == 0:
                ok = False
            if ok and rule["lagna"] == "movable" and mod != 0:
                ok = False
            tara = None
            if ok and person:
                tr = ((pan["nak_index"] - natal_nak) % 27) % 9
                hm = J.house_from(J.sign_of(e.lon(mid, "Moon")), person.moon_sign)
                if tr in (2, 4, 6) or hm in (4, 8, 12):
                    ok = False
                tara = J.TARA[tr].split(" (")[0]
            slots.append((j, j + step, ok, pan, asg, chog_at(mid), tara))
            j += step
        windows, cur = [], None
        for s in slots:
            if s[2]:
                cur = [s[0], s[1], s] if cur is None else [cur[0], s[1], cur[2]]
            elif cur:
                windows.append(cur)
                cur = None
        if cur:
            windows.append(cur)
        windows = [w for w in windows if (w[1] - w[0]) * 1440 >= args.min_minutes]
        if not windows:
            excluded["no clean window"] = excluded.get("no clean window", 0) + 1
        for w in windows:
            pan, asg, chog, tara = w[2][3], w[2][4], w[2][5], w[2][6]
            score = (w[1] - w[0]) * 1440 / 10 + (5 if chog == "Amrit" else 2 if chog in ("Shubh", "Labh") else 0) + (
                3 if pan["nakshatra"] in ("Pushya", "Rohini", "Uttara Phalguni", "Revati") else 0) + (
                3 if tara in ("Sampat", "Sadhaka", "Parama Mitra") else 0)
            days.append((score, day, w, pan, asg, chog, tara))
        day += timedelta(days=1)
    days.sort(key=lambda x: -x[0])
    out = [f"# Muhurta: {args.purpose.replace('_', ' ')} ({d0:%d %b %Y} - {d1:%d %b %Y}, "
           f"{lat:.3f},{lon:.3f})", ""]
    if person:
        out.append("Personal tarabala and chandrabala applied for the native.\n")
    if days:
        out.append(J.table(["Rank", "Date", "Window", "Nakshatra", "Tithi", "Yoga", "Lagna at start",
                            "Choghadiya", "Tara"],
                           [[i + 1, f"{loc(w[0]):%a %d %b %Y}", f"{J.fmt_local(loc(w[0]), False)}-{J.fmt_local(loc(w[1]), False)}",
                             pan["nakshatra"], pan["tithi"], pan["yoga"], J.SIGNS[asg], chog, tara or "-"]
                            for i, (sc, d, w, pan, asg, chog, tara) in enumerate(days[:args.top])]))
    else:
        out.append("No window passed all rules in this range - widen the range or use --include-night.")
    if excluded:
        out.append("\nDays excluded: " + ", ".join(f"{k} {v}" for k, v in excluded.items()))
    out.append("\nRules: purpose nakshatras and weekdays, no Rikta tithi/Amavasya, no bad yoga, no Vishti "
               "(Bhadra), no Rahu kaal/Yamaganda/Gulika, lagna type, good choghadiya"
               + (" (bonus only)" if not rule.get("chog_required", True) else "")
               + (", no Panchak" if args.purpose in ("griha_pravesh", "travel") else "")
               + (", Kharmas/Chaturmas/Adhik maas/Guru-Shukra asta excluded" if rule["seasonal"] else "")
               + ". Windows shown are the first 10-minute slot's panchang.")
    print("\n".join(out))



# --------------------------------------------------------------------------
# verify: check a report's numbers against a fresh calculation
# --------------------------------------------------------------------------

SIGN_ALIAS = {}
for i, names in enumerate([
        ("aries", "mesh", "mesha", "ari"), ("taurus", "vrishabh", "vrishabha", "vrushabh", "vrisabh", "tau"),
        ("gemini", "mithun", "mithuna", "gem"), ("cancer", "kark", "karka", "karkat", "can"),
        ("leo", "simha", "singh", "sinh"), ("virgo", "kanya", "vir"), ("libra", "tula", "lib"),
        ("scorpio", "vrishchik", "vrischik", "vrishchika", "vrushchik", "sco"),
        ("sagittarius", "dhanu", "dhanus", "sag"), ("capricorn", "makar", "makara", "cap"),
        ("aquarius", "kumbh", "kumbha", "aqu"), ("pisces", "meen", "meena", "mina", "pis")]):
    for nm in names:
        SIGN_ALIAS[nm] = i
PLANET_ALIAS = {"sun": "Sun", "surya": "Sun", "su": "Sun", "moon": "Moon", "chandra": "Moon", "mo": "Moon",
                "mars": "Mars", "mangal": "Mars", "ma": "Mars", "mercury": "Mercury", "budh": "Mercury",
                "me": "Mercury", "jupiter": "Jupiter", "guru": "Jupiter", "ju": "Jupiter", "brihaspati": "Jupiter",
                "venus": "Venus", "shukra": "Venus", "ve": "Venus", "saturn": "Saturn", "shani": "Saturn",
                "sa": "Saturn", "rahu": "Rahu", "ra": "Rahu", "ketu": "Ketu", "ke": "Ketu",
                "lagna": "Lagna", "asc": "Lagna", "ascendant": "Lagna", "la": "Lagna"}


def parse_position(v):
    """'Leo 06°42'21"', 'Simha 6-42-21', '6:42:21 Leo', '126.7056' -> absolute degrees."""
    if isinstance(v, (int, float)):
        return float(v) % 360
    txt = str(v).lower()
    sign = None
    for word in re.findall(r"[a-z]+", txt):
        if word in SIGN_ALIAS:
            sign = SIGN_ALIAS[word]
            break
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", txt)]
    if not nums:
        raise ValueError(f"no number in position '{v}'")
    deg = nums[0] + (nums[1] / 60 if len(nums) > 1 else 0) + (nums[2] / 3600 if len(nums) > 2 else 0)
    if sign is None:
        return deg % 360
    return (sign * 30 + deg) % 360


def cmd_verify(args):
    J = _J()
    rep = json.load(open(args.report))
    for k in ("date", "time", "tz", "lat", "lon"):
        if getattr(args, k, None) is None and k in rep:
            setattr(args, k, rep[k])
    missing = [k for k in ("date", "time", "tz", "lat", "lon") if getattr(args, k, None) is None]
    if missing:
        raise SystemExit(f"verify needs birth details {missing} (flags, --profile, or in the JSON)")
    n = J.Natal(args)
    given = {}
    for k, v in (rep.get("planets") or {}).items():
        p = PLANET_ALIAS.get(k.strip().lower())
        if p:
            given[p] = parse_position(v)
    if "lagna" in rep:
        given["Lagna"] = parse_position(rep["lagna"])
    comp = dict(n.lons)
    comp["Lagna"] = n.asc_lon
    rows, diffs = [], {}
    for p in ["Lagna"] + J.PLANETS:
        if p not in given:
            continue
        d = ((given[p] - comp[p] + 180) % 360 - 180) * 60   # arc-minutes, report minus computed
        diffs[p] = d
        st = "OK" if abs(d) < 5 else "close" if abs(d) < 60 else "MISMATCH"
        rows.append([p, J.fmt_lon(given[p]), J.fmt_lon(comp[p]), f"{d:+.1f}'",
                     "same" if J.sign_of(given[p]) == J.sign_of(comp[p]) else "DIFFERENT SIGN", st])
    out = [f"# Report check ({args.ayanamsa} ayanamsa, {args.node} node, {n.eph.engine})", "",
           J.table(["Body", "Report", "Computed", "Diff (report-computed)", "Sign", "Status"], rows), ""]
    diag = []
    slow = [diffs[p] for p in ("Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn") if p in diffs]
    if len(slow) >= 3:
        med = sorted(slow)[len(slow) // 2]
        spread = max(slow) - min(slow)
        if abs(med) >= 3 and spread < max(3, abs(med) * 0.3):
            best = None
            for ay in ("lahiri", "kp", "raman", "yukteshwar", "true_chitra"):
                ns = argparse.Namespace(**vars(args))
                ns.ayanamsa = ay
                e2 = J.make_ephem(ns)
                off = (((e2.lon(n.jd, "Sun") - n.lons["Sun"]) + 180) % 360 - 180) * 60
                if best is None or abs(off - med) < abs(best[1] - med):
                    best = (ay, off)
            if abs(med) > 1000:
                diag.append(f"All planets differ by ~{med / 60:.1f}°: the report is probably TROPICAL (Western). Use sidereal values.")
            else:
                diag.append(f"All planets differ by ~{med:+.1f}': a different ayanamsa - closest is '{best[0]}' "
                            f"(offset {best[1]:+.1f}'). Re-run with --ayanamsa {best[0]} to match the report, or explain the difference.")
        elif spread >= 3:
            diag.append("Planet differences are not uniform: check the birth DATE and whether the report used the same place/time zone.")
    if "Lagna" in diffs and abs(diffs["Lagna"]) >= 30 and (not slow or max(abs(x) for x in slow) < 10):
        target = given["Lagna"]
        tried = []
        for label, mins in (("1 hour: war time (1942-45) or DST was handled differently by the report", 60),
                            ("1 hour: war time (1942-45) or DST was handled differently by the report", -60),
                            ("12 hours: AM/PM was swapped", 720), ("12 hours: AM/PM was swapped", -720),
                            ("30 minutes: wrong time-zone offset", 30), ("30 minutes: wrong time-zone offset", -30)):
            a = n.eph.asc(n.jd - mins / 1440, n.lat, n.lon)
            tried.append((abs(((target - a + 180) % 360) - 180), label))
        tried.sort()
        if tried[0][0] < 1.0:
            diag.append(f"The report's Lagna matches our chart shifted by {tried[0][1]}. Confirm the recorded "
                        "clock time with the person and say which chart you use.")
        else:
            rate = 0.25  # roughly 1 degree of ascendant per 4 minutes
            diag.append(f"Lagna differs by {diffs['Lagna'] / 60:+.2f}° (~{abs(diffs['Lagna']) / 60 / rate:.0f} min of time) "
                        "while planets agree: different birth time or coordinates in the report.")
    if "Moon" in diffs and abs(diffs["Moon"]) >= 5 and (not slow or max(abs(x) for x in slow) < 3):
        mins = diffs["Moon"] / 60 / (n.pl["Moon"]["speed"] / 1440)
        diag.append(f"Moon differs by {diffs['Moon']:+.1f}' = about {mins:+.0f} min of birth time; every dasha date shifts accordingly.")
    if "Rahu" in diffs and 5 <= abs(diffs["Rahu"]) <= 120:
        ns = argparse.Namespace(**vars(args))
        ns.node = "true" if args.node == "mean" else "mean"
        alt = J.make_ephem(ns).lon(n.jd, "Rahu")
        if abs(((given["Rahu"] - alt + 180) % 360) - 180) * 60 < 5:
            diag.append(f"Rahu/Ketu match the {ns.node} node: the report uses the {ns.node} node (use --node {ns.node}).")
    for md in rep.get("dasha", []):
        lord = md.get("lord", "").strip().title()
        hit = next((m for m in n.dasha.mds if m[0] == lord and abs(m[1] - J.jd_from_utc(n.tz.to_utc(J.parse_date(md['start'])))) < 400)
                   if md.get("start") else None, None)
        if hit:
            dd = (J.jd_from_utc(n.tz.to_utc(J.parse_date(md["start"]))) - hit[1])
            diag.append(f"{lord} Mahadasha start differs by {dd:+.0f} days"
                        + (" (year-length convention, fine)" if abs(dd) <= 10 else " (Moon/birth-time difference - check)"))
    out.append("**Diagnosis**\n")
    out += [f"- {d}" for d in diag] or ["- Report and calculation agree; proceed with the computed data."]
    print("\n".join(out))

# --------------------------------------------------------------------------
# CLI registration
# --------------------------------------------------------------------------

def register(sub, add_birth, add_at):
    p = sub.add_parser("profile", help="save / list / show / delete birth profiles")
    p.add_argument("action", choices=["save", "list", "show", "delete"])
    add_birth(p)
    p.add_argument("--sex", choices=["male", "female", "other"], default=None)
    p.set_defaults(fn=cmd_profile, needs_birth=False)

    r = sub.add_parser("rectify", help="birth-time rectification from life events")
    add_birth(r)
    r.add_argument("--event", action="append", help="YYYY-MM-DD:type (repeat). Types: " + ", ".join(EVENT_RULES))
    r.add_argument("--window", type=int, default=30, help="minutes either side of the recorded time")
    r.add_argument("--step", type=int, default=1, help="minutes between candidates")
    r.add_argument("--top", type=int, default=10)
    r.set_defaults(fn=cmd_rectify)

    m = sub.add_parser("match", help="kundali milan (Ashtakoota 36 gunas + Manglik)")
    add_birth(m)
    m.add_argument("--boy", required=True, help="profile name or 'YYYY-MM-DD,HH:MM,TZ,LAT,LON[,Name]'")
    m.add_argument("--girl", required=True, help="profile name or 'YYYY-MM-DD,HH:MM,TZ,LAT,LON[,Name]'")
    m.add_argument("--system", default="both", choices=["north", "south", "both"],
                   help="north = Ashtakoota 36 gunas, south = Dashakoota 10 poruthams")
    m.set_defaults(fn=cmd_match, needs_birth=False)

    v = sub.add_parser("verify", help="check a report's planet/lagna/dasha numbers against the calculation")
    add_birth(v)
    v.add_argument("--report", required=True, help="JSON with planets/lagna/dasha (and optional birth fields)")
    v.set_defaults(fn=cmd_verify, needs_birth=False)

    u = sub.add_parser("muhurta", help="best days/windows for a purpose")
    add_birth(u)
    add_at(u)
    u.add_argument("--purpose", required=True, choices=list(PURPOSES))
    u.add_argument("--from", required=True)
    u.add_argument("--to", required=True)
    u.add_argument("--top", type=int, default=10)
    u.add_argument("--min-minutes", type=int, default=30, help="shortest window to report")
    u.add_argument("--include-night", action="store_true", help="search sunset to next sunrise too")
    u.set_defaults(fn=cmd_muhurta, needs_birth=False)
