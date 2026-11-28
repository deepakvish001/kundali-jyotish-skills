# Kundali-jyotish-skills

Claude skills for detailed Vedic astrology (Jyotish) kundali reading. The main skill,
**`kundali-jyotish`**, turns Claude into a rigorous chart reader. It:

- reads a kundali report completely: PDF, screenshot, photo of a handwritten janampatri, or
  AstroSage / ClickAstro / Jagannatha Hora printouts (North, South and East Indian charts);
- **recomputes the chart** with the Swiss Ephemeris and checks it against the report (ayanamsa,
  time zone, Indian war time 1942-45, birth-time sensitivity);
- analyses every layer: rashi, house (whole-sign, Bhava Chalit, KP), exact degree,
  nakshatra-pada-lord-deity, tara, uchcha/neecha/moolatrikona/swa, natural + temporary +
  compound friend/enemy tables, vakri/asta/graha yuddha/sandhi/gandanta/vargottama, avasthas,
  aspects with virupa strength and conjunction orbs, D1-D60 vargas, bala components and
  Vimshopaka, yogas and doshas (with cancellations), Vimshottari to Prana + Yogini dasha, gochar
  with vedha, kakshya and exact transit hits, KP, Jaimini, special lagnas, upagrahas, Varshphal;
- gives direct predictions with timing at **five levels - year, month, week, day and hour**
  (hora, choghadiya, Rahu kaal, rising-sign windows), each with its reasons and a strength label
  (Pakka / Sambhav / Jhukav), plus full remedies (gemstone, mantra, daan, dosha upay);
- **rectifies an uncertain birth time** from dated life events, does **kundli milan** (36-gun
  Ashtakoota with Nadi/Bhakoot cancellations and Manglik comparison), finds **shubh muhurat**
  (marriage, griha pravesh, vehicle, business, travel, interview) and saves birth profiles;
- works even where pyswisseph can't be installed (e.g. the Claude app) via a built-in ephemeris
  for 1900-2100;
- answers in the user's language, Hinglish by default for Hinglish questions.

> Calculations are exact (Swiss Ephemeris). Readings are direct, in the voice of a senior jyotishi.
> Four fixed limits: no date of death or remaining lifespan, never advise stopping medical
> treatment, no lottery/betting numbers, no prediction of an unborn child's sex.

## Layout

```
.claude/skills/kundali-jyotish/
├── SKILL.md                 workflow (start here)
├── scripts/
│   ├── setup.sh             finds or installs pyswisseph, prints the python to use
│   ├── jyotish.py           engine: report | chart | transits | day | dasha | varshphal
│   ├── jyotish_ext.py       profile | rectify | match | muhurta
│   ├── lite_ephem.py        built-in ephemeris backend (no pyswisseph needed)
│   ├── build_ephem.py       rebuilds data/ephem.bin from pyswisseph
│   └── data/ephem.bin       daily ephemeris 1900-2100 (1.7 MB)
├── references/              01 reading reports ... 09 advanced layers, 10 tools
├── assets/master-prompt.md  copy-paste prompt for chat apps without the skill
└── evals/                   test prompts + a fictional kundali PDF
```

## Install

- **Claude Code in this repo**: nothing to do. Skills in `.claude/skills/` load automatically.
- **Claude Code anywhere**: copy `.claude/skills/kundali-jyotish/` to `~/.claude/skills/` (all
  projects) or to another project's `.claude/skills/`.
- **Claude apps that support custom skills**: zip the `kundali-jyotish` folder and upload it as a
  custom skill.
- **Any other chat app**: paste `assets/master-prompt.md` and attach your report.

## Use

Just talk to Claude:

- "Ye meri kundli ki PDF hai, pura detail analysis karo aur agle 12 mahine ka month-wise batao."
- "DOB 14-03-1996, 6:40 AM, Indore - shaadi kab hogi, government job ka yog hai kya?"
- "Kal interview hai, Jaipur me hoon - kal ka hour-wise best time batao."

## Calculation engine (optional, direct use)

`chart` prints 19 sections: panchang, planets, houses, 16 vargas, KP, yogas/doshas, Jaimini,
ashtakavarga, Vimshottari to Prana, transits, Sade Sati, planet details (nakshatra deity, tara,
avasthas, flags), friendship tables, aspect strength in virupas, Bhava Chalit, strength
(bala components, Vimshopaka), special lagnas and upagrahas, Yogini dasha, prastarashtakavarga,
birth-time sensitivity. `report` runs everything in one go.

```bash
PY=$(bash .claude/skills/kundali-jyotish/scripts/setup.sh)
S=.claude/skills/kundali-jyotish/scripts/jyotish.py
$PY $S report    --date 1992-08-23 --time 14:15 --tz Asia/Kolkata --lat 26.9124 --lon 75.7873 --out out/
$PY $S chart     --date 1992-08-23 --time 14:15 --tz Asia/Kolkata --lat 26.9124 --lon 75.7873 --asof 2026-11-27
$PY $S transits  --date ... --from 2026-12-01 --to 2027-11-30 --monthly
$PY $S day       --date ... --day 2026-11-28 --days 7   # horas, choghadiya, Rahu kaal
$PY $S dasha     --date ... --level 3 --from 2026-01-01 --to 2030-01-01
$PY $S varshphal --date ... --year 2027
$PY $S profile save --profile me --date ... --time ... --tz ... --lat ... --lon ... --place ...
$PY $S rectify   --profile me --window 30 --event 2015-08-01:job --event 2018-02-14:marriage --event 2019-11-03:child
$PY $S match     --boy me --girl "1993-09-12,22:40,Asia/Kolkata,19.08,72.88,Priya"
$PY $S muhurta   --purpose marriage --from 2027-01-01 --to 2027-06-30 --at-lat 26.91 --at-lon 75.79 --at-tz Asia/Kolkata
```

Defaults: Lahiri ayanamsa, mean node, whole-sign houses (Placidus only for KP), 365.2425-day
dasha year, sunrise at the upper limb with refraction. Each one can be changed with a flag.
Use an IANA time zone (`Asia/Kolkata`) so historical offsets are applied automatically.

Requires Python 3.9+. `pyswisseph` is used when available (installed by `setup.sh`); otherwise the
built-in ephemeris (1900-2100) is used automatically: planets within 2", ascendant within 10",
sunrise within ~30 s; eclipses and Placidus (KP) cusps need pyswisseph.
