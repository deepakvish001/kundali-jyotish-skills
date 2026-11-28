# Tools: profiles, rectification, kundali milan, muhurta, built-in ephemeris

Contents: 1. Profiles · 2. Birth-time rectification · 3. Kundali milan · 4. Muhurta finder ·
5. Built-in ephemeris · 6. Event finder · 7. Tajik Varshphal · 8. KP Prashna · 9. Charts and
PDF · 10. Daily rashifal · 11. Prediction log

## 1. Profiles

```bash
$PY $J profile save --profile "rahul" --date 1990-05-01 --time 07:15 --tz Asia/Kolkata \
    --lat 28.61 --lon 77.21 --place Delhi --name "Rahul" --sex male
$PY $J profile list | show --profile rahul | delete --profile rahul
$PY $J chart --profile rahul --asof <today>          # any command accepts --profile
```
Stored as JSON in `~/.kundali/` (override with the `KUNDALI_HOME` environment variable). Save a
profile whenever someone gives birth details you will reuse (self, spouse, children, parents).
In a cloud or app sandbox the folder may not survive the session; say so if it matters.

## 2. Birth-time rectification

Use when the time is approximate ("subah 6-7 ke beech"), the Lagna/D9/D10 sits on a boundary
(chart section 19), or predictions keep missing. Collect 4-6 dated events of different types:

```bash
$PY $J rectify --profile rahul --window 30 --step 1 \
   --event 2012-06-20:education --event 2015-08-01:job --event 2018-02-14:marriage \
   --event 2019-11-03:child --event 2021-05-10:father_loss
```
Event types: marriage, engagement, divorce, child, job, promotion, job_loss, business, education,
foreign, property, vehicle, accident, illness, father_loss, mother_loss, sibling.

How it scores each candidate time: for every event, the running MD/AD/PD lords (weights 3/2/1)
get points if they own or occupy the event houses, are the karaka, or sit in the nakshatra of such
a lord; +1 each when transiting Jupiter and Saturn influence the event houses or their lords
(double transit); +1/+0.5 when the relevant varga (D9 marriage, D10 career, D7 child, D12
parents...) has its key lord in the dasha.

Reading the output: the **segments** table groups candidate times with the same Lagna/D9/D10.
Pick the segment that wins across most events (not a single spike), then confirm with physical
appearance and temperament (Lagna, Lagna lord), spouse description (7th, D9) and career type
(10th, D10). Report the rectified time with the confidence and re-run `report` with it. Exact event
dates (day, not month) make the dasha part sharper.

## 3. Kundali milan (Ashtakoota)

```bash
$PY $J match --boy rahul --girl priya                    # saved profiles
$PY $J match --boy "1990-05-01,07:15,Asia/Kolkata,28.61,77.21,Rahul" \
             --girl "1993-09-12,22:40,Asia/Kolkata,19.08,72.88,Priya"
```
| Koota | Max | Rule used |
|---|---|---|
| Varna | 1 | groom's Moon-sign varna >= bride's |
| Vashya | 2 | 5 groups (Chatushpada, Manava, Jalachara, Vanachara, Keeta; Sagittarius/Capricorn split at 15°), most common bride-row/groom-column grid |
| Tara | 3 | 1.5 for each direction whose count mod 9 is not 3, 5, 7 |
| Yoni | 4 | 14 animals; same 4; the 7 sworn-enemy pairs (Horse-Buffalo, Elephant-Lion, Sheep-Monkey, Serpent-Mongoose, Dog-Deer, Cat-Rat, Cow-Tiger) 0; others from the widely used software table |
| Graha maitri | 5 | Moon-sign lords' natural relationship (5/4/3/1/0.5/0) |
| Gana | 6 | same 6; Deva-Manushya 5; Rakshasa groom with Deva/Manushya bride 0; Deva/Manushya groom with Rakshasa bride 1 |
| Bhakoot | 7 | 0 for 2/12, 6/8, 5/9 Moon-sign relations |
| Nadi | 8 | 0 if same nadi |

Published tables differ for Vashya, Yoni (non-enemy pairs) and Gana direction; if the family's
pandit uses another table, a 1-2 point difference is normal - say so. Verdict bands: 33+ excellent,
25-32 very good, 18-24 acceptable, <18 below the traditional minimum. The tool also applies the
standard Nadi and Bhakoot cancellations and compares Manglik status. A full milan reading adds:
7th houses and lords, Venus/Jupiter, D9 of both, Darakaraka/Upapada, and both persons' dashas in
the planned marriage period (`chart --profile` for each).

## 4. Muhurta finder

