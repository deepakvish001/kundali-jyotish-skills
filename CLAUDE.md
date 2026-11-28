# Instructions for Claude in this repo

This repo holds Claude skills for Vedic astrology (Jyotish). The main skill is
`.claude/skills/kundali-jyotish/`.

- For any kundali / horoscope / birth-chart request, use the `kundali-jyotish` skill and follow
  its SKILL.md (calculate with `scripts/jyotish.py`, never from memory).
- When editing the skill: keep SKILL.md under ~500 lines and put detail in `references/`. Never
  put data from the eval charts (`evals/`) into SKILL.md or references, because that would let
  the skill pass its tests without real reasoning.
- After changing `scripts/jyotish.py`, run `chart`, `day` and `transits` for at least one eval
  chart and check against known dates (e.g. Saturn entered sidereal Aquarius on 17 Jan 2023,
  Jupiter entered Taurus on 1 May 2024) before committing.
- Readings are direct (no disclaimers or softening). Only four fixed limits: no date of death or
  remaining lifespan, never advise stopping medical treatment, no lottery/betting numbers, no
  prediction of an unborn child's sex. Doshas always come with their cancellation check (accuracy).
- Changes to the ephemeris settings (node, ayanamsa list, date range) require rebuilding
  `scripts/data/ephem.bin` with `scripts/build_ephem.py` and re-checking lite vs swe
  (`chart --engine lite` vs `--engine swe` should differ only in sunrise-based points by minutes).
- Birth profiles and the prediction log live in `~/.kundali/` (personal data) - never commit them.
- Do not add Narayana/Kalachakra dasha or the Sarvatobhadra chakra without a verified source for
  their rules; wrong dasha dates are worse than none.
- Eval workspaces (`*-workspace/`) are scratch output; do not commit them.
