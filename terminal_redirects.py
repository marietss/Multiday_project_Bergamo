"""Server-side, single-outcome Phase-1 routing, including consent refusal."""
import math
from datetime import datetime, timezone
from participant_access import has_participant_label
from utc_timestamps import utc_isoformat
from settings import MAXIMILES_REDIRECT_URLS

SPEEDER_THRESHOLD_SECONDS = 180
MAX_QUESTIONNAIRE_SECONDS = 1200


def finalize_terminal_redirect(participant, config, *, attention_error, completed=False,
                               consent_not_provided=False):
    """Persist one decision; refreshes/re-entry return that same destination.

    Quality uses the two-check error total OR more than 1200 survey seconds.
    Both duration rules use the existing substantive questionnaire timer.
    """
    stored = participant.vars.get('phase1_terminal_redirect')
    if stored is not None:
        return stored
    if not has_participant_label(participant):
        return None
    seconds = participant.vars.get('seconds_survey_time')
    if consent_not_provided:
        outcome, key = 'screenout', 'screenout_redirect_url'
        reason = 'consent_not_provided'
    elif attention_error == 2 or (seconds is not None and seconds > MAX_QUESTIONNAIRE_SECONDS):
        outcome, key = 'quality', 'attention_screenout_url'
        reason = 'quality_attention_checks' if attention_error == 2 else 'quality_over_1200'
    elif completed:
        if not participant.vars.get('phase1_questionnaire_timing_ended'):
            raise ValueError('Completion timing must be finalized before terminal routing.')
        seconds = participant.seconds_survey_time
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError('Invalid server-side questionnaire duration.')
        if seconds < SPEEDER_THRESHOLD_SECONDS:
            outcome, key = 'speeder', 'speeder_redirect_url'
            reason = 'speeder_under_180'
        else:
            outcome, key = 'complete', 'complete_redirect_url'
            reason = 'completed_normally'
    else:
        return None
    # oTree snapshots config at session creation: sessions already created
    # before this update may have missing keys or the old empty Quality URL.
    result = {'outcome': outcome, 'reason': reason,
              'url': config.get(key) or MAXIMILES_REDIRECT_URLS[outcome]}
    participant.vars['phase1_terminal_redirect'] = result
    # Declared in PARTICIPANT_FIELDS: persisted server-side and exported as
    # participant.terminal_status / participant.terminal_reason in wide CSV.
    participant.vars['terminal_status'] = outcome
    participant.vars['terminal_reason'] = reason
    participant.vars['terminal_time_utc'] = utc_isoformat(datetime.now(timezone.utc))
    return result
