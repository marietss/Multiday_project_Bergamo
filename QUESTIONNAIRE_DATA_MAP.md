# Phase 1 questionnaire data map

## Approved wording revisions

- Municipality (Q3): “In quale comune vivi attualmente?” (already the displayed wording).
  Uses the searchable ISTAT selector documented below.
- Influential place (Q4): “Tra i luoghi in cui hai vissuto durante l’infanzia o
  l’adolescenza, quale ritieni abbia influenzato maggiormente il tuo attuale modo
  di vivere e di pensare?” Free text and its two-Unicode-letter rule are preserved.
- Phase-2 email sentence: “a partire da lunedì prossimo, per 5 giorni consecutivi,
  riceverai una mail con le istruzioni per prendere una decisione.”
  Consent uses the corresponding formal wording: “la prossima settimana, per
  cinque giorni consecutivi, riceverà ogni giorno una mail con le istruzioni per
  prendere una decisione.”
- Donation (Q11): “Immagina la seguente situazione: oggi hai ricevuto 700 euro
  per pura fortuna e senza sforzo. Quanto di questa somma doneresti per una giusta causa?”
- Q23 introduction: “Nelle prossime 5 situazioni ti chiederemo di scegliere tra
  una somma di denaro sicura e una lotteria in cui hai il 50% di probabilità di
  ricevere 150 euro e il 50% di non ricevere nulla. L'importo del pagamento sicuro
  cambierà da una situazione all'altra.”
- Q24 tax evasion: “Non pagare volontariamente, del tutto o in parte, le tasse dovute.”

These wording revisions do not change raw coding, scales, branching or scoring.

## Attention checks

`intro.Player.attention_check_1` stores `blue` (Azzurro), `green` (Verde),
`dog` (Cane), or `red` (Rosso). Its nullable Boolean
`attention_check_1_failed` is set to `answer != 'dog'` after valid submission.
This page follows Demographics3, retaining progress 3/13.

`other.Player.attention_check_2` stores `six` (6), `five` (5), `cat` (Gatto),
or `eight` (8). Its nullable Boolean `attention_check_2_failed` is set to
`answer != 'cat'`. This page follows RiskGeneral, before Q23, retaining 9/13.

After the second valid submission, nullable integer `other.Player.attention_error`
is assigned `int(attention_check_1_failed) + int(attention_check_2_failed)`:
0 means both correct, 1 means one incorrect, and 2 means both incorrect.
It remains NULL until both checks have been answered. The total is assigned
deterministically, never incremented. A first failure alone does not screen out.

Two failures set `participant.vars['attention_screened_out']` and lead to the
dedicated AttentionScreenOut page immediately before Q23. All later questionnaire
pages are disabled. This state is separate from consent screen-out. The terminal
page has no continue button and rejects POSTs. Session configuration key
`attention_screenout_url` in settings.py controls its redirect. The empty
development default leaves the participant on this page without redirecting.
TODO(Bilendi): supply the dedicated attention-screenout URL before production.
Neither check adds a substantive stage; the total remains 13.

Categorical fields store the machine-readable codes defined in each app's
`Player` model; the Italian text is only the participant-facing label.

