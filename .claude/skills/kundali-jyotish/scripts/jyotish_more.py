"""More classical layers for jyotish.py.

chart sections 20-23 (extra yogas incl. 32 Nabhasa, full Shadbala + Bhava bala + Ishta/Kashta,
Ashtottari / Shodashottari / Jaimini Chara dasha, Ashtakavarga shodhana + pindas) and the commands
`tajik`, `prashna`, `event`, `charts`, `daily`, `log`, plus South Indian Dashakoota for `match`.
"""
import argparse
import importlib
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timedelta


def _J():
    m = sys.modules.get("__main__")
    return m if hasattr(m, "Natal") else importlib.import_module("jyotish")


def _X():
    return importlib.import_module("jyotish_ext")


SIGN_ELEMENT_ODD = lambda s: s % 2 == 0          # Aries=0 is an odd sign
MALE, NEUTER, FEMALE = {"Sun", "Mars", "Jupiter"}, {"Mercury", "Saturn"}, {"Moon", "Venus"}
REQUIRED_RUPAS = {"Sun": 6.5, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0, "Jupiter": 6.5,
                  "Venus": 5.5, "Saturn": 5.0}
BENEFIC7 = {"Jupiter", "Venus", "Mercury", "Moon"}


# --------------------------------------------------------------------------
# 20. Extra yogas: 32 Nabhasa + named yogas
# --------------------------------------------------------------------------

def extra_yogas(J, n, sex=None):
    S, L = n.signs, n.lagna
    H = {p: J.house_from(S[p], L) for p in J.PLANETS}
    seven = J.SEVEN
    occ_signs = {S[p] for p in seven}
    houses7 = {H[p] for p in seven}
    out = []
    mod = lambda s: s % 3  # 0 movable, 1 fixed, 2 dual
    # Ashraya
    for k, nm in ((0, "Rajju (all in movable signs)"), (1, "Musala (all in fixed signs)"),
                  (2, "Nala (all in dual signs)")):
        if all(mod(S[p]) == k for p in seven):
            out.append(("Nabhasa - " + nm, "Ashraya yoga"))
    ben = [p for p in ("Jupiter", "Venus", "Mercury") if True]
    mal = ["Sun", "Mars", "Saturn"]
    kend = {1, 4, 7, 10}
    if len({H[p] for p in ben} & kend) >= 3 and all(H[p] in kend for p in ben):
        out.append(("Nabhasa - Mala/Srak", "benefics occupy three kendras"))
    if len({H[p] for p in mal} & kend) >= 3 and all(H[p] in kend for p in mal):
        out.append(("Nabhasa - Sarpa", "malefics occupy three kendras"))
    akriti = {
        "Gada (two successive kendras)": [{1, 4}, {4, 7}, {7, 10}, {10, 1}],
        "Shakata (1 and 7 only)": [{1, 7}], "Vihaga (4 and 10 only)": [{4, 10}],
        "Shringataka (1, 5, 9)": [{1, 5, 9}],
        "Hala (other trine groups)": [{2, 6, 10}, {3, 7, 11}, {4, 8, 12}],
        "Kamala (all four kendras)": [{1, 4, 7, 10}],
        "Vapi (panaparas or apoklimas only)": [{2, 5, 8, 11}, {3, 6, 9, 12}],
    }
    for nm, sets in akriti.items():
        for st in sets:
            if houses7 <= st and (nm.startswith(("Kamala", "Vapi", "Hala", "Gada")) or houses7 == st):
                if nm.startswith("Kamala") and houses7 != st:
                    continue
                out.append(("Nabhasa - " + nm, f"planets in houses {sorted(houses7)}"))
                break
    for start, nm in ((1, "Yupa (1-4)"), (4, "Shara (4-7)"), (7, "Shakti (7-10)"), (10, "Danda (10-1)")):
        rng = {(start - 1 + i) % 12 + 1 for i in range(4)}
        if houses7 <= rng:
            out.append(("Nabhasa - " + nm, "all planets in four successive houses"))
    for start, nm in ((1, "Nauka"), (4, "Koota"), (7, "Chhatra"), (10, "Chapa")):
        rng = {(start - 1 + i) % 12 + 1 for i in range(7)}
        if houses7 == rng:
            out.append(("Nabhasa - " + nm, f"seven successive houses from H{start}"))
    for start in (2, 3, 5, 6, 8, 9, 11, 12):
        rng = {(start - 1 + i) % 12 + 1 for i in range(7)}
        if houses7 == rng:
            out.append(("Nabhasa - Ardhachandra", f"seven successive houses from H{start}"))
    if houses7 == {1, 3, 5, 7, 9, 11}:
        out.append(("Nabhasa - Chakra", "alternate houses from Lagna"))
    if houses7 == {2, 4, 6, 8, 10, 12}:
        out.append(("Nabhasa - Samudra", "alternate houses from the 2nd"))
    vajra_ok = all(H[p] in (1, 7) for p in ben) and all(H[p] in (4, 10) for p in mal)
    yava_ok = all(H[p] in (4, 10) for p in ben) and all(H[p] in (1, 7) for p in mal)
    if vajra_ok:
        out.append(("Nabhasa - Vajra", "benefics in 1/7, malefics in 4/10"))
    if yava_ok:
        out.append(("Nabhasa - Yava", "malefics in 1/7, benefics in 4/10"))
    sank = {7: "Vallaki/Veena", 6: "Damini", 5: "Pasha", 4: "Kedara", 3: "Shoola", 2: "Yuga", 1: "Gola"}
    out.append((f"Nabhasa (Sankhya) - {sank[len(occ_signs)]}",
                f"7 planets occupy {len(occ_signs)} signs (applies only if no other Nabhasa yoga)"))
    # Sun-based
    from_sun = lambda p: J.house_from(S[p], S["Sun"])
    v2 = [p for p in ("Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn") if p != "Moon" and from_sun(p) == 2]
    v12 = [p for p in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn") if from_sun(p) == 12]
    if v2 and v12:
        out.append(("Ubhayachari", f"2nd from Sun: {v2}; 12th from Sun: {v12}"))
    elif v2:
        out.append(("Vesi", f"{v2} in 2nd from Sun"))
    elif v12:
        out.append(("Vasi", f"{v12} in 12th from Sun"))
    # Kartari
    for ref, nm in ((L, "Lagna"), (S["Moon"], "Moon")):
        b2 = [p for p in seven if J.house_from(S[p], ref) == 2 and p != "Moon"]
        b12 = [p for p in seven if J.house_from(S[p], ref) == 12 and p != "Moon"]
        if b2 and b12:
            if all(p in BENEFIC7 for p in b2 + b12):
                out.append((f"Shubha Kartari ({nm})", f"benefics both sides: {b2 + b12}"))
            elif all(p in mal for p in b2 + b12):
                out.append((f"Papa Kartari ({nm})", f"malefics both sides: {b2 + b12}"))
    lord = lambda h: J.SIGN_LORD[(L + h - 1) % 12]
    dg = lambda p: J.dignity(p, n.lons[p], S)
    strong = lambda p: dg(p).startswith(("Exalted", "Own", "Moolatrikona"))
    # Named yogas
    if all(H[p] in kend for p in ("Jupiter", "Venus", "Mercury") if True) and not any(H[p] in (6, 8) for p in mal):
        out.append(("Parvata", "benefics in kendras, no malefic in 6/8"))
    l4, l9 = lord(4), lord(9)
    if J.house_from(S[l4], S[l9]) in (1, 4, 7, 10) and strong(lord(1)):
        out.append(("Kahala", "4th and 9th lords in mutual kendras, strong Lagna lord"))
    l1 = lord(1)
    if dg(l1).startswith("Exalted") and H[l1] in kend and (S[l1] == S["Jupiter"] or S[l1] in J.aspected_signs("Jupiter", S["Jupiter"])):
        out.append(("Chamara", "Lagna lord exalted in kendra with Jupiter's influence"))
    l9 = lord(9)
    if strong(l9) and H[l9] in (1, 4, 5, 7, 9, 10) and strong(l1):
        out.append(("Lakshmi", "strong 9th lord in kendra/trikona, strong Lagna lord"))
    if all(H[p] in (1, 2, 4, 5, 7, 9, 10) for p in ("Jupiter", "Venus", "Mercury")) and not J.dignity("Jupiter", n.lons["Jupiter"], S).startswith("Debil"):
        out.append(("Saraswati", "Jupiter, Venus, Mercury in kendra/trikona/2nd"))
    l10 = lord(10)
    if l9 != l10 and (S[l9] == S[l10] or (S[l9] in J.OWN.get(l10, []) and S[l10] in J.OWN.get(l9, []))
                      or (S[l9] in J.aspected_signs(l10, S[l10]) and S[l10] in J.aspected_signs(l9, S[l9]))):
        out.append(("Dharma-Karmadhipati", f"9th lord {l9} and 10th lord {l10} associated"))
    if J.house_from(S["Moon"], S["Jupiter"]) in (6, 8, 12):
        out.append(("Shakata", "Moon in 6/8/12 from Jupiter (cancelled if Moon in kendra from Lagna)"
                    + (" - cancelled" if H["Moon"] in kend else "")))
    if H[lord(11)] in (6, 8, 12):
        out.append(("Daridra (11th lord in dusthana)", f"{lord(11)} in H{H[lord(11)]}"))
    l5, l6 = lord(5), lord(6)
    if J.house_from(S[l5], S[l6]) in (1, 4, 7, 10) and strong(l1):
        out.append(("Shankha", "5th and 6th lords in mutual kendras, strong Lagna lord"))
    if sex:
        sun_odd, moon_odd, lag_odd = SIGN_ELEMENT_ODD(S["Sun"]), SIGN_ELEMENT_ODD(S["Moon"]), SIGN_ELEMENT_ODD(L)
        day = n.lons is not None and getattr(n, "_day_birth", None)
        if sex == "male" and sun_odd and moon_odd and lag_odd:
            out.append(("Mahabhagya (male, check day birth)", "Lagna, Sun, Moon in odd signs"))
        if sex == "female" and not sun_odd and not moon_odd and not lag_odd:
            out.append(("Mahabhagya (female, check night birth)", "Lagna, Sun, Moon in even signs"))
    return out


# --------------------------------------------------------------------------
# 21. Full Shadbala, Ishta/Kashta, Bhava bala
# --------------------------------------------------------------------------

def _decl(J, n, p):
    trop = (n.lons[p] + n.eph.ayanamsa_value(n.jd)) % 360
    eps = 23.44
    return math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(trop))))