```bash
$PY $J muhurta --purpose marriage --from 2027-01-01 --to 2027-06-30 \
   --at-lat 26.91 --at-lon 75.79 --at-tz Asia/Kolkata [--profile priya] [--include-night] [--top 10]
```
Purposes: marriage, griha_pravesh, vehicle, business, travel, interview, general.
Rules applied per 10-minute slot: purpose nakshatras and weekdays; no Rikta tithi (4/9/14) or
Amavasya; none of the 9 bad yogas (Vishkambha, Atiganda, Shula, Ganda, Vyaghata, Vajra,
Vyatipata, Parigha, Vaidhriti); no Vishti (Bhadra) karana; outside Rahu kaal, Yamaganda and
Gulika; good choghadiya (Chal also for travel/vehicle); lagna type (fixed/dual for marriage, fixed
for griha pravesh and business, movable for vehicle/travel). Marriage and griha pravesh also
exclude Kharmas (Sun in Dhanu/Meen), Chaturmas (Ashadha Shukla Ekadashi to Kartika Shukla
Ekadashi), Adhik maas and Jupiter/Venus combustion. With `--profile` it requires good tarabala and
no Chandrabala 4/8/12 for that person (for marriage, run once for each partner and intersect).
Present the top windows with their panchang, and mention that local tradition (e.g. the family
pandit's Panchang) may add holidays or regional rules.

## 5. Built-in ephemeris

`setup.sh` falls back to plain `python3` when pyswisseph cannot be installed (e.g. inside the Claude
app); `--engine auto` (default) then uses `scripts/data/ephem.bin`: daily Swiss Ephemeris samples
1900-2100 with 6-point interpolation. Measured against pyswisseph: planets within 2 arc-seconds,
ascendant within 10 arc-seconds, sunrise within ~30 s (so Bhava/Hora/Ghati lagna can differ by a
few arc-minutes). Not available in this mode: eclipses (listed as unavailable) and Placidus cusps
(KP section uses Porphyry - say so for KP cusp sub-lord answers). Dates outside 1900-2100 need
pyswisseph. Rebuild the data with `python3 scripts/build_ephem.py` (needs pyswisseph).

## 6. Event finder

```bash
$PY $J event --profile rahul --type marriage --from 2026-12-01 --to 2030-12-31 --top 12
```
Types as in `rectify`. Each month is checked by four independent layers: Vimshottari MD/AD/PD
signification of the event houses/karakas, Yogini MD/AD lords, Jaimini Chara dasha sign relation
to the event houses/lords/karakas, and the Jupiter + Saturn double transit. 3-4 layers = Pakka,
2 = Sambhav, 1 = Jhukav. Then narrow the best months with `transits` exact-hit dates.

## 7. Tajik Varshphal

```bash
$PY $J tajik --profile rahul --year 2027 [--at-lat --at-lon --at-tz <current city>]
```
Gives the solar-return moment, Varsha lagna, Muntha, the five office-bearers and the year lord
(strongest bearer with a Tajik aspect to the Varsha lagna, strength by sign dignity + kendra, a
simplified Pancha-vargiya), Sahams (Punya, Vidya, Vivaha, Putra), Ithasala/Ishrafa yogas
(Tajik orbs: Sun 15, Moon 12, Mars 8, Mercury 7, Jupiter 9, Venus 7, Saturn 9), Mudda dasha and
the 12 monthly (Masa pravesh) charts.

## 8. KP Prashna

```bash
$PY $J prashna --number 108 --question marriage --at-lat .. --at-lon .. --at-tz .. [--when now]
```
The person thinks of the question and gives a number 1-249 (KP sub divisions, sign boundaries
split). The number fixes the horary ascendant; cusps are cast for the moment that degree rises
at the place (Placidus with pyswisseph, Porphyry with the built-in ephemeris), planets for the
question time, KP ayanamsa and true node. Verdict from the question cusp's sub lord (marriage 7,
job 10, money 2, property 4, travel 12, child 5, health 1, litigation 6, education 4, business 7)
and the houses it signifies, plus the ruling planets for timing.

## 9. Charts and PDF

```bash
$PY $J charts --profile rahul --out charts/ [--pdf]
```
North and South Indian SVGs for D1, D9, D10 and the Moon chart, plus `kundali.html` (charts +
planet table). `--pdf` renders `kundali.pdf` where Node + Playwright exist; otherwise open the HTML
and print to PDF. Share the files with the person.

## 10. Daily rashifal

```bash
$PY $J daily --profile rahul --at-lat .. --at-lon .. --at-tz .. [--day YYYY-MM-DD]
```
Seven lines: panchang, Moon's house from natal Moon/Lagna with chandrabala and tarabala, running
dasha to Prana, good choghadiya windows outside Rahu kaal, Rahu kaal, and sign changes that day.
To send it every morning, create a scheduled task (in Claude Code: the scheduled-task tools; at a
time the person chooses) whose prompt runs this command for their saved profile and city and
writes it up in their language. The profile must exist where the task runs.

## 11. Prediction log

```bash
$PY $J log add --profile rahul --start 2027-03-01 --end 2027-06-30 --area career --strength Pakka \
   --technique "vimshottari+double-transit" --text "Job change / promotion"
$PY $J log list --profile rahul --due        # past their end date without an outcome
$PY $J log mark --id 3 --outcome hit|partial|miss --note "..."
$PY $J log stats [--profile rahul]           # hit rate by strength, area, technique
```
Stored in `~/.kundali/predictions.json` next to the profiles.

## Not implemented

Narayana dasha, Kalachakra dasha and the Sarvatobhadra chakra are not computed: their rules and
grid layouts need a verified source. If asked, say so and use the implemented systems instead.
