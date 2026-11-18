# Phase 1 questionnaire data map

## Linking Phase 1 and Phase 2 with the recruitment ID

Use the native oTree room URL:
`/room/my_room/?participant_label=U12345` (replace the room and ID as needed).
An active Phase-1 session must be assigned to the room. The standard room
welcome/start flow forwards the query parameter and stores the received value
unchanged in `participant.label`; no new study ID is generated. URL-encode IDs
when constructing links so special characters survive normal URL decoding.

`participant.label` is included in native per-app CSV and wide CSV exports.
Phase 2 must receive that same recruitment ID through its own
`participant_label` parameter and use `participant.label` as the cross-phase
linking key. Do not substitute `participant.code`, `id_in_session`, or the
retained legacy `unique_id` field. The existing Phase-1 `unique_id` is not
automatically populated or used for matching.

`settings.ROOMS` defines `my_room` without `use_secure_urls=True` and without a
participant-label file, so no hash is required by its current configuration.
If a future room enables secure URLs, use oTree's participant-specific URL
including its generated `hash`; do not bypass that validation. Two distinct IDs
and repeated entry/export behavior are covered by `test_room_participant_label.py`.

All project pages inherit `participant_access.LabelRequiredPage`. Both GET and
POST check that the stored `participant.label` is a non-empty string containing
at least one non-whitespace character, before rendering questions or processing
form submissions. Trimming is used only to test validity; the ID is never
modified. Missing/None/empty/whitespace-only IDs receive the local Italian
`global/InvalidParticipantLink.html` page (HTTP 403, no form, no continue link,
no provider redirect). Neither survey timing nor a terminal classification is
started. Use the complete recruitment room link containing a valid
`participant_label` to enter. An ID in an ordinary form field or page query is
not accepted as a replacement for the stored label. This also protects direct
session links and ongoing pages independently of room settings.

CLI bot fixtures explicitly supply `TEST-ID-<case>` before their first request;
this is test-only setup. No production code generates a replacement ID. Existing
development sessions without labels are deliberately blocked by this guard.

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
`attention_screenout_url` in settings.py controls its Maximiles Quality redirect.
This URL is now supplied; see terminal routing below.
Neither check adds a substantive stage; the total remains 13.

## Maximiles terminal routing

The four supplied URLs are defined once in `settings.MAXIMILES_REDIRECT_URLS`
and copied into the `initial_survey` session configuration:

| Outcome | Session configuration key | URL |
|---|---|---|
| Complete / Target 1 | `complete_redirect_url` | `https://survey.maximiles.com/static-complete?p=177137_7285c59a` |
| Quality | `attention_screenout_url` | `https://survey.maximiles.com/static-quality?p=177137` |
| Speeder | `speeder_redirect_url` | `https://survey.maximiles.com/static-speeder?p=177137` |
| Screen-out (consent not provided) | `screenout_redirect_url` | `https://survey.maximiles.com/static-screenout?p=177137_17a5978d` |

For sessions created before these configuration keys existed, absent/empty
values fall back to these same supplied project URLs. No session-data migration
is needed, and the previous empty Quality URL cannot prevent the redirect.

`terminal_redirects.finalize_terminal_redirect` chooses and saves exactly one
outcome/URL in `participant.vars['phase1_terminal_redirect']`. Re-entry returns
the stored decision. No recruitment label or additional URL parameters are added.

### Terminal status and reason

`participant.terminal_status` and `participant.terminal_reason` are declared in
`PARTICIPANT_FIELDS` and stored in the existing participant vars database column.
No SQL schema migration is required. Both are assigned server-side by
`finalize_terminal_redirect`, together with the outcome/URL snapshot, and remain
unchanged on later calls, refreshes or re-entry. They are not form fields and
are never populated from browser input. They are blank before a terminal
decision. Consent refusal now receives its own explicit Screen-out outcome.