| Question | Database field(s) |
|---|---|
| Q1 | `intro.Player.sex_at_birth` |
| Q2 | `intro.Player.age` |
| Q3 | `intro.Player.current_municipality`, `intro.Player.current_municipality_istat_code` |
| Q4 | `intro.Player.influential_place` |
| Q5 | `intro.Player.marital_status` |
| Q6 | `intro.Player.number_of_children` |
| Q7 | `intro.Player.education_level` |
| Q8 | `intro.Player.employment_status` |
| Q9 | `intro.Player.net_monthly_income` |
| Q10 | `s_c.Player.generalized_trust` |
| Q11 | `s_c.Player.unexpected_money_donation` |
| Q12 | `s_c.Player.reciprocity_gift_value` |
| Q13 | `s_c.Player.best_intentions` |
| Q14 | `s_c.Player.positive_reciprocity` |
| Q15 | `s_c.Player.revenge` |
| Q16 | `s_c.Player.punish_personal_unfairness` |
| Q17 | `s_c.Player.punish_unfairness_to_others` |
| Q18 | `s_c.Player.unconditional_charitable_giving` |
| Q19 | `other.Player.religiosity` |
| Q20 | `other.Player.political_position`, `other.Player.political_no_position` |
| Q21 | `other.Player.worship_attendance` |
| Q22 | `other.Player.general_risk_willingness` |
| Q23 | `other.Player.risk_staircase_amount_1` … `_5`, `risk_staircase_choice_1` … `_5`, `risk_staircase_first_attempt`, `risk_staircase_first_retry`, `risk_staircase_completed_steps`, `risk_staircase_terminated_nonresponse`, `risk_staircase_derived_measure` |
| Q24a | `other.Player.justify_false_benefits` |
| Q24b | `other.Player.justify_fare_evasion` |
| Q24c | `other.Player.justify_tax_evasion` |
| Q24d | `other.Player.justify_keep_found_money` |
| Q24e | `other.Player.justify_not_report_vehicle_damage` |
| Q24 derived CIVIC | `other.Player.civic_norms_score` |
| Q25 | The 15 raw Boolean fields and five derived fields listed below |
| Q26 | `other.Player.local_collective_action`; conditional follow-up `other.Player.local_collective_action_details` |
| Q27 | `other.Player.perceived_altruism` |
| Q28 | `other.Player.perceived_fairness` |

Q12 `reciprocity_gift_value` is an integer storing the selected gift's actual
euro value: `0`, `4`, `8`, `12`, `16`, `20`, or `24`.

Q25 uses independent `_member` and `_participated` Boolean fields for each
organisation prefix: `political_party`, `trade_union`, `volunteering`,
`civic_environment`, `sports`, `cultural_recreational`, and `professional`.
The separate exclusive field is `associations_none`.

The seven included organisation categories are political parties; trade
unions; volunteering organisations/groups; environmental, civil-rights, or
peace organisations; sports organisations/groups; cultural, recreational, or
other associations; and professional or trade associations. Sports are
therefore included in all Q25 derived measures.

The nullable Boolean derived fields are:

- `associativita_member`: true when at least one `_member` field is selected;
- `associativita_participation`: true when at least one `_participated` field
  is selected;
- `associativita_any`: true when either of the preceding indicators is true.

The nullable integer fields `associativita_member_count` and
`associativita_participation_count` count selected organisation categories of
each type and range from 0 to 7. Higher counts indicate engagement across more
organisation categories. Selecting `associations_none` produces false for all
three indicators and zero for both counts. All 15 raw Q25 fields remain stored
unchanged.

## Q3 ISTAT municipality selection

The sole authoritative source is `data/istat/comuni_istat_2026-10-16.xlsx`,
sheet `Codici statistici e denominazio`. Run
`python3 scripts/build_istat_comuni.py` to produce the bundled
`_static/global/istat_comuni.json`; `--check` verifies byte-deterministic output
and every source name/code/province. No workbook parsing or live ISTAT requests
occur at questionnaire runtime. Commit the source, script and generated JSON.

All 7,894 source rows are represented, with 7,894 unique codes and no missing
names, codes or province abbreviations. Duplicate names (Samone, Livo, Peglio,
Castro, San Teodoro) remain separate records. Display is `Comune (SIGLA)`;
province abbreviation disambiguates results and is not stored as a new field.
Search ignores case, accents and punctuation without automatically selecting.

`current_municipality` stores exactly the official `Comune` spelling.
`current_municipality_istat_code` stores the six-character string from
`Codice Comune (alfanumerico)`, retaining leading zeroes. Both must match the
same bundled record server-side. Editing the visible text clears the selection.
Typed-but-unselected text is rejected with “Seleziona un comune dall’elenco.”
The influential-place question remains free text with its existing validation.