def shadbala(J, n):
    e = n.eph
    wd, sr = J.vedic_day(e, n.local, n.tz, n.lat, n.lon)
    ss = e.sun_event(sr, n.lat, n.lon, False)
    sr2 = e.sun_event(ss, n.lat, n.lon, True)
    day_birth = sr <= n.jd < ss
    base = J.strength_components(n)
    midday = (sr + ss) / 2
    d_mid = abs(((n.jd - (midday + 0.5)) + 0.5) % 1 - 0.5) * 24   # hours from midnight (0..12)
    if day_birth:
        third = int(min(2, (n.jd - sr) / ((ss - sr) / 3)))
        tri_lord = ["Mercury", "Sun", "Saturn"][third]
    else:
        third = int(min(2, (n.jd - ss) / ((sr2 - ss) / 3)))
        tri_lord = ["Moon", "Venus", "Mars"][third]
    hora_idx = int((n.jd - sr) / ((ss - sr) / 12)) if day_birth else 12 + int((n.jd - ss) / ((sr2 - ss) / 12))
    hora_lord = J.HORA_ORDER[(J.HORA_ORDER.index(J.WEEKDAY_LORD[wd]) + hora_idx) % 7]
    ahar = int(n.jd - 588465.5)
    fri = 4  # Kali epoch weekday = Friday (Mon=0)
    abda_lord = J.WEEKDAY_LORD[(fri + (ahar // 360) * 360) % 7]
    masa_lord = J.WEEKDAY_LORD[(fri + (ahar // 30) * 30) % 7]
    elong = J.ang_dist(n.lons["Moon"], n.lons["Sun"])
    rows = {}
    for p in J.SEVEN:
        lon = n.lons[p]
        s = J.sign_of(lon)
        nav = J.varga_sign(lon, 9)
        even_pref = p in FEMALE
        oja = (15 if (s % 2 == 1) == even_pref else 0) + (15 if (nav % 2 == 1) == even_pref else 0)
        h = J.house_from(s, n.lagna)
        kendradi = 60 if h in (1, 4, 7, 10) else 30 if h in (2, 5, 8, 11) else 15
        dk = int(J.deg_in_sign(lon) // 10)
        drek = 15 if ((p in MALE and dk == 0) or (p in NEUTER and dk == 1) or (p in FEMALE and dk == 2)) else 0
        sthana = base[p]["uchcha"] + base[p]["saptavargaja"] + oja + kendradi + drek
        if p == "Mercury":
            nato = 60.0
        elif p in ("Sun", "Jupiter", "Venus"):
            nato = 60 * d_mid / 12
        else:
            nato = 60 * (12 - d_mid) / 12
        paksha = base[p]["paksha"] * (2 if p == "Moon" else 1)
        tri = 60 if (p == tri_lord or p == "Jupiter") else 0
        vara = 45 if p == J.WEEKDAY_LORD[wd] else 0
        hora = 60 if p == hora_lord else 0
        masa = 30 if p == masa_lord else 0
        abda = 15 if p == abda_lord else 0
        dec = _decl(J, n, p)
        if p in ("Moon", "Saturn"):
            ay = (24 - dec) * 60 / 48
        elif p == "Mercury":
            ay = (24 + abs(dec)) * 60 / 48
        else:
            ay = (24 + dec) * 60 / 48
        if p == "Sun":
            ay *= 2
        kala = nato + paksha + tri + vara + hora + masa + abda + ay
        chesta = ay if p == "Sun" else paksha if p == "Moon" else base[p]["chesta"]
        dig = base[p]["dig"]
        nais = base[p]["naisargika"]
        drik = base[p]["drik"]
        total = sthana + dig + kala + chesta + nais + drik
        rup = total / 60
        u = base[p]["uchcha"]
        ch = min(max(chesta, 0), 60)
        rows[p] = dict(sthana=sthana, dig=dig, kala=kala, chesta=chesta, nais=nais, drik=drik,
                       total=total, rupas=rup, ratio=rup / REQUIRED_RUPAS[p],
                       ishta=math.sqrt(max(u * ch, 0)), kashta=math.sqrt(max((60 - u) * (60 - ch), 0)))
    meta = dict(day_birth=day_birth, tri_lord=tri_lord, hora_lord=hora_lord, vara_lord=J.WEEKDAY_LORD[wd],
                masa_lord=masa_lord, abda_lord=abda_lord)
    return rows, meta


def bhava_bala(J, n, sb):
    madhya, _ = J.sripati_bhavas(n.asc_lon, n.mc_lon)
    strongest = {"nara": 1, "jala": 4, "keeta": 7, "chatush": 10}
    def stype(lon):
        s, d = J.sign_of(lon), J.deg_in_sign(lon)
        if s in (2, 5, 6, 10) or (s == 8 and d < 15):
            return "nara"
        if s in (3, 11) or (s == 9 and d >= 15):
            return "jala"
        if s == 7:
            return "keeta"
        return "chatush"
    rows = []
    for h in range(1, 13):
        lon = madhya[h]
        lord = J.SIGN_LORD[J.sign_of(lon)]
        lordb = sb[lord]["total"]
        dist = min((h - strongest[stype(lon)]) % 12, (strongest[stype(lon)] - h) % 12)
        dig = max(0, 60 - dist * 10)
        dr = 0.0
        for p in J.SEVEN:
            v = J.drishti_virupa(p, (lon - n.lons[p]) % 360)
            dr += v if p in BENEFIC7 else -v
        tot = lordb + dig + dr / 4
        rows.append((h, lord, lordb, dig, dr / 4, tot))
    return rows


# --------------------------------------------------------------------------
# 22. Ashtottari, Shodashottari, Jaimini Chara dasha
# --------------------------------------------------------------------------

ASHT = [("Sun", 6, [5, 6, 7, 8]), ("Moon", 15, [9, 10, 11]), ("Mars", 8, [12, 13, 14, 15]),
        ("Mercury", 17, [16, 17, 18]), ("Saturn", 10, [19, 20, 21]), ("Jupiter", 19, [22, 23, 24]),
        ("Rahu", 12, [25, 26, 0, 1]), ("Venus", 21, [2, 3, 4])]
SHOD = [("Sun", 11), ("Mars", 12), ("Jupiter", 13), ("Saturn", 14), ("Ketu", 15), ("Moon", 16),
        ("Mercury", 17), ("Venus", 18)]


def ashtottari(J, n, yd):
    moon = n.lons["Moon"]
    nk = J.nakshatra_info(moon)["index"]
    gi = next(i for i, g in enumerate(ASHT) if nk in g[2])
    naks = ASHT[gi][2]
    start = naks[0] * J.NAK_SPAN
    span = len(naks) * J.NAK_SPAN
    frac = ((moon - start) % 360) / span
    t = n.jd - frac * ASHT[gi][1] * yd
    mds = []
    for k in range(9):
        lord, yrs, _ = ASHT[(gi + k) % 8]
        mds.append((lord, t, t + yrs * yd))
        t += yrs * yd
    return mds, (1 - frac) * ASHT[gi][1]


def shodashottari(J, n, yd):
    nk = J.nakshatra_info(n.lons["Moon"])
    i0 = ((nk["index"] - 7) % 27) % 8
    frac = nk["fraction_elapsed"]
    t = n.jd - frac * SHOD[i0][1] * yd
    mds = []
    for k in range(9):
        lord, yrs = SHOD[(i0 + k) % 8]
        mds.append((lord, t, t + yrs * yd))
        t += yrs * yd
    return mds, (1 - frac) * SHOD[i0][1]


SAVYA = {0, 1, 2, 6, 7, 8}   # Aries Taurus Gemini Libra Scorpio Sagittarius


def _chara_lord(J, n, s):
    S = n.signs
    if s == 7:
        cands = ["Mars", "Ketu"]
    elif s == 10:
        cands = ["Saturn", "Rahu"]
    else:
        return J.SIGN_LORD[s]
    a, b = cands
    if S[a] == s and S[b] != s:
        return b
    if S[b] == s and S[a] != s:
        return a
    cnt = lambda p: sum(1 for q in J.PLANETS if q != p and S[q] == S[p])
    if cnt(a) != cnt(b):
        return a if cnt(a) > cnt(b) else b
    return a if J.deg_in_sign(n.lons[a]) >= J.deg_in_sign(n.lons[b]) else b


def chara_dasha(J, n, yd):
    S = n.signs
    direct = ((n.lagna + 8) % 12) in SAVYA
    seq = [(n.lagna + (k if direct else -k)) % 12 for k in range(12)]
    first = []
    for s in seq:
        lord = _chara_lord(J, n, s)
        ls = S[lord]
        cnt = (ls - s) % 12 if s in SAVYA else (s - ls) % 12
        yrs = 12 if cnt == 0 else cnt
        dgl = J.dignity(lord, n.lons[lord], S) if lord in J.SEVEN else ""
        if dgl.startswith("Exalted"):
            yrs += 1
        elif dgl.startswith("Debilitated"):
            yrs -= 1
        first.append((s, lord, max(yrs, 1)))
    out, t = [], n.jd
    for cyc in (1, 2):
        for s, lord, yrs in first:
            y = yrs if cyc == 1 else 12 - yrs
            if y <= 0:
                continue
            out.append((s, lord, t, t + y * yd, cyc))
            t += y * yd
    return out, direct


# --------------------------------------------------------------------------
# 23. Ashtakavarga shodhana and pindas
# --------------------------------------------------------------------------

RASHI_MULT = [7, 10, 8, 4, 10, 5, 7, 8, 9, 5, 11, 12]
GRAHA_MULT = {"Sun": 5, "Moon": 5, "Mars": 8, "Mercury": 5, "Jupiter": 10, "Venus": 7, "Saturn": 5}
PAIRS = {"Mars": (0, 7), "Venus": (1, 6), "Mercury": (2, 5), "Jupiter": (8, 11), "Saturn": (9, 10)}


def shodhana(J, n, bav):
    occupied = {n.signs[p] for p in J.SEVEN}
    res = {}
    for p in J.SEVEN:
        b = list(bav[p])
        for g in range(4):
            idx = [g, g + 4, g + 8]
            vals = [b[i] for i in idx]
            if len(set(vals)) == 1:
                for i in idx:
                    b[i] = 0
            else:
                m = min(vals)
                for i in idx:
                    b[i] -= m
        for _, (x, y) in PAIRS.items():
            ox, oy = x in occupied, y in occupied
            if ox and oy:
                continue
            if not ox and not oy:
                if b[x] == b[y]:
                    b[x] = b[y] = 0
                else:
                    b[x] = b[y] = min(b[x], b[y])
            else:
                o, u = (x, y) if ox else (y, x)
                if b[u] <= b[o]:
                    b[u] = 0
                else:
                    b[u] -= b[o]
        rashi = sum(b[s] * RASHI_MULT[s] for s in range(12))
        graha = sum(b[n.signs[q]] * GRAHA_MULT[q] for q in J.SEVEN)
        res[p] = (b, rashi, graha, rashi + graha)
    return res


# --------------------------------------------------------------------------
# chart sections
# --------------------------------------------------------------------------

def chart_sections(n, args, asof_jd):
    J = _J()
    out = []
    sex = getattr(args, "sex", None)
    out.append("\n## 20. More yogas (Nabhasa, Sun-based, Kartari, named)\n")
    ys = extra_yogas(J, n, sex)
    out.append(J.table(["Yoga", "Formation / note"], ys) if ys else "None.")
    out.append("Nabhasa yogas give lifelong patterns; Sankhya applies only when no other Nabhasa forms. "
               "Grade named yogas by the strength of the planets involved (section 21).")

    sb, meta = shadbala(J, n)
    out.append("\n## 21. Shadbala (six-fold strength), Ishta/Kashta, Bhava bala\n")
    rows = [[p, f"{r['sthana']:.0f}", f"{r['dig']:.0f}", f"{r['kala']:.0f}", f"{r['chesta']:.0f}",
             f"{r['nais']:.0f}", f"{r['drik']:+.0f}", f"{r['rupas']:.2f}", f"{REQUIRED_RUPAS[p]}",
             f"{r['ratio']:.2f}" + (" strong" if r['ratio'] >= 1 else " weak"),
             f"{r['ishta']:.0f}", f"{r['kashta']:.0f}"] for p, r in sb.items()]
    out.append(J.table(["Planet", "Sthana", "Dig", "Kala", "Chesta", "Naisargika", "Drik", "Total rupas",
                        "Required", "Ratio", "Ishta", "Kashta"], rows))
    out.append(f"\nKala bala used: {'day' if meta['day_birth'] else 'night'} birth; Tribhaga lord "
               f"{meta['tri_lord']}, Vara {meta['vara_lord']}, Hora {meta['hora_lord']}, Masa {meta['masa_lord']}, "
               f"Abda {meta['abda_lord']} (ahargana method; implementations differ). Ayana uses declination "
               "without ecliptic latitude; Chesta of Mars-Saturn is motion-class based. Ratio >= 1 = adequate "
               "strength. Ishta > Kashta: the planet's dasha gives more good than bad.")
    bb = bhava_bala(J, n, sb)
    rank = sorted(bb, key=lambda r: -r[5])
    out.append("\n" + J.table(["Bhava", "Lord", "Lord's shadbala", "Bhava dig", "Aspects", "Bhava bala (virupas)"],
                              [[h, lo, f"{a:.0f}", f"{d:.0f}", f"{dr:+.0f}", f"{t:.0f}"] for h, lo, a, d, dr, t in bb]))
    out.append("\nStrongest houses: " + ", ".join(f"H{r[0]}" for r in rank[:3]) +
               "; weakest: " + ", ".join(f"H{r[0]}" for r in rank[-3:]) + ".")

    yd = args.dasha_year
    out.append("\n## 22. Other dashas\n")
    sun, moon = n.lons["Sun"], n.lons["Moon"]
    elong = (moon - sun) % 360
    shukla = elong < 180
    wd, sr = J.vedic_day(n.eph, n.local, n.tz, n.lat, n.lon)
    ss = n.eph.sun_event(sr, n.lat, n.lon, False)
    day = sr <= n.jd < ss
    l1 = J.SIGN_LORD[n.lagna]
    rahu_kt = J.house_from(n.signs["Rahu"], n.signs[l1]) in (1, 4, 5, 7, 9, 10) and n.signs["Rahu"] != n.lagna
    paksha_ok = (day and not shukla) or (not day and shukla)
    hora_sign = J.varga_sign(n.asc_lon, 2)
    shod_ok = (hora_sign == 3 and not shukla) or (hora_sign == 4 and shukla)
    for title, (mds, bal), ok in (
            (f"Ashtottari (108 y) - applicability: Rahu in kendra/trikona from Lagna lord: {rahu_kt}; "
             f"{'day' if day else 'night'} birth in {'Shukla' if shukla else 'Krishna'} paksha: "
             f"{'fits' if paksha_ok else 'does not fit'}", ashtottari(J, n, yd), rahu_kt and paksha_ok),
            (f"Shodashottari (116 y) - applicability: Lagna in {'Moon' if hora_sign == 3 else 'Sun'}'s hora, "
             f"{'Shukla' if shukla else 'Krishna'} paksha", shodashottari(J, n, yd), shod_ok)):
        out.append(f"**{title} -> {'APPLIES' if ok else 'not indicated (use as secondary)'}**; "
                   f"balance at birth {mds[0][0]} {bal:.2f} y\n")
        rr = [[L_, J.fmt_local(n.local_of(max(a, n.jd)))[:10], J.fmt_local(n.local_of(b))[:10]
               + (" **<- running**" if a <= asof_jd < b else "")]
              for L_, a, b in mds if b > n.jd and a < n.jd + 110 * 365.25]
        out.append(J.table(["Dasha", "From", "To"], rr) + "\n")
    cd, direct = chara_dasha(J, n, yd)
    out.append(f"**Jaimini Chara dasha (K. N. Rao method: {'zodiacal' if direct else 'reverse'} order from Lagna, "
               "decided by the 9th sign; years = count to sign lord - 1, +1 exalted / -1 debilitated lord, "
               "12 if lord in the sign; second cycle = 12 - first)**\n")
    rr = [[f"{J.SIGNS[s]} (H{J.house_from(s, n.lagna)})", lord, f"cycle {c}",
           J.fmt_local(n.local_of(a))[:10], J.fmt_local(n.local_of(b))[:10] + (" **<- running**" if a <= asof_jd < b else "")]
          for s, lord, a, b, c in cd if a < n.jd + 100 * 365.25]
    out.append(J.table(["Chara MD sign", "Lord used", "Cycle", "From", "To"], rr))
    out.append("Read a Chara dasha sign as a temporary Lagna: planets and karakas in it and in its "
               "trines/7th, and its relation to the Arudha Lagna, the 10th (career) and Upapada (marriage).")

    bav, sav, contrib = J.ashtakavarga(n.signs)
    sh = shodhana(J, n, bav)
    out.append("\n## 23. Ashtakavarga shodhana and pindas\n")
    rows = [[p] + sh[p][0] + [sh[p][1], sh[p][2], sh[p][3]] for p in J.SEVEN]
    out.append(J.table(["Reduced BAV"] + [s[:3] for s in J.SIGNS] + ["Rashi pinda", "Graha pinda", "Shodhya pinda"], rows))
    out.append("\nAfter Trikona and Ekadhipatya shodhana (rule used for one occupied sign: the vacant sign "
               "loses its bindus if it has fewer or equal, else it is reduced by the occupied sign's count). "
               "Reduced bindus show where a transiting planet really delivers; a higher Shodhya pinda = a "
               "stronger planet for results in its periods.")
    return out


# --------------------------------------------------------------------------
# Tajik Varshphal (full)
# --------------------------------------------------------------------------

TRIRASHI = {0: ("Sun", "Jupiter"), 1: ("Venus", "Moon"), 2: ("Saturn", "Mercury"), 3: ("Venus", "Mars"),
            4: ("Jupiter", "Sun"), 5: ("Moon", "Venus"), 6: ("Mercury", "Saturn"), 7: ("Mars", "Venus"),
            8: ("Saturn", "Saturn"), 9: ("Mars", "Mars"), 10: ("Jupiter", "Jupiter"), 11: ("Moon", "Moon")}
DEEPTAMSHA = {"Sun": 15, "Moon": 12, "Mars": 8, "Mercury": 7, "Jupiter": 9, "Venus": 7, "Saturn": 9}
SPEED_RANK = ["Moon", "Mercury", "Venus", "Sun", "Mars", "Jupiter", "Saturn"]
MUDDA_ORDER = ["Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu", "Venus"]


def _tajik_aspect(a, b):
    d = (b - a) % 12 + 1
    return "friendly" if d in (3, 5, 9, 11) else "inimical" if d in (1, 4, 7, 10) else None


def _dig_score(J, p, lon, signs):
    dg = J.dignity(p, lon, signs)
    for k, v in (("Exalted", 5), ("Moolatrikona", 4), ("Own", 4), ("Great friend", 3), ("Friend", 2),
                 ("Neutral", 1), ("Enemy", 0), ("Great enemy", -1), ("Debilitated", -2)):
        if dg.startswith(k):
            return v, dg
    return 0, dg


def cmd_tajik(args):
    J = _J()
    n = J.Natal(args)
    e = n.eph
    year = args.year
    sun0 = n.lons["Sun"]
    try:
        g = n.local.replace(year=year)
    except ValueError:
        g = n.local.replace(year=year, day=28)
    j = J.jd_from_utc(n.tz.to_utc(g))
    for _ in range(30):
        lon, sp = e.lon_speed(j, "Sun")
        diff = ((sun0 - lon + 180) % 360) - 180
        if abs(diff) < 1e-7:
            break
        j += diff / sp
    lat = args.at_lat if args.at_lat is not None else n.lat
    lon_ = args.at_lon if args.at_lon is not None else n.lon
    tz = J.TZ(args.at_tz) if args.at_tz else n.tz
    asc = e.asc(j, lat, lon_)
    vl = J.sign_of(asc)
    pl = e.planets(j)
    vs = {p: J.sign_of(pl[p]["lon"]) for p in J.PLANETS}
    age = year - n.local.year
    muntha = (n.lagna + age) % 12
    sr = e.sun_event(j - 1, lat, lon_, True)
    while sr is not None and sr + 1 < j:
        sr = e.sun_event(sr + 0.5, lat, lon_, True)
    ss = e.sun_event(sr, lat, lon_, False) if sr else None
    day = sr is not None and ss is not None and sr <= j < ss
    bearers = {"Natal Lagna lord": J.SIGN_LORD[n.lagna], "Varsha Lagna lord": J.SIGN_LORD[vl],
               "Muntha lord": J.SIGN_LORD[muntha], "Tri-rashi pati": TRIRASHI[vl][0 if day else 1],
               "Dina-ratri pati": J.SIGN_LORD[vs["Sun"] if day else vs["Moon"]]}
    rows, cands = [], []
    for role, p in bearers.items():
        asp = _tajik_aspect(vs[p], vl)
        sc, dg = _dig_score(J, p, pl[p]["lon"], vs)
        hh = J.house_from(vs[p], vl)
        sc += 1 if hh in (1, 4, 7, 10) else 0
        rows.append([role, p, f"H{hh}", dg.split(" in ")[0], asp or "no aspect", sc])
        if asp:
            cands.append((sc, p))
    yl = max(cands)[1] if cands else max((r[5], r[1]) for r in rows)[1]
    out = [f"# Tajik Varshphal {year}-{year + 1} (age {age} completed)", "",
           J.table(["Item", "Value"], [
               ["Varsha pravesh", f"{J.fmt_local(tz.from_utc(J.utc_from_jd(j)))} ({'day' if day else 'night'})"],
               ["Varsha lagna", f"{J.fmt_lon(asc)}"],
               ["Muntha", f"{J.SIGNS[muntha]} = H{J.house_from(muntha, vl)} of varsha chart, lord {J.SIGN_LORD[muntha]}"],
               ["Year lord (Varsheshwar)", f"**{yl}**"]]), "",
           "**Office-bearers (Panchadhikari)** - year lord = strongest bearer aspecting the Varsha lagna "
           "(strength here: sign dignity + kendra; a simplified Pancha-vargiya bala)\n",
           J.table(["Role", "Planet", "House", "Dignity", "Tajik aspect to lagna", "Score"], rows), ""]
    vrows = [[p, J.fmt_lon(pl[p]["lon"]) + (" R" if pl[p]["speed"] < 0 and p not in ("Rahu", "Ketu") else ""),
              J.house_from(vs[p], vl)] for p in J.PLANETS]
    out.append(J.table(["Planet", "Varsha position", "Varsha house"], vrows))
    a = asc
    P = {p: pl[p]["lon"] for p in J.PLANETS}

    def saham(x, y):
        v = (x - y + a) % 360
        if not ((a - y) % 360 <= (x - y) % 360):
            v = (v + 30) % 360
        return v
    sahams = {"Punya (fortune)": saham(P["Moon"], P["Sun"]) if day else saham(P["Sun"], P["Moon"]),
              "Vidya (learning)": saham(P["Sun"], P["Moon"]) if day else saham(P["Moon"], P["Sun"]),
              "Vivaha (marriage)": saham(P["Venus"], P["Saturn"]),
              "Putra (children)": saham(P["Jupiter"], P["Moon"])}
    out.append("\n**Sahams** (A - B + Asc, +30° when the Asc is not between B and A)\n")
    out.append(J.table(["Saham", "Position", "Varsha house", "Lord"],
                       [[k, J.fmt_lon(v), J.house_from(J.sign_of(v), vl), J.SIGN_LORD[J.sign_of(v)]] for k, v in sahams.items()]))
    yog = []
    seven = J.SEVEN
    for i, p in enumerate(seven):
        for q in seven[i + 1:]:
            asp = _tajik_aspect(vs[p], vs[q])
            if not asp:
                continue
            orb = (DEEPTAMSHA[p] + DEEPTAMSHA[q]) / 2
            dp, dq = J.deg_in_sign(P[p]), J.deg_in_sign(P[q])
            if abs(dp - dq) > orb:
                continue
            fast, slow = (p, q) if SPEED_RANK.index(p) < SPEED_RANK.index(q) else (q, p)
            df, ds = J.deg_in_sign(P[fast]), J.deg_in_sign(P[slow])
            kind = "Ithasala (applying - promise fulfilled)" if df < ds else "Ishrafa (separating - matter passing)"
            yog.append([f"{fast} - {slow}", asp, f"{abs(df - ds):.1f}° (orb {orb:.1f})", kind])
    out.append("\n**Tajik yogas**\n")
    out.append(J.table(["Pair (faster - slower)", "Aspect", "Gap", "Yoga"], yog) if yog else "None within orb.")
    nk = J.nakshatra_info(n.lons["Moon"])["index"] + 1
    r = (nk + age - 2) % 9
    i0 = (r - 1) % 9
    t = j
    rows = []
    for k in range(9):
        lord = MUDDA_ORDER[(i0 + k) % 9]
        d = J.DASHA_YEARS[lord] * 365.2425 / 120
        rows.append([lord, J.fmt_local(tz.from_utc(J.utc_from_jd(t)))[:10],
                     J.fmt_local(tz.from_utc(J.utc_from_jd(t + d)))[:10]])
        t += d
    out.append("\n**Mudda dasha** (Vimshottari compressed into the year; start = (janma nakshatra + age - 2) mod 9)\n")
    out.append(J.table(["Lord", "From", "To"], rows))
    rows = []
    for m in range(1, 12):
        target = (sun0 + 30 * m) % 360
        jj = j + 30.4 * m
        for _ in range(30):
            lo, sp = e.lon_speed(jj, "Sun")
            dd = ((target - lo + 180) % 360) - 180
            if abs(dd) < 1e-7:
                break
            jj += dd / sp
        ml = J.sign_of(e.asc(jj, lat, lon_))
        rows.append([m + 1, J.fmt_local(tz.from_utc(J.utc_from_jd(jj))), J.SIGNS[ml],
                     J.SIGNS[(muntha + 0) % 12] if m == 0 else "-"])
    out.append("\n**Masa pravesh (monthly charts)**\n")
    out.append(J.table(["Month", "Starts", "Masa lagna", ""], [r[:3] + [""] for r in rows]))
    out.append("\nMuntha in 9/10/11 best, 1/2/3 good, 5 mixed, 4/6/7/8/12 caution. Judge the year by the year "
               "lord's strength, Muntha, Ithasala yogas involving the houses asked about, and the Mudda dasha.")
    print("\n".join(out))


# --------------------------------------------------------------------------
# KP Prashna (1-249)
# --------------------------------------------------------------------------

def kp_249(J):
    out = []
    for nk in range(27):
        start = nk * J.NAK_SPAN
        lord = J.DASHA_ORDER[nk % 9]
        i0 = J.DASHA_ORDER.index(lord)
        t = start
        for k in range(9):
            sub = J.DASHA_ORDER[(i0 + k) % 9]
            span = J.NAK_SPAN * J.DASHA_YEARS[sub] / 120
            a, b = t, t + span
            boundary = (math.floor(a / 30 + 1e-9) + 1) * 30
            if a < boundary < b - 1e-9:
                out.append((a, boundary, lord, sub))
                out.append((boundary, b, lord, sub))
            else:
                out.append((a, b, lord, sub))
            t = b
    return out


KP_Q = {"marriage": (7, [2, 7, 11], [1, 6, 10]), "job": (10, [2, 6, 10, 11], [1, 5, 9, 12]),
        "money": (2, [2, 6, 11], [5, 8, 12]), "property": (4, [4, 11, 12], [3, 5, 8]),
        "travel": (12, [3, 9, 12], [4, 8, 11]), "child": (5, [2, 5, 11], [1, 4, 10]),
        "health": (1, [1, 5, 11], [6, 8, 12]), "litigation": (6, [6, 11], [5, 8, 12]),
        "education": (4, [4, 9, 11], [3, 8, 12]), "business": (7, [7, 10, 11], [5, 8, 12])}


def cmd_prashna(args):
    J = _J()
    tab = kp_249(J)
    if not 1 <= args.number <= len(tab):
        raise SystemExit(f"Number must be 1-{len(tab)}")
    a, b, star, sub = tab[args.number - 1]
    ns = argparse.Namespace(ayanamsa="kp", node="true", hindu_sunrise=False, engine=args.engine)
    e = J.make_ephem(ns)
    tz = J.TZ(args.at_tz)
    when = J.parse_moment(args.when) if args.when else tz.from_utc(datetime.utcnow())
    jq = J.jd_from_utc(tz.to_utc(when))
    f = lambda jj: ((e.asc(jj, args.at_lat, args.at_lon) - a + 180) % 360) - 180
    best = None
    t, fa = jq - 0.5, f(jq - 0.5)
    while t < jq + 0.5:
        t2 = t + 1 / 288
        fb = f(t2)
        if fa < 0 <= fb and abs(fa) < 20:
            x, y = t, t2
            for _ in range(40):
                m = (x + y) / 2
                if f(m) < 0:
                    x = m
                else:
                    y = m
            if best is None or abs(y - jq) < abs(best - jq):
                best = y
        t, fa = t2, fb
    asc, mc, cusps, sysname = e.asc_mc(best, args.at_lat, args.at_lon)
    pl = e.planets(jq)
    lons = {p: pl[p]["lon"] for p in J.PLANETS}

    def bhava(lon):
        for i in range(12):
            x, y = cusps[i], cusps[(i + 1) % 12]
            if (lon - x) % 360 < (y - x) % 360:
                return i + 1
        return 12
    pb = {p: bhava(lons[p]) for p in J.PLANETS}
    owner = {h: J.SIGN_LORD[J.sign_of(cusps[h - 1])] for h in range(1, 13)}
    owned_by = {p: [h for h in range(1, 13) if owner[h] == p] for p in J.PLANETS}

    def signified(p):
        st = J.nakshatra_info(lons[p])["lord"]
        hs = {pb[st]} | set(owned_by.get(st, [])) | {pb[p]} | set(owned_by.get(p, []))
        if p in ("Rahu", "Ketu"):
            hs |= set(owned_by.get(J.SIGN_LORD[J.sign_of(lons[p])], []))
        return sorted(hs)
    qh, good, bad = KP_Q[args.question]
    csl = J.nakshatra_info(cusps[qh - 1])["sub"]
    sig = signified(csl)
    g, bd = [h for h in sig if h in good], [h for h in sig if h in bad]
    verdict = "YES - promised" if len(g) >= 2 and len(g) >= len(bd) else ("DOUBTFUL" if g else "NO - not promised")
    wd = when.weekday()
    ml = lons["Moon"]
    lag_now = e.asc(jq, args.at_lat, args.at_lon)
    rp = [("Day lord", J.WEEKDAY_LORD[wd]), ("Lagna sign lord", J.SIGN_LORD[J.sign_of(lag_now)]),
          ("Lagna star lord", J.nakshatra_info(lag_now)["lord"]), ("Lagna sub lord", J.nakshatra_info(lag_now)["sub"]),
          ("Moon sign lord", J.SIGN_LORD[J.sign_of(ml)]), ("Moon star lord", J.nakshatra_info(ml)["lord"]),
          ("Moon sub lord", J.nakshatra_info(ml)["sub"])]
    out = [f"# KP Prashna - number {args.number} ({args.question}), {when:%Y-%m-%d %H:%M}", "",
           f"Horary ascendant {J.fmt_lon(a)} (star {star}, sub {sub}); cusps cast for the moment that degree "
           f"rises at the place ({J.fmt_local(tz.from_utc(J.utc_from_jd(best)))}), {sysname}; KP ayanamsa, true node.", "",
           J.table(["Cusp", "Longitude", "Sign lord", "Star lord", "Sub lord"],
                   [[i + 1, J.fmt_lon(c), J.SIGN_LORD[J.sign_of(c)], J.nakshatra_info(c)["lord"],
                     J.nakshatra_info(c)["sub"]] for i, c in enumerate(cusps)]), "",
           J.table(["Planet", "Position", "Star", "Sub", "Bhava", "Signifies houses"],
                   [[p, J.fmt_lon(lons[p]), J.nakshatra_info(lons[p])["lord"], J.nakshatra_info(lons[p])["sub"],
                     pb[p], ", ".join(map(str, signified(p)))] for p in J.PLANETS]), "",
           f"**Judgement:** cusp {qh} sub lord **{csl}** signifies {sig}. Favourable houses for "
           f"{args.question} {good} -> {g}; denial houses {bad} -> {bd}. **{verdict}.**", "",
           "**Ruling planets at the time of the question**\n",
           J.table(["Factor", "Planet"], rp),
           "\nTiming: the event comes in the dasha/bhukti/antara of significators of the favourable houses "
           "that are also ruling planets; transits of the Moon/Sun over their stars fix the day/month."]
    print("\n".join(out))


# --------------------------------------------------------------------------
# Event finder (multi-dasha agreement)
# --------------------------------------------------------------------------

def cmd_event(args):
    J, X = _J(), _X()
    n = J.Natal(args)
    e = n.eph
    houses, karakas, varga = X.EVENT_RULES[args.type]
    yg = J.Yogini(n.lons["Moon"], n.jd, args.dasha_year)
    cd, _ = chara_dasha(J, n, args.dasha_year)
    d0, d1 = J.parse_date(getattr(args, "from")), J.parse_date(args.to)
    rows = []
    cur = d0.replace(day=1)
    targets = {(n.lagna + h - 1) % 12 for h in houses[:2]}
    lord_signs = {n.signs[J.SIGN_LORD[t]] for t in targets}
    while cur <= d1:
        jd = J.jd_from_utc(n.tz.to_utc(cur.replace(day=15, hour=12)))
        path = n.dasha.path(jd, 3)
        vim = sum(w * X._signifies(J, n, p[0], houses, karakas) for p, w in zip(path, (3, 2, 1)))
        vim_ok = vim >= 9
        yl = None
        for idx, a, b in yg.mds:
            if a <= jd < b:
                for j2, x, y in J.Yogini.sub(idx, a, b):
                    if x <= jd < y:
                        yl = (J.YOGINI[idx][1], J.YOGINI[j2][1])
        ys = sum(X._signifies(J, n, p, houses, karakas) for p in yl) if yl else 0
        yog_ok = ys >= 2
        cs = next((c for c in cd if c[2] <= jd < c[3]), None)
        ch_ok = False
        if cs:
            s = cs[0]
            rel = {(s + k) % 12 for k in (0, 4, 6, 8)}
            ch_ok = bool(rel & (targets | lord_signs)) or any(n.signs[k] in rel for k in karakas if k in n.signs)
        tr = 0
        for tp in ("Jupiter", "Saturn"):
            ts = J.sign_of(e.lon(jd, tp))
            if (targets | lord_signs) & ({ts} | set(J.aspected_signs(tp, ts))):
                tr += 1
        layers = int(vim_ok) + int(yog_ok) + int(ch_ok) + (1 if tr == 2 else 0)
        score = vim + 2 * ys + (3 if ch_ok else 0) + 2 * tr
        rows.append((cur, score, layers, path, yl, cs, tr, vim_ok, yog_ok, ch_ok))
        m = cur.month + 1
        cur = cur.replace(year=cur.year + (m > 12), month=(m - 1) % 12 + 1)
    best = sorted(rows, key=lambda r: (-r[2], -r[1]))[:args.top]
    lab = lambda l: "Pakka" if l >= 3 else "Sambhav" if l == 2 else "Jhukav"
    out = [f"# Event windows: {args.type} ({d0:%b %Y} - {d1:%b %Y})", "",
           f"Event houses {houses}, karakas {karakas}. Layers: Vimshottari MD/AD/PD signify the event, "
           "Yogini MD/AD lords signify it, Chara dasha sign relates to the event houses/lords/karakas, "
           "Jupiter + Saturn double transit.", "",
           J.table(["Rank", "Month", "Strength", "Layers agreeing", "Vimshottari", "Yogini", "Chara sign", "J/S transit"],
                   [[i + 1, f"{r[0]:%b %Y}", lab(r[2]), r[2],
                     " > ".join(p[0] for p in r[3]) + (" ✓" if r[7] else ""),
                     (" > ".join(r[4]) if r[4] else "-") + (" ✓" if r[8] else ""),
                     (J.SIGNS[r[5][0]] if r[5] else "-") + (" ✓" if r[9] else ""), f"{r[6]}/2"]
                    for i, r in enumerate(best)]),
           "\nUse `transits --from/--to` on the top months for exact-hit dates, and the natal promise "
           "(houses, lords, varga) to decide whether the event is promised at all."]
    print("\n".join(out))


# --------------------------------------------------------------------------
# Charts (SVG) + HTML / PDF
# --------------------------------------------------------------------------

def north_svg(J, placements, lagna_sign, title):
    pos = {1: (200, 95), 2: (100, 45), 3: (45, 110), 4: (100, 200), 5: (45, 290), 6: (100, 355),
           7: (200, 305), 8: (300, 355), 9: (355, 290), 10: (300, 200), 11: (355, 110), 12: (300, 45)}
    num = {1: (200, 178), 2: (100, 85), 3: (80, 100), 4: (178, 200), 5: (80, 300), 6: (100, 318),
           7: (200, 225), 8: (300, 318), 9: (320, 300), 10: (222, 200), 11: (320, 100), 12: (300, 85)}
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 430" width="360" height="387">'
         f'<text x="200" y="422" font-size="15" text-anchor="middle" font-family="sans-serif">{title}</text>'
         '<rect x="1" y="1" width="398" height="398" fill="#fffbea" stroke="#b45309" stroke-width="2"/>'
         '<line x1="0" y1="0" x2="400" y2="400" stroke="#b45309"/><line x1="400" y1="0" x2="0" y2="400" stroke="#b45309"/>'
         '<polygon points="200,0 400,200 200,400 0,200" fill="none" stroke="#b45309"/>')
    for h in range(1, 13):
        sg = (lagna_sign + h - 1) % 12
        x, y = num[h]
        s += f'<text x="{x}" y="{y}" font-size="12" fill="#b91c1c" text-anchor="middle" font-family="sans-serif">{sg + 1}</text>'
        lab = (["Asc"] if h == 1 else []) + placements.get(sg, [])
        x, y = pos[h]
        for i, t in enumerate(lab):
            s += (f'<text x="{x}" y="{y + i * 15 - (len(lab) - 1) * 7}" font-size="13" text-anchor="middle" '
                  f'font-weight="bold" font-family="sans-serif">{t}</text>')
    return s + "</svg>"


def south_svg(J, placements, lagna_sign, title):
    grid = [[11, 0, 1, 2], [10, None, None, 3], [9, None, None, 4], [8, 7, 6, 5]]
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 430" width="360" height="387">'
         f'<text x="200" y="422" font-size="15" text-anchor="middle" font-family="sans-serif">{title}</text>'
         '<rect x="1" y="1" width="398" height="398" fill="#f0f9ff" stroke="#1d4ed8" stroke-width="2"/>')
    for r, row in enumerate(grid):
        for c, sg in enumerate(row):
            if sg is None:
                continue
            x, y = c * 100, r * 100
            s += f'<rect x="{x}" y="{y}" width="100" height="100" fill="none" stroke="#1d4ed8"/>'
            s += f'<text x="{x + 5}" y="{y + 14}" font-size="11" fill="#1d4ed8" font-family="sans-serif">{J.SIGNS[sg][:3]}</text>'
            if sg == lagna_sign:
                s += f'<line x1="{x}" y1="{y + 20}" x2="{x + 20}" y2="{y}" stroke="#b91c1c" stroke-width="2"/>'
            for i, t in enumerate(placements.get(sg, [])):
                s += (f'<text x="{x + 50}" y="{y + 38 + i * 15}" font-size="13" text-anchor="middle" '
                      f'font-weight="bold" font-family="sans-serif">{t}</text>')
    return s + "</svg>"


def cmd_charts(args):
    J = _J()
    n = J.Natal(args)
    os.makedirs(args.out, exist_ok=True)
    lab = lambda p: J.ABBR[p] + ("(R)" if n.retro(p) and p not in ("Rahu", "Ketu") else "")
    charts = {}
    for v, nm in ((1, "D1 Rashi"), (9, "D9 Navamsa"), (10, "D10 Dasamsa")):
        pl = {}
        for p in J.PLANETS:
            pl.setdefault(J.varga_sign(n.lons[p], v), []).append(lab(p))
        lg = J.varga_sign(n.asc_lon, v)
        charts[f"north-D{v}.svg"] = north_svg(J, pl, lg, f"{nm} (North)")
        charts[f"south-D{v}.svg"] = south_svg(J, pl, lg, f"{nm} (South)")
    mpl = {}
    for p in J.PLANETS:
        mpl.setdefault(n.signs[p], []).append(lab(p))
    charts["north-Moon.svg"] = north_svg(J, mpl, n.moon_sign, "Chandra kundali")
    for fn, svg in charts.items():
        with open(os.path.join(args.out, fn), "w") as fh:
            fh.write(svg)
    rows = "".join(f"<tr><td>{p}</td><td>{J.fmt_lon(n.lons[p])}{' R' if n.retro(p) and p not in ('Rahu', 'Ketu') else ''}</td>"
                   f"<td>{J.nakshatra_info(n.lons[p])['name']}-{J.nakshatra_info(n.lons[p])['pada']}</td>"
                   f"<td>{J.house_from(n.signs[p], n.lagna)}</td><td>{J.dignity(p, n.lons[p], n.signs) if p in J.SEVEN else '-'}</td></tr>"
                   for p in J.PLANETS)
    path = n.dasha.path(J.jd_from_utc(datetime.utcnow()), 3)
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Kundali - {args.name or ''}</title>
<style>body{{font-family:sans-serif;margin:24px;color:#111}}h1{{color:#b45309}}table{{border-collapse:collapse;margin:12px 0}}
td,th{{border:1px solid #ccc;padding:4px 8px;font-size:13px}}.charts svg{{margin:6px}}</style></head><body>
<h1>Kundali: {args.name or ''}</h1><p>{n.local:%d %b %Y %H:%M} · {args.place or ''} · Lagna {J.fmt_lon(n.asc_lon)} ·
Rashi {J.SIGNS[n.moon_sign]} · {J.nakshatra_info(n.lons['Moon'])['name']} · Running: {' > '.join(p[0] for p in path)}</p>
<div class="charts">{charts['north-D1.svg']}{charts['south-D1.svg']}{charts['north-D9.svg']}{charts['north-D10.svg']}{charts['north-Moon.svg']}</div>
<table><tr><th>Planet</th><th>Position</th><th>Nakshatra</th><th>House</th><th>Dignity</th></tr>{rows}</table>
<p style="font-size:11px;color:#666">Calculated with {n.eph.engine}, {args.ayanamsa} ayanamsa.</p></body></html>"""
    hp = os.path.join(args.out, "kundali.html")
    with open(hp, "w") as fh:
        fh.write(html)
    print(f"wrote {len(charts)} SVG charts and {hp}")
    if args.pdf:
        js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
              f"const p=await b.newPage();await p.goto('file://{os.path.abspath(hp)}');"
              f"await p.pdf({{path:'{os.path.abspath(os.path.join(args.out, 'kundali.pdf'))}',format:'A4',printBackground:true}});"
              "await b.close();})()")
        try:
            subprocess.run(["node", "-e", js], check=True, capture_output=True, timeout=120)
            print("wrote " + os.path.join(args.out, "kundali.pdf"))
        except Exception as ex:
            print(f"PDF not created ({ex.__class__.__name__}): open kundali.html and print to PDF instead.")


# --------------------------------------------------------------------------
# Daily personal rashifal
# --------------------------------------------------------------------------

def cmd_daily(args):
    J = _J()
    n = J.Natal(args)
    e = n.eph
    tz = J.TZ(args.at_tz) if args.at_tz else n.tz
    lat = args.at_lat if args.at_lat is not None else n.lat
    lon = args.at_lon if args.at_lon is not None else n.lon
    day = J.parse_date(args.day) if args.day else tz.from_utc(datetime.utcnow()).replace(hour=0, minute=0, second=0, microsecond=0)
    sr = e.sun_event(J.jd_from_utc(tz.to_utc(day)), lat, lon, True)
    ss = e.sun_event(sr, lat, lon, False)
    wd = day.weekday()
    pan = J.panchang_at(e, sr)
    natal_nak = J.nakshatra_info(n.lons["Moon"])["index"]
    tara = J.TARA[((pan["nak_index"] - natal_nak) % 27) % 9]
    mh = J.house_from(J.sign_of(e.lon(sr + 0.25, "Moon")), n.moon_sign)
    ml = J.house_from(J.sign_of(e.lon(sr + 0.25, "Moon")), n.lagna)
    cb = "CHANDRASHTAMA - low-key day" if mh == 8 else "good" if mh in (1, 3, 6, 7, 10, 11) else "weak" if mh in (4, 12) else "mixed"
    path = n.dasha.path(sr + 0.25, 5)
    part = (ss - sr) / 8
    rk = (sr + (J.RAHU_KAAL_PART[wd] - 1) * part, sr + J.RAHU_KAAL_PART[wd] * part)
    idx = J.HORA_ORDER.index(J.WEEKDAY_LORD[wd])
    good = []
    for k in range(8):
        a, b = sr + k * part, sr + (k + 1) * part
        cg = J.CHOGHADIYA[J.HORA_ORDER[(idx + k) % 7]]
        if cg in ("Amrit", "Shubh", "Labh") and not (a < rk[1] and b > rk[0]):
            good.append(f"{J.fmt_local(tz.from_utc(J.utc_from_jd(a)), False)}-{J.fmt_local(tz.from_utc(J.utc_from_jd(b)), False)} {cg}")
    ev = []
    for p in ("Sun", "Mars", "Mercury", "Venus", "Jupiter", "Saturn", "Rahu"):
        for tc, a, b in J.scan_changes(lambda j, p=p: J.sign_of(e.lon(j, p)), sr - 0.5, sr + 1.5, 0.25):
            ev.append(f"{p} enters {J.SIGNS[b]} (H{J.house_from(b, n.lagna)} from Lagna)")
    loc = lambda j: J.fmt_local(tz.from_utc(J.utc_from_jd(j)), False)
    out = [f"## {args.name or 'Aaj'} - {day:%A %d %b %Y}",
           f"- Panchang: {pan['tithi']}, {pan['nakshatra']}, {pan['yoga']} yoga; sunrise {loc(sr)}, sunset {loc(ss)}",
           f"- Chandra: natal Moon se H{mh}, Lagna se H{ml} ({cb}); tarabala {tara}",
           f"- Dasha: {' > '.join(p[0] for p in path)}",
           f"- Shubh samay: {', '.join(good) or '-'}",
           f"- Bachein: Rahu kaal {loc(rk[0])}-{loc(rk[1])}",
           f"- Gochar: {'; '.join(ev) if ev else 'koi rashi parivartan nahi'}"]
    print("\n".join(out))


# --------------------------------------------------------------------------
# Prediction log
# --------------------------------------------------------------------------

def _logpath():
    d = _X().PROFILE_DIR
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "predictions.json")


def cmd_log(args):
    J = _J()
    path = _logpath()
    data = json.load(open(path)) if os.path.exists(path) else []
    if args.action == "add":
        if not (args.text and args.start and args.end):
            raise SystemExit("log add needs --text --start --end (and ideally --area --strength --technique)")
        item = {"id": (max([d["id"] for d in data]) + 1) if data else 1, "profile": args.profile,
                "created": datetime.utcnow().strftime("%Y-%m-%d"), "start": args.start, "end": args.end,
                "area": args.area, "strength": args.strength, "technique": args.technique,
                "text": args.text, "outcome": None, "note": None}
        data.append(item)
        json.dump(data, open(path, "w"), indent=1, ensure_ascii=False)
        print(f"logged #{item['id']}")
    elif args.action == "mark":
        it = next((d for d in data if d["id"] == args.id), None)
        if not it:
            raise SystemExit(f"No prediction #{args.id}")
        it["outcome"], it["note"] = args.outcome, args.note
        json.dump(data, open(path, "w"), indent=1, ensure_ascii=False)
        print(f"marked #{args.id} {args.outcome}")
    elif args.action == "list":
        today = datetime.utcnow().strftime("%Y-%m-%d")
        rows = [[d["id"], d["profile"] or "-", d["start"], d["end"], d["area"] or "-", d["strength"] or "-",
                 d["text"][:70], d["outcome"] or ("DUE - ask the outcome" if d["end"] < today else "open")]
                for d in data if (not args.profile or d["profile"] == args.profile)
                and (not args.due or (d["outcome"] is None and d["end"] < today))]
        print(J.table(["#", "Profile", "From", "To", "Area", "Strength", "Prediction", "Outcome"], rows) if rows else "No predictions.")
    elif args.action == "stats":
        done = [d for d in data if d["outcome"] and (not args.profile or d["profile"] == args.profile)]
        if not done:
            print("No marked predictions yet.")
            return
        val = {"hit": 1.0, "partial": 0.5, "miss": 0.0}
        out = [f"Marked predictions: {len(done)}; overall hit rate {sum(val[d['outcome']] for d in done) / len(done):.0%}", ""]
        for key in ("strength", "area", "technique"):
            grp = {}
            for d in done:
                grp.setdefault(d.get(key) or "-", []).append(val[d["outcome"]])
            out.append(J.table([key.title(), "Count", "Hit rate"],
                               [[k, len(v), f"{sum(v) / len(v):.0%}"] for k, v in sorted(grp.items())]))
            out.append("")
        out.append("Calibrate: a technique or strength label with a hit rate below ~50% deserves a lower label "
                   "next time (e.g. require one more agreeing layer before calling it Pakka).")
        print("\n".join(out))


# --------------------------------------------------------------------------
# South Indian Dashakoota (10 poruthams)
# --------------------------------------------------------------------------

RAJJU = {**{i: "Pada" for i in (0, 8, 9, 17, 18, 26)}, **{i: "Kati" for i in (1, 7, 10, 16, 19, 25)},
         **{i: "Nabhi" for i in (2, 6, 11, 15, 20, 24)}, **{i: "Kantha" for i in (3, 5, 12, 14, 21, 23)},
         **{i: "Siro" for i in (4, 13, 22)}}
VEDHA = [{0, 17}, {1, 16}, {2, 15}, {3, 14}, {5, 21}, {6, 20}, {7, 19}, {8, 18}, {9, 26}, {10, 25},
         {11, 24}, {12, 23}, {4, 13}, {4, 22}, {13, 22}]
VASYA_RASI = {0: {4, 7}, 1: {3, 6}, 2: {5}, 3: {7, 8}, 4: {6}, 5: {2, 11}, 6: {9, 5}, 7: {3},
              8: {11}, 9: {0, 10}, 10: {0}, 11: {9}}


def dashakoota(J, boy, girl):
    X = _X()
    bm, gm = boy.lons["Moon"], girl.lons["Moon"]
    bn, gn = J.nakshatra_info(bm)["index"], J.nakshatra_info(gm)["index"]
    bs, gs = J.sign_of(bm), J.sign_of(gm)
    c = (bn - gn) % 27 + 1
    rows = []
    rows.append(["Dina", f"count {c}", "good" if c % 9 in (2, 4, 6, 8, 0) else "bad"])
    gb, gg = J.GANA[bn], J.GANA[gn]
    rows.append(["Gana", f"{gb}/{gg}", "good" if gb == gg else "medium" if {gb, gg} == {"Deva", "Manushya"} else "bad"])
    rows.append(["Mahendra", f"count {c}", "good" if c in (4, 7, 10, 13, 16, 19, 22, 25) else "-"])
    rows.append(["Stree Deergha", f"count {c}", "good" if c > 13 else "medium" if c > 9 else "bad"])
    yp = X.YONI_PTS[X.YONI_ORDER.index(J.YONI[bn])][X.YONI_ORDER.index(J.YONI[gn])]
    rows.append(["Yoni", f"{J.YONI[bn]}/{J.YONI[gn]}", "good" if yp >= 3 else "medium" if yp == 2 else "bad"])
    r = (bs - gs) % 12 + 1
    rows.append(["Rasi", f"boy's rasi {r} from girl's", "good" if r in (1, 7, 9, 10, 11) else "bad"])
    lb, lg = J.SIGN_LORD[bs], J.SIGN_LORD[gs]
    rel = {J.natural_rel(lb, lg), J.natural_rel(lg, lb)} if lb != lg else {"friend"}
    rows.append(["Rasyadhipati", f"{lb}/{lg}", "bad" if "enemy" in rel else "good" if rel == {"friend"} else "medium"])
    rows.append(["Vasya", f"{J.SIGNS[bs]}/{J.SIGNS[gs]}", "good" if gs in VASYA_RASI[bs] or bs in VASYA_RASI[gs] else "-"])
    rows.append(["Rajju (critical)", f"{RAJJU[bn]}/{RAJJU[gn]}", "BAD - same rajju" if RAJJU[bn] == RAJJU[gn] else "good"])
    rows.append(["Vedha (critical)", f"{J.NAKSHATRAS[bn]}/{J.NAKSHATRAS[gn]}", "BAD - vedha pair" if {bn, gn} in VEDHA else "good"])
    goods = sum(1 for x in rows if x[2].startswith("good"))
    return rows, goods


# --------------------------------------------------------------------------
# CLI registration
# --------------------------------------------------------------------------

def register(sub, add_birth, add_at):
    t = sub.add_parser("tajik", help="full Tajik Varshphal: year lord, sahams, Tajik yogas, Mudda dasha, monthly charts")
    add_birth(t)
    add_at(t)
    t.add_argument("--year", type=int, required=True)
    t.set_defaults(fn=cmd_tajik)

    p = sub.add_parser("prashna", help="KP horary (number 1-249)")
    p.add_argument("--number", type=int, required=True)
    p.add_argument("--question", required=True, choices=list(KP_Q))
    p.add_argument("--at-lat", type=float, required=True)
    p.add_argument("--at-lon", type=float, required=True)
    p.add_argument("--at-tz", required=True)
    p.add_argument("--when", default=None, help="YYYY-MM-DDTHH:MM local (default now)")
    p.add_argument("--engine", default="auto", choices=["auto", "swe", "lite"])
    p.set_defaults(fn=cmd_prashna, needs_birth=False, ayanamsa="kp")

    ev = sub.add_parser("event", help="rank months for an event by multi-dasha + transit agreement")
    add_birth(ev)
    ev.add_argument("--type", required=True, choices=list(_X().EVENT_RULES))
    ev.add_argument("--from", required=True)
    ev.add_argument("--to", required=True)
    ev.add_argument("--top", type=int, default=12)
    ev.set_defaults(fn=cmd_event)

    c = sub.add_parser("charts", help="North/South Indian SVG charts + kundali.html (+ --pdf)")
    add_birth(c)
    c.add_argument("--out", required=True)
    c.add_argument("--pdf", action="store_true")
    c.set_defaults(fn=cmd_charts)

    d = sub.add_parser("daily", help="short personal daily rashifal")
    add_birth(d)
    add_at(d)
    d.add_argument("--day", default=None)
    d.set_defaults(fn=cmd_daily)

    lg = sub.add_parser("log", help="prediction log: add / list / mark / stats")
    lg.add_argument("action", choices=["add", "list", "mark", "stats"])
    lg.add_argument("--profile", default=None)
    lg.add_argument("--start")
    lg.add_argument("--end")
    lg.add_argument("--area")
    lg.add_argument("--strength", choices=["Pakka", "Sambhav", "Jhukav"])
    lg.add_argument("--technique")
    lg.add_argument("--text")
    lg.add_argument("--id", type=int)
    lg.add_argument("--outcome", choices=["hit", "partial", "miss"])
    lg.add_argument("--note")
    lg.add_argument("--due", action="store_true")
    lg.set_defaults(fn=cmd_log, needs_birth=False)