`participant.terminal_time_utc` is assigned in that same central function at
the first terminal classification, including Screen-out and early Quality.
It uses `utc_timestamps.utc_isoformat(datetime.now(timezone.utc))`. The existing
stored-decision guard returns before any timestamp assignment on subsequent
calls. This event time is not the time of clicking the external fallback link.
The field is persisted in participant vars and appears in the wide CSV.

| terminal_status | terminal_reason | Meaning |
|---|---|---|
| `complete` | `completed_normally` | Valid completion, 180–1200 seconds inclusive, not Quality |
| `speeder` | `speeder_under_180` | Valid completion below 180 seconds, not Quality |
| `quality` | `quality_attention_checks` | Both existing attention checks failed |
| `quality` | `quality_over_1200` | The submission time guard found more than 1200 seconds |
| `screenout` | `consent_not_provided` | One or both consent declarations not affirmed; survey not started |

Both fields appear as `participant.terminal_status` and
`participant.terminal_reason` in the native **wide/all-apps CSV**, alongside
`participant.label`, `participant.terminal_time_utc` and
`participant.seconds_survey_time`. The existing nested
snapshot also stores `reason`; its outcome and URL remain the routing source.

Reasons preserve the **first assigned terminal decision**. If a single call
receives both causes before any decision exists, `quality_attention_checks`
takes precedence. In the existing real submission sequence, the elapsed-time
guard runs before the per-page hook. If the second check is submitted after
1200 seconds, the time guard assigns `quality_over_1200` first and that reason
is not overwritten when the two-check failure total is then calculated.
The original attention flags/`other.Player.attention_error` and the exported
`seconds_survey_time` retain the evidence for both causes: error total 2 plus
time greater than 1200 shows that both criteria were met, without another field.
This adds metadata only; routing precedence, URLs and all thresholds are unchanged.

Precedence is Quality, then Speeder, then Complete. Quality uses only
`attention_error == 2`, derived from the two existing blue questions (the colour
question requiring `dog` and the 3 × 2 question requiring `cat`), OR
`seconds_survey_time > 1200`. Two attention failures are finalized in
`AttentionCheck2.before_next_page`; the existing early-stop point and dedicated
AttentionScreenOut page remain. One failure alone permits continuation.

Every substantive/attention page has the shared `timed_questionnaire_page`
submission guard. After validation, but before choosing the next page, it
recalculates elapsed UTC seconds from the original Demographics1 timestamp and
updates the existing `seconds_survey_time`. More than 1200 seconds sets
`participant.vars['survey_time_limit_exceeded']` and saves the immutable Quality
destination. Exactly 1200 seconds still permits continuation. Existing per-page
hooks continue to preserve raw/derived responses.

No GET, refresh, re-entry or client timer can trigger this limit while a
participant is working on a page. The participant's next valid Continue/Avanti
submission triggers Quality. Early exits skip subsequent questionnaire pages
to AttentionScreenOut. If that page is already behind the participant (during
Q23 or later), subsequent questions are skipped to the existing End page,
which displays the shared Quality message/link instead of completion content.
No new questionnaire pages or progress stages are introduced. Both terminal
pages block further submissions after a time-limit termination.

For a valid completion, `LocalSocialCapital.before_next_page` first calls the
existing server-side timing finalizer and then chooses Quality for more than
1200 seconds, Speeder for less than 180 seconds, otherwise Complete. Exactly
180 and exactly 1200 seconds are Complete if both checks were not failed.
This is the substantive questionnaire interval from first Demographics1 render
through successful Q28 submission; Intro/Structure/Consent reading time is
excluded. `seconds_total_study_time` continues to include Intro reading time,
but is not the Speeder criterion. Both durations and UTC timestamps remain
stored and are available in the native wide CSV export for audit. An early
Quality exit preserves the elapsed `seconds_survey_time` without fabricating
`time_ended_utc` or `seconds_total_study_time`. If the final Q28 form itself
passes validation after 1200 seconds, its completion timestamps are recorded
normally, but the outcome is Quality.

