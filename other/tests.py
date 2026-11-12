import re
from datetime import datetime

from otree.api import Bot, SubmissionMustFail

from intro import INCOME_CHOICES

from . import (
    AttentionCheck2,
    AttentionScreenOut,
    Associations,
    C,
    CivicNorms,
    LocalSocialCapital,
    PoliticsReligion,
    RiskGeneral,
    RiskStaircase1,
    RiskStaircase2,
    RiskStaircase3,
    RiskStaircase4,
    RiskStaircase5,
    RiskStaircaseRetry,
    calculate_associativita,
    calculate_civic_norms_score,
    calculate_risk_staircase_score,
)

INCOME_TEST_CODES = [code for code, label in INCOME_CHOICES]

CASES = [
    'path_a', 'path_b', 'path_c', 'path_d',
    'retry_lottery', 'retry_sure', 'retry_dont_know',
    'intermediate_dont_know', 'final_dont_know', 'screenout',
] + INCOME_TEST_CODES + ['attention_both_wrong']


# Each tuple after the initial/retry answers is (amount shown, submitted choice).
STAIRCASE_PLANS = {
    'path_a': (C.LOTTERY, None, [(120, C.LOTTERY), (140, C.LOTTERY), (150, C.LOTTERY), (155, C.SURE)]),
    'path_b': (C.LOTTERY, None, [(120, C.SURE), (100, C.SURE), (90, C.SURE), (85, C.LOTTERY)]),
    'path_c': (C.SURE, None, [(40, C.LOTTERY), (60, C.SURE), (50, C.LOTTERY), (55, C.SURE)]),
    'path_d': (C.SURE, None, [(40, C.SURE), (20, C.SURE), (10, C.SURE), (5, C.LOTTERY)]),
    'retry_lottery': (C.DONT_KNOW, C.LOTTERY, [(120, C.LOTTERY), (140, C.LOTTERY), (150, C.LOTTERY), (155, C.LOTTERY)]),
    'retry_sure': (C.DONT_KNOW, C.SURE, [(40, C.SURE), (20, C.SURE), (10, C.SURE), (5, C.SURE)]),
    'retry_dont_know': (C.DONT_KNOW, C.DONT_KNOW, []),
    'intermediate_dont_know': (C.LOTTERY, None, [(120, C.LOTTERY), (140, C.DONT_KNOW)]),
    'final_dont_know': (C.SURE, None, [(40, C.SURE), (20, C.SURE), (10, C.SURE), (5, C.DONT_KNOW)]),
}

EXPECTED_COMPLETE_SCORES = {
    'path_a': 31,
    'path_b': 18,
    'path_c': 11,
    'path_d': 2,
    'retry_lottery': 32,
    'retry_sure': 1,
}