For existing SQLite databases, stop the server and run
`python3 scripts/migrate_municipality_code.py db.sqlite3`. This additive,
idempotent migration backs up the database and preserves all legacy names,
leaving their new codes NULL. No legacy name is automatically harmonized.
The script also documents the corresponding PostgreSQL ALTER TABLE statement.

## Q9 income codes (unchanged)

The ordered codes and labels are:

1. `income_01_lt_500` — Meno di €500
2. `income_02_500_999` — Da €500 a €999
3. `income_03_1000_1499` — Da €1.000 a €1.499
4. `income_04_1500_1999` — Da €1.500 a €1.999
5. `income_05_2000_2499` — Da €2.000 a €2.499
6. `income_06_2500_2999` — Da €2.500 a €2.999
7. `income_07_3000_3499` — Da €3.000 a €3.499
8. `income_08_3500_3999` — Da €3.500 a €3.999
9. `income_09_4000_6999` — Da €4.000 a €6.999
10. `income_10_ge_7000` — €7.000 o più
11. `prefer_not_to_answer` — Preferisco non rispondere

## Q23 adaptive staircase

The five `amount_n` fields store the certain amounts actually shown. The five
`choice_n` fields use `lottery`, `sure`, or `dont_know`.
`risk_staircase_first_attempt` always stores the original €80 response. If it
is `dont_know`, `risk_staircase_first_retry` stores the repeated €80 response;
otherwise the retry stays NULL. `risk_staircase_completed_steps` counts the
number of numbered situations answered, excluding the retry screen.
`risk_staircase_terminated_nonresponse` identifies early termination.
For a completed fifth decision with final certain amount `A`, let
`k = (A - 5) / 10`. `risk_staircase_derived_measure` stores `2*k + 1` after a
final `sure` choice or `2*k + 2` after a final `lottery` choice, yielding an
integer from 1 to 32. It remains NULL after any `dont_know` termination. The
raw staircase amounts and choices remain authoritative and unchanged.

## Q24 CIVIC norms-of-cooperation score

The five raw Q24 variables remain stored unchanged on their original 1–10
scale, where 1 means “Mai giustificato” and 10 means “Sempre giustificato”:
`justify_false_benefits`, `justify_fare_evasion`, `justify_tax_evasion`,
`justify_keep_found_money`, and `justify_not_report_vehicle_damage`.

Each item is reverse-coded as `11 - raw_item`. The nullable integer field
`civic_norms_score` is calculated only after all five items pass validation:

`civic_norms_score = 55 - sum(the five raw Q24 items)`

Its range is 5–50, with higher values indicating stronger norms of civic
cooperation. Missing items are not imputed; if any item is unexpectedly
missing, the score remains NULL.

## Phase-1 timing

All timestamps use server-side UTC ISO 8601 strings. Both durations are seconds.

| Participant field | Meaning |
|---|---|
| `time_first_page_utc` | First arrival on Intro, recorded by `Intro.vars_for_template` through `record_first_page_time`. |
| `time_started_utc` | First arrival on Demographics1; substantive questionnaire start. |
| `time_ended_utc` | Final questionnaire completion after Q28 passes validation. |
| `seconds_total_study_time` | Intro to final completion: end minus first-page timestamp. |
| `seconds_survey_time` | Demographics1 to final completion: end minus questionnaire start. |

`record_questionnaire_end`, called by `LocalSocialCapital.before_next_page`,
calculates both durations from the same stored end timestamp. Durations are
clamped to zero if a clock anomaly would otherwise make them negative. The
existing completion guard prevents refresh/re-entry from overwriting them.
Intro's stored timestamp is also never overwritten on refresh or re-entry.
Consent and attention screen-outs retain their Intro timestamp but receive no
completed-study duration. If an older participant has no Intro timestamp, no
total duration is fabricated.

oTree's built-in `participant.time_started_utc` is overwritten exactly once
when `Demographics1.vars_for_template` first runs. This excludes the Intro,
Structure, and Consent pages. `participant.time_ended_utc` and
`participant.seconds_survey_time` are populated server-side by
`LocalSocialCapital.before_next_page`, after the final questionnaire form has
passed validation. Refreshes do not overwrite either timestamp.
