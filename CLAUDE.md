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
- Guardrails are part of the product: no death/lifespan predictions, health = "doctor se salah
  lein", gemstones are never a cure, Manglik/Kaal Sarp with cancellations and no fear language,
  Avakahada varna is not caste.
- Eval workspaces (`*-workspace/`) are scratch output; do not commit them.