End, AttentionScreenOut and consent ScreenOut render a shared fallback link.
Complete displays a confirmation that Phase 1 is finished and that participants
will be contacted by email from Monday 23 November 2026 for Phase 2, with an
automatic redirect after **7 seconds**. Other terminal outcomes retain the
1.5-second redirect and do not promise successful completion/Phase-2 contact.
The delay does not extend the saved survey duration or terminal event time.
The redirect remains guarded against duplicate automatic/manual dispatch.
Missing consent is the
only current Maximiles Screen-out criterion. There is no quota-full condition.

### Consent Screen-out before questionnaire entry

The third page is `intro.Consent`, following Intro and Structure. Its existing
fields are `consent_read` (Boolean checkbox, “Ho letto le informazioni sullo
studio.”) and `consent_accept` (string radio field with `accept` / `decline`,
“Acconsento” / “Non acconsento”). Their texts and raw coding are unchanged.
Both fields allow unselected submission so the server can process refusal:
only `consent_read == True` AND `consent_accept == 'accept'` permits entry.
Unchecked/missing `consent_read` is stored as false; unselected `consent_accept`
is blank. Explicit `decline` remains stored as `decline`.

`Consent.before_next_page` sets `screened_out` and finalizes
`screenout / consent_not_provided` before the redirect when either affirmation
is missing. This decision precedes and is separate from Quality/Speed/Complete.
The existing `intro.ScreenOut` page now uses the shared Maximiles automatic
redirect/fallback, and rejects further Continue submissions. The survey timer
has not started, no Speeder/Quality duration rule is evaluated, and no completed
timing values are fabricated. `time_first_page_utc` remains stored. Subsequent
questionnaire pages are disabled. Once assigned, the destination/status/reason
cannot be replaced by another outcome. No other Screen-out condition is active.

Raw consent values remain in native app exports and in wide CSV as
`intro.1.player.consent_read` and `intro.1.player.consent_accept`; wide CSV also
contains terminal status/reason, participant.label and the blank survey duration.

`test_maximiles_redirects.py` tests the boundary, precedence, re-entry, label,
and timing-export behavior, including the 1199/1200/1201-second boundaries and
real HTTP early/late time-limit exits, in an isolated in-memory database. The app bot tests
also check the actual terminal-page destination after normal and Quality paths.

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
| Q8 occupation follow-up | `intro.Player.occupation_category` |
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

## Education, employment and occupation

All three are required single-choice demographic variables. “Non so” and
“Preferisco non rispondere”, where offered, are valid answers. Occupation is
a socioeconomic covariate only and is not included in any index.

`education_level`: “Qual è il livello di istruzione più alto che hai completato?”

| Code | Label |
|---|---|
| `doctorate` | Dottorato di ricerca o titolo equivalente |
| `masters_or_equivalent` | Laurea magistrale o specialistica, laurea a ciclo unico, laurea del vecchio ordinamento o titolo equivalente |
| `bachelors_its_or_equivalent` | Laurea triennale, diploma universitario, diploma ITS Academy o titolo equivalente |
| `upper_secondary_diploma_or_ifts` | Diploma di scuola secondaria di secondo grado (maturità o equivalente) o certificato di specializzazione tecnica superiore (IFTS) |
| `upper_secondary_vocational_no_maturita` | Qualifica o diploma professionale di livello secondario superiore, senza maturità |
| `lower_secondary` | Licenza di scuola secondaria di primo grado (scuola media) |
| `vocational_initiation_school` | Licenza di scuola di avviamento professionale (percorso triennale dopo la scuola elementare) |
| `primary_or_none` | Licenza di scuola primaria (scuola elementare) o nessun titolo di studio |
| `dont_know` | Non so |
| `prefer_not_to_answer` | Preferisco non rispondere |

`employment_status`: “Quale delle seguenti opzioni descrive meglio la tua attuale condizione occupazionale?”

