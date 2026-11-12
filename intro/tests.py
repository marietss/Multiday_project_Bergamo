import re

from otree.api import Bot, SubmissionMustFail

from . import (
    AttentionCheck1,
    Consent,
    Demographics1,
    Demographics2,
    Demographics3,
    INCOME_CHOICES,
    Intro,
    Structure,
    _has_at_least_two_letters,
    influential_place_error_message,
)

INCOME_TEST_CODES = [code for code, label in INCOME_CHOICES]
REMOVED_INCOME_CODES = [
    'income_09_4000_4999',
    'income_10_5000_6999',
    'income_11_7000_10000',
    'income_12_gt_10000',
]

CASES = [
    'path_a', 'path_b', 'path_c', 'path_d',
    'retry_lottery', 'retry_sure', 'retry_dont_know',
    'intermediate_dont_know', 'final_dont_know', 'screenout',
] + INCOME_TEST_CODES + ['attention_both_wrong']


class PlayerBot(Bot):
    cases = CASES

    def play_round(self):
        # Unicode-safe minimum-text validation covers the requested Q3/Q4
        # boundary cases without restricting punctuation or accented letters.
        for invalid_value in ['', ' ', 'A', '12', 'A1']:
            assert not _has_at_least_two_letters(invalid_value)
        for valid_value in ['AB', "L'Aquila"]:
            assert _has_at_least_two_letters(valid_value)
        for invalid_value in ['', '1', 'A']:
            assert not _has_at_least_two_letters(invalid_value)
            assert influential_place_error_message(None, invalid_value)
        for valid_value in ['Roma, Italia', 'Parigi - Francia']:
            assert _has_at_least_two_letters(valid_value)
            assert influential_place_error_message(None, valid_value) is None

        first_page_time = self.participant.time_first_page_utc
        assert first_page_time
        for url in [self.participant_bot.url, f'/InitializeParticipant/{self.participant.code}']:
            response = self.participant_bot.client.get(url, allow_redirects=True)
            assert response.status_code == 200
            assert self.participant.time_first_page_utc == first_page_time
        # Explicit re-render follows the same server hook as revisiting Intro.
        Intro.vars_for_template(self.player)
        assert self.participant.time_first_page_utc == first_page_time
        yield Intro
        assert 'Importante' in self.participant_bot.html
        yield Structure
        if self.case == 'screenout':
            yield Consent, dict(consent_read=True, consent_accept='decline')
            assert self.participant.time_first_page_utc == first_page_time
            assert self.participant.vars.get('seconds_total_study_time') is None
            return
        yield Consent, dict(consent_read=True, consent_accept='accept')
        assert '1 di 13' in self.participant_bot.html
        assert re.search(r'<h2[^>]*id="_otree-title"[^>]*>\s*</h2>', self.participant_bot.html)
        assert 'Domande sociodemografiche' not in self.participant_bot.html
        start_time = self.participant.time_started_utc
        assert start_time
        assert first_page_time <= start_time
        self.participant_bot.client.get(self.participant_bot.url, allow_redirects=True)
        assert self.participant.time_started_utc == start_time
        assert self.participant.vars['phase1_questionnaire_timing_started'] is True
        if self.case == 'path_a':
            yield SubmissionMustFail(Demographics1, dict())
            assert 'This field is required' not in self.participant_bot.html
            assert 'Questo campo è obbligatorio' in self.participant_bot.html
            for invalid_municipality in ['', ' ', 'A', '12', 'A1', 'Bologna']:
                yield SubmissionMustFail(
                    Demographics1,
                    dict(sex_at_birth='female', age=18, current_municipality=invalid_municipality),
                )
            assert 'Seleziona un comune dall’elenco.' in self.participant_bot.html
            yield SubmissionMustFail(Demographics1, dict(
                sex_at_birth='female', age=18, current_municipality='Roma',
                current_municipality_istat_code='037006'))
        yield SubmissionMustFail(
            Demographics1,
            dict(sex_at_birth='female', age=17, current_municipality='Bologna'),
        )
        assert self.participant.time_started_utc == start_time
        assert 'Il numero deve essere compreso tra 18 e 100.' in self.participant_bot.html
        boundary_age = 18 if self.case == 'path_a' else 100
        yield Demographics1, dict(sex_at_birth='female', age=boundary_age, current_municipality='Bologna', current_municipality_istat_code='037006')
        assert self.player.current_municipality == 'Bologna'
        assert self.player.current_municipality_istat_code == '037006'
        assert '2 di 13' in self.participant_bot.html
        if self.case == 'path_a':
            for invalid_place in ['', '1', 'A']:
                yield SubmissionMustFail(
                    Demographics2,
                    dict(
                        influential_place=invalid_place,
                        marital_status='unmarried_not_cohabiting',
                        number_of_children='0',
                    ),
                )
            assert 'almeno 2 lettere' in self.participant_bot.html
        yield Demographics2, dict(
            influential_place='Bologna, Italia',
            marital_status='unmarried_not_cohabiting',
            number_of_children='0',
        )
        assert '3 di 13' in self.participant_bot.html
        income_html = self.participant_bot.html
        for code, label in INCOME_CHOICES:
            assert f'value="{code}"' in income_html
            assert label in income_html
        for removed_code in REMOVED_INCOME_CODES:
            assert removed_code not in income_html
        income_code = self.case if self.case in INCOME_TEST_CODES else 'income_04_1500_1999'
        yield Demographics3, dict(
            education_level='masters_or_postgraduate',
            employment_status='employee_full_time',
            net_monthly_income=income_code,
        )
        assert self.player.net_monthly_income == income_code
        assert '3 di 13' in self.participant_bot.html
        yield SubmissionMustFail(AttentionCheck1, {})
        first_answer = 'blue' if self.case in ['path_b', 'attention_both_wrong'] else 'dog'
        yield AttentionCheck1, dict(attention_check_1=first_answer)
        first = self.participant.get_player('intro', 1)
        assert first.attention_check_1 == first_answer
        assert first.attention_check_1_failed == (first_answer != 'dog')
        assert '4 di 13' in self.participant_bot.html
        assert not self.participant.vars.get('attention_screened_out', False)
