"""Shared questionnaire navigation and server-side timing helpers."""

from datetime import datetime, timezone


SURVEY_STEPS = {
    'demographics1': 1,
    'demographics2': 2,
    'demographics3': 3,
    'social_capital1': 4,
    'social_capital2': 5,
    'social_capital3': 6,
    'social_capital4': 7,
    'politics_religion': 8,
    'risk_general': 9,
    'risk_staircase': 10,
    'civic_norms': 11,
    'associations': 12,
    'local_social_capital': 13,
}
SURVEY_TOTAL_STEPS = len(SURVEY_STEPS)


def survey_page_context(title=None, stage=None, subtitle=None):
    context = {}
    if title:
        context['page_title'] = title
    if subtitle:
        context['page_subtitle'] = subtitle
    if stage is not None:
        step = SURVEY_STEPS[stage]
        context.update(
            survey_progress_step=step,
            survey_progress_total=SURVEY_TOTAL_STEPS,
            survey_progress_percent=round(100 * step / SURVEY_TOTAL_STEPS),
        )
    return context


def can_continue_questionnaire(player):
    """Keep consent screen-outs out of every later app."""
    return not (
        player.participant.vars.get('screened_out', False)
        or player.participant.vars.get('attention_screened_out', False)
    )


def record_first_page_time(participant):
    """Record the first Intro render once, using the existing UTC ISO format."""
    if not participant.vars.get('time_first_page_utc'):
        participant.time_first_page_utc = datetime.now(timezone.utc).isoformat()


def record_questionnaire_start(participant):
    """Start Phase-1 timing once, immediately before Demographics1 is shown."""
    if not participant.vars.get('phase1_questionnaire_timing_started'):
        # oTree already has a built-in participant.time_started_utc column. Its
        # session-entry value is replaced here with the requested substantive
        # questionnaire start, rather than adding a duplicate custom field.
        participant.time_started_utc = datetime.now(timezone.utc).isoformat()
        participant.vars['phase1_questionnaire_timing_started'] = True


def record_questionnaire_end(participant):
    """Record Phase-1 completion and elapsed seconds once."""
    if participant.vars.get('phase1_questionnaire_timing_ended'):
        return
    ended = datetime.now(timezone.utc)
    participant.time_ended_utc = ended.isoformat()
    started = datetime.fromisoformat(participant.time_started_utc)
    participant.seconds_survey_time = max(0.0, (ended - started).total_seconds())
    first_page = participant.vars.get('time_first_page_utc')
    if first_page:
        participant.seconds_total_study_time = max(
            0.0, (ended - datetime.fromisoformat(first_page)).total_seconds()
        )
    participant.vars['phase1_questionnaire_timing_ended'] = True