| Code | Label |
|---|---|
| `employee_full_time` | Lavoratore/lavoratrice dipendente a tempo pieno |
| `employee_part_time` | Lavoratore/lavoratrice dipendente a tempo parziale |
| `self_employed` | Lavoratore/lavoratrice autonomo/a o libero/a professionista |
| `unemployed_seeking` | Disoccupato/a, in cerca di lavoro |
| `not_employed_not_seeking` | Non occupato/a e non in cerca di lavoro |
| `parental_leave` | In congedo parentale |
| `student` | Studente/studentessa |
| `retired` | Pensionato/a |
| `homemaker_caregiver` | Casalingo/a o caregiver |
| `other` | Altro |
| `prefer_not_to_answer` | Preferisco non rispondere |

`occupation_category`: “Quale delle seguenti opzioni descrive meglio la tua professione attuale o, se non lavori attualmente, l'ultima svolta?”

| Code | Label |
|---|---|
| `manager` | Dirigente |
| `professional` | Professione intellettuale, scientifica o di elevata specializzazione |
| `technician` | Professione tecnica |
| `clerical` | Impiegato/a di ufficio |
| `services_sales` | Addetto/a ai servizi o alle vendite |
| `skilled_agriculture_forestry_fishing` | Lavoratore/lavoratrice qualificato/a dell'agricoltura, delle foreste o della pesca |
| `craft_skilled_worker` | Artigiano/a o operaio/a specializzato/a |
| `plant_machine_operator_assembler` | Conduttore/conduttrice di impianti o macchinari / addetto/a al montaggio |
| `elementary_occupation` | Professione non qualificata |
| `armed_forces` | Professione nelle forze armate |
| `never_worked` | Non ho mai svolto un’attività lavorativa |
| `dont_know` | Non so |
| `prefer_not_to_answer` | Preferisco non rispondere |

All four items remain on Demographics3, ordered education, employment,
occupation, income. The occupation follow-up retains the historical Q8/Q9
documentation references; no later question numbers or stages are shifted.

### Legacy data and migration

`scripts/migrate_occupation_category.py` adds a nullable column to an existing
SQLite database and creates a timestamped backup. Legacy occupation stays NULL.
This schema migration itself does not remap education/employment. Fresh databases
receive the column from the model; PostgreSQL migration SQL is in the script.

The active development database has now been normalized to the finalized code
system. Production analysis should use only that finalized code system.
The following historical labels explain the conversion decisions:

| Old education code | Original meaning |
|---|---|
| `lower_secondary_or_less` | Licenza media inferiore (scuola media) o titolo inferiore |
| `upper_secondary` | Diploma di scuola superiore (Maturità o equivalente) |
| `bachelors` | Laurea triennale (o diploma universitario di 3 anni) |
| `masters_or_postgraduate` | Laurea magistrale/specialistica (o laurea vecchio ordinamento) e/o Master post-laurea |
| `doctorate` | Dottorato di ricerca; retained for the new doctorate/equivalent category |

### Development data normalization (2026-11-12)

There were 24 participant records at migration time (the original 20 plus four
subsequently created records). All were preserved. A timestamped SQLite backup
was created before any values were updated:
`db.sqlite3.before-demographic-normalization-20261112T211337245569Z.bak`.

| Field | Old code | Final value | Rows changed |
|---|---|---|---:|
| Employment | `not_working_not_seeking` | `not_employed_not_seeking` | 1 |
| Education | `bachelors` | `bachelors_its_or_equivalent` | 2 |
| Education | `upper_secondary` | `upper_secondary_diploma_or_ifts` | 1 |
| Education | `lower_secondary_or_less` | NULL | 1 |
| Education | `masters_or_postgraduate` | NULL | 1 |

