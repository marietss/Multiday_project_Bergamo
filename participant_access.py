"""Project page guard; native oTree room/initialization and IDs are unchanged."""
from otree.api import Page
from otree.templating import render


def has_participant_label(participant):
    value = participant.label
    return isinstance(value, str) and bool(value.strip())


class LabelRequiredPage(Page):
    def get(self):
        from survey_common import record_otree_entry_time
        record_otree_entry_time(self.participant)
        if not has_participant_label(self.participant):
            response = render('global/InvalidParticipantLink.html', {})
            response.status_code = 403
            return response
        return super().get()

    def post(self):
        if not has_participant_label(self.participant):
            response = render('global/InvalidParticipantLink.html', {})
            response.status_code = 403
            return response
        return super().post()
