"""Shared questionnaire navigation and server-side timing helpers."""

from datetime import datetime, timezone
from functools import wraps
from participant_access import has_participant_label
from utc_timestamps import utc_isoformat


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
    return has_participant_label(player.participant) and not (
        player.participant.vars.get('screened_out', False)
        or player.participant.vars.get('attention_screened_out', False)
        or player.participant.vars.get('survey_time_limit_exceeded', False)
    )


def record_otree_entry_time(participant):
    """ISO mirror of native entry time, without changing oTree's original value.

    oTree explicitly creates this native datetime in UTC without tzinfo.
    Only this documented native value is interpreted as UTC when naive.
    Do not reconstruct the entry from an already-replaced questionnaire start.
    """
    if (participant.vars.get('time_otree_entry_utc')
            or participant.vars.get('phase1_questionnaire_timing_started')):
        return
    if participant.time_started_utc:
        entered = datetime.fromisoformat(participant.time_started_utc)
        if entered.tzinfo is None:
            entered = entered.replace(tzinfo=timezone.utc)
        participant.time_otree_entry_utc = utc_isoformat(entered)


def record_first_page_time(participant):
    """Record the first Intro render once, using the existing UTC ISO format."""
    if not participant.vars.get('time_first_page_utc'):
        participant.time_first_page_utc = utc_isoformat(datetime.now(timezone.utc))


def record_questionnaire_start(participant):
    """Start Phase-1 timing once, immediately before Demographics1 is shown."""
    if not has_participant_label(participant):
        return
    if not participant.vars.get('phase1_questionnaire_timing_started'):
        # oTree already has a built-in participant.time_started_utc column. Its
        # session-entry value is replaced here with the requested substantive
        # questionnaire start, rather than adding a duplicate custom field.
        participant.time_started_utc = utc_isoformat(datetime.now(timezone.utc))
        participant.vars['phase1_questionnaire_timing_started'] = True


def record_questionnaire_end(participant):
    """Record Phase-1 completion and elapsed seconds once."""
    if participant.vars.get('phase1_questionnaire_timing_ended'):
        return
    ended = datetime.now(timezone.utc)
    participant.time_ended_utc = utc_isoformat(ended)
    started = datetime.fromisoformat(participant.time_started_utc)
    participant.seconds_survey_time = max(0.0, (ended - started).total_seconds())
    first_page = participant.vars.get('time_first_page_utc')
    if first_page:
        participant.seconds_total_study_time = max(
            0.0, (ended - datetime.fromisoformat(first_page)).total_seconds()
        )
    participant.vars['phase1_questionnaire_timing_ended'] = True


def check_questionnaire_time_limit(player):
    """Check only on a validated submission, using the original start timestamp.

    Interim elapsed time is exported in the existing seconds_survey_time field.
    An early Quality exit does not fabricate final completion timestamps.
    """
    from terminal_redirects import MAX_QUESTIONNAIRE_SECONDS, finalize_terminal_redirect

    participant = player.participant
    if (not participant.vars.get('phase1_questionnaire_timing_started')
            or participant.vars.get('phase1_terminal_redirect') is not None):
        return
    started = datetime.fromisoformat(participant.time_started_utc)
    participant.seconds_survey_time = max(0.0, (datetime.now(timezone.utc) - started).total_seconds())
    if participant.seconds_survey_time > MAX_QUESTIONNAIRE_SECONDS:
        participant.vars['survey_time_limit_exceeded'] = True
        finalize_terminal_redirect(participant, player.session.config, attention_error=None)


def timed_questionnaire_page(page_class):
    """Add the shared submission guard while preserving the page's own hook.

    oTree runs before_next_page after form validation/population and before
    choosing the next page. GET, refresh and invalid forms never run this guard.
    """
    original = getattr(page_class, 'before_next_page', None)

    def before_next_page(player, timeout_happened):
        check_questionnaire_time_limit(player)
        if original is not None:
            original(player, timeout_happened)

    if original is not None:
        before_next_page = wraps(original)(before_next_page)
    page_class.before_next_page = staticmethod(before_next_page)
    return page_class