class PlayerBot(Bot):
    cases = CASES

    def assert_staircase_screen(self, amount, step):
        assert '10 di 13' in self.participant_bot.html
        assert f'Situazione {step} di 5' in self.participant_bot.html
        assert f'pagamento sicuro di {amount} euro?' in self.participant_bot.html

    def play_round(self):
        assert calculate_risk_staircase_score(5, C.SURE) == 1
        assert calculate_risk_staircase_score(5, C.LOTTERY) == 2
        assert calculate_risk_staircase_score(55, C.SURE) == 11
        assert calculate_risk_staircase_score(55, C.LOTTERY) == 12
        assert calculate_risk_staircase_score(85, C.SURE) == 17
        assert calculate_risk_staircase_score(85, C.LOTTERY) == 18
        assert calculate_risk_staircase_score(155, C.SURE) == 31
        assert calculate_risk_staircase_score(155, C.LOTTERY) == 32
        assert calculate_risk_staircase_score(155, C.DONT_KNOW) is None

        civic_examples = [
            ([1, 1, 1, 1, 1], 50),
            ([10, 10, 10, 10, 10], 5),
            ([1, 2, 3, 4, 5], 40),
            ([5, 5, 5, 5, 5], 30),
        ]
        for raw_values, expected_score in civic_examples:
            values = dict(zip(CivicNorms.form_fields, raw_values))
            unchanged_values = values.copy()
            assert calculate_civic_norms_score(values) == expected_score
            assert values == unchanged_values
        assert calculate_civic_norms_score({
            'justify_false_benefits': 1,
            'justify_fare_evasion': 2,
            'justify_tax_evasion': 3,
            'justify_keep_found_money': 4,
            'justify_not_report_vehicle_damage': None,
        }) is None

        empty_associations = {
            field_name: False
            for field_name in Associations.form_fields
            if field_name != 'associations_none'
        }
        association_examples = [
            ({}, (False, False, False, 0, 0)),
            ({'political_party_member': True}, (True, False, True, 1, 0)),
            ({'volunteering_participated': True}, (False, True, True, 0, 1)),
            ({'sports_member': True, 'sports_participated': True}, (True, True, True, 1, 1)),
            ({'political_party_member': True, 'trade_union_participated': True}, (True, True, True, 1, 1)),
            ({
                'political_party_member': True,
                'sports_member': True,
                'professional_member': True,
                'volunteering_participated': True,
                'sports_participated': True,
            }, (True, True, True, 3, 2)),
        ]
        for selections, expected in association_examples:
            values = {**empty_associations, **selections}
            derived = calculate_associativita(values)
            actual = (
                derived['associativita_member'],
                derived['associativita_participation'],
                derived['associativita_any'],
                derived['associativita_member_count'],
                derived['associativita_participation_count'],
            )
            assert actual == expected

        if self.case == 'screenout':
            return

        assert '8 di 13' in self.participant_bot.html
        assert re.search(r'<h2[^>]*id="_otree-title"[^>]*>\s*</h2>', self.participant_bot.html)
        for researcher_title in [
            'Politica e religione',
            'Disponibilità a correre rischi',
            'Comportamenti e norme civiche',
            'Capitale sociale locale',
        ]:
            assert researcher_title not in self.participant_bot.html
        yield SubmissionMustFail(
            PoliticsReligion,
            dict(
                religiosity=3,
                political_position=4,
                political_no_position=True,
                worship_attendance='never',
            ),
        )
        assert 'scegli una sola modalità di risposta' in self.participant_bot.html
        if self.case == 'path_b':
            yield PoliticsReligion, dict(
                religiosity=3,
                political_position=0,
                worship_attendance='never',
            )
        else:
            yield PoliticsReligion, dict(
                religiosity=3,
                political_position=None,
                political_no_position=True,
                worship_attendance='never',
            )

        yield RiskGeneral, dict(general_risk_willingness=6)
        assert '9 di 13' in self.participant_bot.html
        yield SubmissionMustFail(AttentionCheck2, {})
        second_answer = 'six' if self.case in ['path_c', 'attention_both_wrong'] else 'cat'
        yield AttentionCheck2, dict(attention_check_2=second_answer)
        current = self.participant.get_player('other', 1)
        first = self.participant.get_player('intro', 1)
        expected_errors = 2 if self.case == 'attention_both_wrong' else int(self.case in ['path_b', 'path_c'])
        assert current.attention_check_2 == second_answer
        assert current.attention_check_2_failed == (second_answer != 'cat')
        assert current.attention_error == expected_errors
        for _ in range(2):
            self.participant_bot.client.get(self.participant_bot.url, allow_redirects=True)
        assert self.participant.get_player('other', 1).attention_error == expected_errors
        # Re-entry hooks assign rather than increment, tested without modifying
        # the live ORM objects used by subsequent browser submissions.
        from types import SimpleNamespace
        from intro import AttentionCheck1
        first_copy = SimpleNamespace(attention_check_1=first.attention_check_1)
        participant_copy = SimpleNamespace(vars={}, get_player=lambda *args: first_copy)
        second_copy = SimpleNamespace(attention_check_2=second_answer, participant=participant_copy)
        for _ in range(2):
            AttentionCheck1.before_next_page(first_copy, False)
            AttentionCheck2.before_next_page(second_copy, False)
            assert second_copy.attention_error == expected_errors
        if self.case == 'attention_both_wrong':
            assert self.participant.time_first_page_utc
            assert self.participant.vars.get('seconds_total_study_time') is None
            assert 'non è possibile' in self.participant_bot.html
            assert '9 di 13' in self.participant_bot.html
            assert 'attention-redirect' not in self.participant_bot.html
            yield SubmissionMustFail(AttentionScreenOut, {}, check_html=False)
            for page in [RiskStaircase1, RiskStaircase2, RiskStaircase3, RiskStaircase4,
                         RiskStaircase5, CivicNorms, Associations, LocalSocialCapital]:
                assert not page.is_displayed(current)
            assert current.field_maybe_none('risk_staircase_amount_1') is None
            return
        del current, first
        self.assert_staircase_screen(80, 1)
        assert 'Nelle prossime 5 situazioni ti chiederemo di scegliere' in self.participant_bot.html

        # A refresh is a read-only re-render of the same €80 state/path.
        refresh = self.participant_bot.client.get(self.participant_bot.url, allow_redirects=True)
        refresh_html = refresh.content.decode('utf-8')
        assert 'Situazione 1 di 5' in refresh_html
        assert 'pagamento sicuro di 80 euro?' in refresh_html
        assert self.player.risk_staircase_amount_1 == 80

        staircase_case = 'path_a' if self.case in INCOME_TEST_CODES else self.case
        first_attempt, first_retry, remaining = STAIRCASE_PLANS[staircase_case]
        if self.case == 'path_a':
            yield SubmissionMustFail(RiskStaircase1, dict())
            assert 'This field is required' not in self.participant_bot.html
            assert 'Questo campo è obbligatorio' in self.participant_bot.html
            self.assert_staircase_screen(80, 1)
        yield RiskStaircase1, dict(risk_staircase_first_attempt=first_attempt)

        if first_attempt == C.DONT_KNOW:
            self.assert_staircase_screen(80, 1)
            assert 'Ti riproponiamo la prima situazione.' in self.participant_bot.html
            assert self.player.risk_staircase_first_attempt == C.DONT_KNOW
            yield RiskStaircaseRetry, dict(risk_staircase_first_retry=first_retry)

        page_classes = [RiskStaircase2, RiskStaircase3, RiskStaircase4, RiskStaircase5]
        field_names = [
            'risk_staircase_choice_2',
            'risk_staircase_choice_3',
            'risk_staircase_choice_4',
            'risk_staircase_choice_5',
        ]
        for page_class, field_name, (expected_amount, choice) in zip(page_classes, field_names, remaining):
            step = int(field_name.rsplit('_', 1)[1])
            self.assert_staircase_screen(expected_amount, step)
            assert getattr(self.player, f'risk_staircase_amount_{step}') == expected_amount
            refresh = self.participant_bot.client.get(self.participant_bot.url, allow_redirects=True)
            refresh_html = refresh.content.decode('utf-8')
            assert f'Situazione {step} di 5' in refresh_html
            assert f'pagamento sicuro di {expected_amount} euro?' in refresh_html
            assert getattr(self.player, f'risk_staircase_amount_{step}') == expected_amount
            yield page_class, {field_name: choice}

        # Q24 follows both complete and early-termination paths.
        assert '11 di 13' in self.participant_bot.html
        player = self.player
        assert player.risk_staircase_first_attempt == first_attempt
        assert player.field_maybe_none('risk_staircase_first_retry') == first_retry

        complete_cases = [
            'path_a', 'path_b', 'path_c', 'path_d', 'retry_lottery', 'retry_sure',
            *INCOME_TEST_CODES,
        ]
        if self.case in complete_cases:
            assert player.risk_staircase_completed_steps == 5
            assert player.risk_staircase_terminated_nonresponse is False
            amounts = [getattr(player, f'risk_staircase_amount_{step}') for step in range(1, 6)]
            assert len([amount for amount in amounts if amount is not None]) == 5
            assert len(set(amounts)) == 5
            expected_score = 31 if self.case in INCOME_TEST_CODES else EXPECTED_COMPLETE_SCORES[self.case]
            assert player.risk_staircase_derived_measure == expected_score
        elif self.case == 'retry_dont_know':
            assert player.field_maybe_none('risk_staircase_derived_measure') is None
            assert player.risk_staircase_completed_steps == 1
            assert player.risk_staircase_terminated_nonresponse is True
            assert player.risk_staircase_choice_1 == C.DONT_KNOW
            assert player.field_maybe_none('risk_staircase_amount_2') is None
            assert player.field_maybe_none('risk_staircase_choice_2') is None
        elif self.case == 'intermediate_dont_know':
            assert player.field_maybe_none('risk_staircase_derived_measure') is None
            assert player.risk_staircase_completed_steps == 3
            assert player.risk_staircase_terminated_nonresponse is True
            assert player.risk_staircase_choice_3 == C.DONT_KNOW
            assert player.field_maybe_none('risk_staircase_amount_4') is None
            assert player.field_maybe_none('risk_staircase_choice_4') is None
            assert player.field_maybe_none('risk_staircase_amount_5') is None
            assert player.field_maybe_none('risk_staircase_choice_5') is None
        else:
            assert self.case == 'final_dont_know'
            assert player.risk_staircase_completed_steps == 5
            assert player.risk_staircase_terminated_nonresponse is True
            assert player.risk_staircase_amount_5 == 5
            assert player.risk_staircase_choice_5 == C.DONT_KNOW
            assert player.field_maybe_none('risk_staircase_derived_measure') is None

        civic_test_values = {
            'path_a': ([1, 1, 1, 1, 1], 50),
            'path_b': ([10, 10, 10, 10, 10], 5),
            'path_c': ([1, 2, 3, 4, 5], 40),
            'path_d': ([5, 5, 5, 5, 5], 30),
        }
        raw_civic_values, expected_civic_score = civic_test_values.get(
            self.case,
            ([1, 2, 3, 4, 5], 40),
        )
        civic_submission = dict(zip(CivicNorms.form_fields, raw_civic_values))
        if self.case == 'path_a':
            incomplete_submission = civic_submission.copy()
            incomplete_submission.pop('justify_not_report_vehicle_damage')
            yield SubmissionMustFail(CivicNorms, incomplete_submission)
            assert self.player.field_maybe_none('civic_norms_score') is None

        yield CivicNorms, civic_submission
        assert expected_civic_score == calculate_civic_norms_score(civic_submission)
        assert 'Se nessuna delle organizzazioni indicate si applica a te' in self.participant_bot.html
        yield SubmissionMustFail(Associations, dict())
        assert 'Seleziona almeno una risposta' in self.participant_bot.html
        yield SubmissionMustFail(
            Associations,
            dict(volunteering_member=True, associations_none=True),
        )
        association_submissions = {
            'path_a': dict(political_party_member=True),
            'path_b': dict(associations_none=True),
            'path_c': dict(volunteering_participated=True),
            'path_d': dict(sports_member=True, sports_participated=True),
            'retry_lottery': dict(political_party_member=True, trade_union_participated=True),
            'retry_sure': dict(
                political_party_member=True,
                sports_member=True,
                professional_member=True,
                volunteering_participated=True,
                sports_participated=True,
            ),
        }
        yield Associations, association_submissions.get(
            self.case,
            dict(volunteering_member=True, volunteering_participated=True),
        )
        assert 'In che modo?' in self.participant_bot.html
        if self.case == 'path_a':
            for invalid_details in ['', ' ', 'A', '12', 'A1']:
                yield SubmissionMustFail(
                    LocalSocialCapital,
                    dict(
                        local_collective_action='yes',
                        local_collective_action_details=invalid_details,
                        perceived_altruism=6,
                        perceived_fairness=7,
                    ),
                )
            assert 'almeno 2 lettere' in self.participant_bot.html

        if self.case == 'path_b':
            yield LocalSocialCapital, dict(
                local_collective_action='no',
                local_collective_action_details='Questo testo deve essere ignorato',
                perceived_altruism=6,
                perceived_fairness=7,
            )
        else:
            yield LocalSocialCapital, dict(
                local_collective_action='yes',
                local_collective_action_details='Collaborazione nel quartiere',
                perceived_altruism=6,
                perceived_fairness=7,
            )
        assert '13 di 13' in self.participant_bot.html
        assert self.participant.time_ended_utc
        assert self.participant.seconds_survey_time >= 0
        assert self.participant.vars['phase1_questionnaire_timing_ended'] is True
        end_time = self.participant.time_ended_utc
        first_time = datetime.fromisoformat(self.participant.time_first_page_utc)
        start_time = datetime.fromisoformat(self.participant.time_started_utc)
        assert first_time <= start_time <= datetime.fromisoformat(end_time)
        total_time = self.participant.seconds_total_study_time
        survey_time = self.participant.seconds_survey_time
        assert total_time >= survey_time >= 0
        assert total_time == (datetime.fromisoformat(end_time) - first_time).total_seconds()
        self.participant_bot.client.get(self.participant_bot.url, allow_redirects=True)
        assert self.participant.time_ended_utc == end_time
        assert self.participant.seconds_total_study_time == total_time
        assert self.participant.seconds_survey_time == survey_time