The old lower-secondary-or-less category does not distinguish lower secondary
from lower education. The actual old `masters_or_postgraduate` category included
“e/o Master post-laurea”, so a master's/specialist degree cannot be inferred.
These two ambiguous responses were set to NULL rather than guessed. There was
no separate combined doctorate/postgraduate-Master response in the stored data.

Already-finalized employment values `employee_full_time` (2 rows) and
`unemployed_seeking` (2 rows) were retained unchanged; 19 employment values were
already NULL. Three education responses now use non-NULL finalized codes and
21 are NULL (19 originally missing plus the two ambiguous responses).
No obsolete non-NULL education or employment codes remain.

All 24 occupation values remain NULL, including all original 20 participants;
occupation cannot be reconstructed from the legacy questionnaire. No other
columns or tables were changed by the normalization.

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

All **project-owned** timestamps use the shared `utc_timestamps.utc_isoformat`
serializer: `YYYY-MM-DDTHH:MM:SS.ffffff+00:00` (six microsecond digits, aware UTC).
Naive datetimes are rejected by this serializer. Both durations are seconds.

### Timestamp audit before this change

An actual wide export of the 32 development participants was inspected:

| Field/event | Owner/storage | Previous format | In native wide CSV? |
|---|---|---|---|
| `time_first_page_utc` | Project, participant vars | Aware UTC ISO with `+00:00` | Yes (4 populated) |
| `time_ended_utc` | Project, participant vars | Aware UTC ISO with `+00:00` | Yes (6 populated) |
| `time_started_utc` | Native participant column, reassigned once by project at Demographics1 | Mixed: naive UTC native entry / aware UTC ISO questionnaire start | Yes (8 populated) |
| `seconds_survey_time`, `seconds_total_study_time` | Project, participant vars | Numeric durations, not timestamps | Yes |
| `_last_page_timestamp`, `_last_request_timestamp`, `_timeout_expiration_time` | oTree internal participant timing | Native epoch values | No |
| Session `_created` | oTree native session timestamp | Native representation | No |
| Page-completion `epoch_time_completed`, queued task `epoch_time`, chat `timestamp` | Native framework event records, not study event fields | Native epoch values | Not wide; separate framework exports where supported |

The native entry value is created by oTree using `datetime.utcnow()` without
tzinfo. oTree internals are not modified. For Screen-out/blocked links that
never reach Demographics1, that original column can still be naive in wide
CSV; use its new aware project mirror `time_otree_entry_utc` for uniform analysis.
That mirror interprets a naive value as UTC only because the native code
explicitly defines it as UTC. The existing substantive-start reassignment is
preserved. Internal native epoch fields are unchanged.

### Current fields

| Participant field | Meaning |
|---|---|
| `time_first_page_utc` | First arrival on Intro, recorded by `Intro.vars_for_template` through `record_first_page_time`. |
| `time_otree_entry_utc` | ISO UTC copy of native initialization time, captured once at first project-page GET before Demographics1 replaces the native value. |
| `time_started_utc` | First arrival on Demographics1; substantive questionnaire start. |
| `time_ended_utc` | Final questionnaire completion after Q28 passes validation. |
| `terminal_time_utc` | First assignment of terminal status/reason; available also for early Quality and consent Screen-out. |
| `seconds_total_study_time` | Intro to final completion: end minus first-page timestamp. |
| `seconds_survey_time` | Elapsed seconds from Demographics1, updated at valid submissions and frozen at final completion or an early terminal Quality exit. |

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

All project event fields above are directly available as `participant.<field>`
in wide CSV. No risky retrospective normalization or SQL schema migration was
performed: existing event timestamps/labels are not rewritten. A new native
entry mirror is not invented for a legacy participant already past the start
hook, and an unknown past terminal time is not backfilled with the current time.
New terminal decisions always receive `terminal_time_utc`. The test suite writes
a five-outcome synthetic wide export to `/tmp/phase1_timestamps_wide_test.csv`
and re-parses all values to verify explicit UTC offsets and the ID/status/reason.
