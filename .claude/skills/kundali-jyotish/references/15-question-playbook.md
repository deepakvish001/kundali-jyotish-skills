# Question playbook: how to answer any question about a chart

Every question gets the same disciplined process. Do not answer from one factor.

## The protocol (do all steps, every time)

1. **Pin the question**: which life area, which period (default: next 3 years), yes/no or timing or
   quality? If the person is not the native (spouse, child, parent), use the native's chart with
   bhavat bhavam (e.g. spouse = 7th as Lagna) and say so.
2. **Map it** with the table below: houses, karakas, varga, Jaimini/KP points, event type.
3. **Promise** (does the chart allow it at all?): house + lord (dignity, bala §21, avastha §11,
   aspects §13, bhavesh phala references/11), karakas, varga (D9/D10/D7/D4...), yogas (§6, §20),
   SAV and reduced BAV of the house (§8, §23). Grade: strong / moderate / weak / denied.
4. **Dasha**: which periods activate those houses/karakas - Vimshottari MD/AD/PD (§9), Yogini
   (§17), Chara (§22), Ashtottari/Shodashottari if applicable. Run `event --type ...` for timing
   questions.
5. **Transit**: Jupiter/Saturn double transit on the house/lord (from Lagna and Moon), BAV bindus
   of the transit signs, exact hits (`transits` file 02/06), Sade Sati/dhaiya, eclipses.
6. **Cross-check**: KP cusp sub lord of the main house (§5) and, for a yes/no with no reliable
   chart, `prashna`. Year questions: `tajik` (year lord, Muntha, Sahams, Ithasala).
7. **Combine**: promise + dasha + transit (+ Yogini/Chara/KP/Tajik agreement) -> Pakka / Sambhav /
   Jhukav. Check `log stats` if this profile has history.
8. **Answer**: the direct answer first (yes/no + when), then the reasons (each factor with its
   value), then what to do (remedy, timing advice). Offer to log the prediction.

## Question map

| Question (Hinglish) | Houses | Karakas | Varga / Jaimini / KP | `event` type |
|---|---|---|---|---|
| Shaadi kab hogi? | 7, 2, 11 (+5 love) | Venus; Jupiter (woman's chart) | D9, UL, DK; KP 7th CSL in 2/7/11 | marriage |
| Love ya arranged? | 5 & 7 link, 9/11 (family) | Venus, Mars, Rahu | D9 5th-7th, A7 | - |
| Spouse kaisa hoga? | 7th sign, lord, occupants | Venus/Jupiter, DK | D9 7th & Lagna, UL 2nd | - |
| Marriage me problem / divorce? | 7, 2, 8, 12, 6 from 7 | Venus, Mars, Saturn, Rahu | D9, UL & its 2nd, A7 | divorce |
| Naukri kab lagegi? | 10, 6, 2, 11 | Sun, Saturn, Mercury | D10, AmK, A10; KP 10th CSL in 2/6/10/11 | job |
| Sarkari naukri? | 10, 6, 9 | Sun (+Moon, Jupiter) | D10 Sun/10th lord | job |
| Promotion? | 10, 11, 2 | Sun, Jupiter | D10 | promotion |
| Job change / chhootna? | 10 and 12/8 from 10 (9, 5), 3 | Saturn, Rahu | D10 | job_loss / job |
| Business karu ya job? | 7, 10, 3, 11 vs 6 | Mercury, Venus, Rahu | D10 7th vs 6th; KP 7 vs 6 | business |
| Career field kaunsa? | 10th sign/lord/occupants, AmK | strongest of 10th-influencers | D10 Lagna & 10th | - |
| Paisa kab aayega / dhan yog? | 2, 11, 5, 9, 8 (sudden) | Jupiter, Venus | D2, HL, Indu Lagna | - (use dasha + transits) |
| Investment / share market? | 5, 8, 11 vs 12 | Mercury, Jupiter, Rahu | D2 | - |
| Karz / loan? | 6, 8, 12, 11 | Saturn, Mars | - | - |
| Property / ghar kab? | 4, 11, 12 (loan), 2 | Mars, Venus, Saturn, Moon | D4; KP 4th CSL in 4/11/12 | property |
| Gaadi kab? | 4, 11 | Venus | D16 | vehicle |
| Videsh jaunga / settle? | 12, 9, 7, 3 | Rahu, Saturn, Moon | movable signs, D9 12th; KP 12th CSL 3/9/12 | foreign |
| Santaan kab? | 5, 2, 11 | Jupiter | D7, PK; KP 5th CSL 2/5/11 | child |
| Padhai / exam / competition? | 4, 5, 9, 6 (competition), 11 | Mercury, Jupiter | D24; KP 4/9/11 | education |
| Sehat / bimari ka samay? | 1, 6, 8, 12, maraka | Sun, Moon, Lagna lord | D30, Gulika; Sade Sati | illness |
| Accident / surgery ka yog? | 8, 6, 1, 3 | Mars, Rahu, Ketu, Saturn | D30 | accident |
| Court case jeetunga? | 6, 11 vs 7, 12, 8 | Mars, Saturn, Sun | KP 6th CSL in 6/11 | - (`prashna --question litigation`) |
| Maa / papa ki sehat? | 4 / 9 (and 8th from them) | Moon / Sun | D12 | mother_loss / father_loss bands only as "care periods" |
| Bhai-behen? | 3 (younger), 11 (elder) | Mars | D3 | sibling |
| Ye saal kaisa rahega? | all, by dasha | - | `tajik --year`, Muntha | - |
| Is mahine / hafte / aaj? | Moon houses, PD/SD/Prana | Moon | files 02/03/04, `daily` | - |
| Sade Sati ka asar? | 12/1/2 from Moon | Saturn | Saturn BAV & kakshya, functional role | - |
| Kaunsa ratna / upay? | weak functional benefics, troubling malefics | - | §15/§21 strength, references/08 | - |
| Shubh muhurat? | - | - | `muhurta --purpose ...` | - |
| Kundli milan? | - | - | `match --system both` + 7th/D9 of both | - |
| Haan/na sawal (koi bhi)? | relevant house | - | `prashna --number N` | - |
| Janm samay sahi hai? | Lagna/D9/D10 boundaries | - | `rectify` with 4-6 dated events | - |

## Answer template

```
**Seedha jawab:** <haan / nahi / kab: dates> - <Pakka/Sambhav/Jhukav>
**Kyun (factors):**
- Promise: <house, lord, dignity/bala, yoga, varga>
- Dasha: <Vimshottari MD>AD>PD dates; Yogini; Chara sign>
- Gochar: <double transit dates, exact hits, BAV>
- Cross-check: <KP CSL / Tajik / prashna>
**Kya karein:** <timing advice, remedy>
```

When factors disagree, say which you weigh more and why (usually Vimshottari + double transit
over a single secondary system), and give the second-best window.
