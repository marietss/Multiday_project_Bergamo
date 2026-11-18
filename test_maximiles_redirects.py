"""Run: OTREE_IN_MEMORY=1 OTREE_EPHEMERAL=1 python3 -m unittest -v test_maximiles_redirects

Uses only an empty in-memory database. No network redirects are followed.
"""
import csv
import io
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch


class MaximilesRedirectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import otree.database as database
        if not database.IN_MEMORY or not os.environ.get('OTREE_EPHEMERAL'):
            raise RuntimeError('Use the isolated in-memory invocation documented above.')
        database.ephemeral_connection = database.engine.connect()
        database.init_orm()

    def participant(self):
        from otree.session import create_session
        session = create_session('initial_survey', num_participants=1)
        participant = session.get_participants()[0]
        participant.label = 'U00012345-CaSe'
        return participant

    def checks(self, participant, first_answer='dog', second_answer='cat'):
        from intro import AttentionCheck1
        from other import AttentionCheck2
        first = participant.get_player('intro', 1)
        second = participant.get_player('other', 1)
        first.attention_check_1 = first_answer
        second.attention_check_2 = second_answer
        with patch('survey_common.datetime', wraps=datetime) as clock:
            if participant.vars.get('phase1_questionnaire_timing_started'):
                clock.now.return_value = datetime.fromisoformat(participant.time_started_utc)
            AttentionCheck1.before_next_page(first, False)
            AttentionCheck2.before_next_page(second, False)
        return second

    def timing(self, participant):
        import survey_common
        start = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)
        with patch('survey_common.datetime', wraps=datetime) as clock:
            clock.now.return_value = start - timedelta(seconds=120)
            survey_common.record_first_page_time(participant)
            clock.now.return_value = start
            survey_common.record_questionnaire_start(participant)
        return start

    def complete(self, participant, seconds, first_answer='dog', second_answer='cat'):
        from other import LocalSocialCapital, End
        start = self.timing(participant)
        player = self.checks(participant, first_answer, second_answer)
        player.local_collective_action = 'no'
        with patch('survey_common.datetime', wraps=datetime) as clock:
            clock.now.return_value = start + timedelta(seconds=seconds)
            LocalSocialCapital.before_next_page(player, False)
        return player, End.vars_for_template(player)

    def test_completion_and_speed_boundaries(self):
        from settings import MAXIMILES_REDIRECT_URLS
        for seconds, outcome in [(179, 'speeder'), (180, 'complete'), (239, 'complete'), (301, 'complete'),
                                 (1199, 'complete'), (1200, 'complete'), (1201, 'quality')]:
            with self.subTest(seconds=seconds):
                participant = self.participant()
                _, context = self.complete(participant, seconds)
                self.assertEqual(participant.seconds_survey_time, seconds)
                self.assertEqual(participant.seconds_total_study_time, seconds + 120)
                self.assertEqual(participant.vars['phase1_terminal_redirect']['outcome'], outcome)
                reason = {'complete': 'completed_normally', 'speeder': 'speeder_under_180',
                          'quality': 'quality_over_1200'}[outcome]
                self.assertEqual(participant.terminal_status, outcome)
                self.assertEqual(participant.terminal_reason, reason)
                parsed_terminal = datetime.fromisoformat(participant.terminal_time_utc)
                self.assertEqual(parsed_terminal.utcoffset(), timedelta(0))
                self.assertTrue(participant.terminal_time_utc.endswith('+00:00'))
                self.assertEqual(context['terminal_redirect_url'], MAXIMILES_REDIRECT_URLS[outcome])
                self.assertEqual(context['terminal_complete'], outcome == 'complete')
                self.assertEqual(context['terminal_redirect_delay_ms'], 7000 if outcome == 'complete' else 1500)
                self.assertEqual(participant.label, 'U00012345-CaSe')
                self.assertNotEqual(context['terminal_redirect_url'], MAXIMILES_REDIRECT_URLS['screenout'])

    def test_each_single_error_continues(self):
        for first, second in [('blue', 'cat'), ('dog', 'six')]:
            with self.subTest(first=first, second=second):
                participant = self.participant()
                player, _ = self.complete(participant, 300, first, second)
                self.assertEqual(player.attention_error, 1)
                self.assertEqual(participant.vars['phase1_terminal_redirect']['outcome'], 'complete')
                self.assertEqual(participant.terminal_status, 'complete')
                self.assertEqual(participant.terminal_reason, 'completed_normally')

    def test_quality_has_priority_and_stops_before_q23(self):
        from other import AttentionScreenOut, RiskStaircase1, End
        from settings import MAXIMILES_REDIRECT_URLS
        from terminal_redirects import finalize_terminal_redirect
        participant = self.participant()
        self.timing(participant)
        player = self.checks(participant, 'blue', 'six')
        self.assertEqual(player.attention_error, 2)
        self.assertTrue(AttentionScreenOut.is_displayed(player))
        self.assertFalse(RiskStaircase1.is_displayed(player))
        self.assertFalse(End.is_displayed(player))
        self.assertIsNone(participant.vars.get('time_ended_utc'))
        self.assertEqual(participant.seconds_survey_time, 0)
        context = AttentionScreenOut.vars_for_template(player)
        self.assertEqual(context['terminal_redirect_url'], MAXIMILES_REDIRECT_URLS['quality'])
        # Even a later competing completion/speed signal cannot issue a new
        # destination for someone already terminated for Quality.
        participant.seconds_survey_time = 179
        repeated = finalize_terminal_redirect(participant, player.session.config,
                                              attention_error=2, completed=True)
        self.assertEqual(repeated, participant.vars['phase1_terminal_redirect'])
        self.assertEqual(repeated['outcome'], 'quality')
        self.assertEqual(participant.terminal_status, 'quality')
        self.assertEqual(participant.terminal_reason, 'quality_attention_checks')
        self.assertEqual(participant.label, 'U00012345-CaSe')

    def test_refresh_and_reentry_keep_timestamps_and_destination(self):
        from intro import Intro, Demographics1
        from other import LocalSocialCapital, End
        from otree.export import export_wide
        participant = self.participant()
        player, _ = self.complete(participant, 179)
        timestamps = (participant.time_first_page_utc, participant.time_started_utc,
                      participant.time_ended_utc, participant.seconds_survey_time,
                      participant.seconds_total_study_time)
        destination = dict(participant.vars['phase1_terminal_redirect'])
        terminal_time = participant.terminal_time_utc
        status_reason = (participant.terminal_status, participant.terminal_reason)
        for _ in range(2):
            Intro.vars_for_template(participant.get_player('intro', 1))
            Demographics1.vars_for_template(participant.get_player('intro', 1))
            LocalSocialCapital.before_next_page(player, False)
            End.vars_for_template(player)
        self.assertEqual(timestamps, (participant.time_first_page_utc, participant.time_started_utc,
                         participant.time_ended_utc, participant.seconds_survey_time,
                         participant.seconds_total_study_time))
        self.assertEqual(participant.vars['phase1_terminal_redirect'], destination)
        self.assertEqual(participant.terminal_time_utc, terminal_time)
        self.assertEqual((participant.terminal_status, participant.terminal_reason), status_reason)
        self.assertEqual(participant.label, 'U00012345-CaSe')
        output = io.StringIO()
        export_wide(output, session_code=player.session.code)
        rows = list(csv.DictReader(io.StringIO(output.getvalue())))
        self.assertEqual(rows[0]['participant.label'], 'U00012345-CaSe')
        self.assertEqual(float(rows[0]['participant.seconds_survey_time']), 179)
        self.assertEqual(rows[0]['participant.terminal_status'], 'speeder')
        self.assertEqual(rows[0]['participant.terminal_reason'], 'speeder_under_180')
        self.assertEqual(rows[0]['participant.terminal_time_utc'], terminal_time)

    def test_no_routing_before_completion_or_quality(self):
        from terminal_redirects import finalize_terminal_redirect
        participant = self.participant()
        player = self.checks(participant)
        self.assertIsNone(finalize_terminal_redirect(participant, player.session.config,
                                                     attention_error=0))
        self.assertNotIn('phase1_terminal_redirect', participant.vars)
        self.assertIsNone(participant.vars.get('terminal_status'))
        self.assertIsNone(participant.vars.get('terminal_reason'))

    def test_existing_session_config_uses_supplied_urls(self):
        from settings import MAXIMILES_REDIRECT_URLS
        from terminal_redirects import finalize_terminal_redirect
        for errors, seconds, outcome in [(2, 179, 'quality'), (0, 179, 'speeder'), (0, 180, 'complete')]:
            participant = self.participant()
            participant.vars['phase1_questionnaire_timing_ended'] = True
            participant.seconds_survey_time = seconds
            result = finalize_terminal_redirect(
                participant, {'attention_screenout_url': ''},
                attention_error=errors, completed=True,
            )
            self.assertEqual(result['url'], MAXIMILES_REDIRECT_URLS[outcome])

    def test_all_questionnaire_submissions_have_the_time_guard(self):
        import intro
        import s_c
        import other
        excluded = {'Intro', 'Structure', 'Consent', 'ScreenOut', 'AttentionScreenOut', 'End'}
        for app in [intro, s_c, other]:
            for page in app.page_sequence:
                if page.__name__ not in excluded:
                    self.assertIn('before_next_page', page.__dict__, page.__name__)

    def test_http_continue_boundaries_refresh_and_early_exit(self):
        from starlette.testclient import TestClient
        from otree.asgi import app
        from otree.models import Participant
        from otree.database import db
        for elapsed in [1199, 1200, 1201]:
            with self.subTest(elapsed=elapsed):
                participant = self.participant()
                pk, code = participant.id, participant.code
                db.commit()
                del participant
                client = TestClient(app)
                start = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)
                with patch('survey_common.datetime', wraps=datetime) as clock:
                    clock.now.return_value = start
                    response = client.get('/InitializeParticipant/' + code, allow_redirects=True)
                    for data in [{}, {}, {'consent_read': 'True', 'consent_accept': 'accept'}]:
                        response = client.post(response.url, data=data, allow_redirects=True)
                        self.assertEqual(response.status_code, 200)
                    self.assertIn('/Demographics1/', response.url)
                    original_start = Participant.objects_get(id=pk).time_started_utc
                    clock.now.return_value = start + timedelta(seconds=elapsed)
                    # A GET after 20 minutes must leave the participant on the
                    # same page, with no terminal state until a valid POST.
                    response = client.get(response.url, allow_redirects=True)
                    response = client.get('/InitializeParticipant/' + code, allow_redirects=True)
                    self.assertIn('/Demographics1/', response.url)
                    self.assertNotIn('phase1_terminal_redirect', Participant.objects_get(id=pk).vars)
                    self.assertEqual(Participant.objects_get(id=pk).time_started_utc, original_start)
                    response = client.post(response.url, data={
                        'sex_at_birth': 'female', 'age': '18',
                        'current_municipality': 'Bologna', 'current_municipality_istat_code': '037006',
                        'terminal_status': 'complete', 'terminal_reason': 'completed_normally',
                    }, allow_redirects=True)
                current = Participant.objects_get(id=pk)
                self.assertEqual(current.label, 'U00012345-CaSe')
                self.assertEqual(current.seconds_survey_time, elapsed)
                if elapsed <= 1200:
                    self.assertIn('/Demographics2/', response.url)
                    self.assertNotIn('phase1_terminal_redirect', current.vars)
                else:
                    self.assertIn('/AttentionScreenOut/', response.url)
                    self.assertEqual(current.vars['phase1_terminal_redirect']['outcome'], 'quality')
                    self.assertEqual(current.terminal_status, 'quality')
                    self.assertEqual(current.terminal_reason, 'quality_over_1200')
                    self.assertIn('https://survey.maximiles.com/static-quality?p=177137', response.text)
                    self.assertIsNone(current.vars.get('time_ended_utc'))
                    self.assertIsNone(current.vars.get('seconds_total_study_time'))
                    self.assertEqual(current.get_player('intro', 1).current_municipality, 'Bologna')
                del current

    def test_http_late_exit_after_quality_page_and_correct_attention(self):
        from starlette.testclient import TestClient
        from otree.asgi import app
        from otree.models import Participant
        from otree.database import db
        participant = self.participant()
        pk, code = participant.id, participant.code
        db.commit()
        del participant
        client = TestClient(app)
        forms = [
            ('Intro', {}), ('Structure', {}),
            ('Consent', {'consent_read': 'True', 'consent_accept': 'accept'}),
            ('Demographics1', {'sex_at_birth': 'female', 'age': 18,
                              'current_municipality': 'Bologna', 'current_municipality_istat_code': '037006'}),
            ('Demographics2', {'influential_place': 'Roma', 'marital_status': 'married', 'number_of_children': '0'}),
            ('Demographics3', {'education_level': 'doctorate', 'employment_status': 'student',
                              'occupation_category': 'never_worked', 'net_monthly_income': 'income_01_lt_500'}),
            ('AttentionCheck1', {'attention_check_1': 'dog'}),
            ('SocialCapital1', {'generalized_trust': 'need_to_be_careful', 'unexpected_money_donation': 0}),
            ('SocialCapital2', {'reciprocity_gift_value': 0}),
            ('SocialCapital3', {'best_intentions': 1, 'positive_reciprocity': 1, 'revenge': 1}),
            ('SocialCapital4', {'punish_personal_unfairness': 1, 'punish_unfairness_to_others': 1,
                               'unconditional_charitable_giving': 1}),
            ('PoliticsReligion', {'religiosity': 1, 'political_no_position': 'True', 'worship_attendance': 'never'}),
            ('RiskGeneral', {'general_risk_willingness': 1}),
            ('AttentionCheck2', {'attention_check_2': 'cat'}),
            ('RiskStaircase1', {'risk_staircase_first_attempt': 'sure'}),
        ]
        start = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)
        with patch('survey_common.datetime', wraps=datetime) as clock:
            clock.now.return_value = start
            response = client.get('/InitializeParticipant/' + code, allow_redirects=True)
            for page_name, data in forms:
                self.assertIn('/' + page_name + '/', response.url)
                response = client.post(response.url, data=data, allow_redirects=True)
                self.assertEqual(response.status_code, 200)
            self.assertIn('/RiskStaircase2/', response.url)
            clock.now.return_value = start + timedelta(seconds=1201)
            response = client.get(response.url, allow_redirects=True)
            self.assertIn('/RiskStaircase2/', response.url)
            self.assertNotIn('phase1_terminal_redirect', Participant.objects_get(id=pk).vars)
            response = client.post(response.url, data={'risk_staircase_choice_2': 'sure'}, allow_redirects=True)
            self.assertIn('/End/', response.url)
            self.assertIn('https://survey.maximiles.com/static-quality?p=177137', response.text)
            self.assertNotIn('Grazie per aver completato', response.text)
            self.assertNotIn('risposte fornite alle domande di controllo', response.text)
            db.expire_all()
            current = Participant.objects_get(id=pk)
            self.assertEqual(current.get_player('other', 1).attention_error, 0)
            self.assertEqual(current.seconds_survey_time, 1201)
            self.assertEqual(current.terminal_status, 'quality')
            self.assertEqual(current.terminal_reason, 'quality_over_1200')
            self.assertEqual(current.label, 'U00012345-CaSe')
            frozen = dict(current.vars['phase1_terminal_redirect'])
            del current
            clock.now.return_value = start + timedelta(seconds=3000)
            response = client.get('/InitializeParticipant/' + code, allow_redirects=True)
            self.assertIn('/End/', response.url)
            db.expire_all()
            current = Participant.objects_get(id=pk)
            self.assertEqual(current.seconds_survey_time, 1201)
            self.assertEqual(current.vars['phase1_terminal_redirect'], frozen)
            self.assertIsNone(current.vars.get('time_ended_utc'))
            from terminal_redirects import finalize_terminal_redirect
            for simulated_duration in [179, 300]:
                # The saved terminal outcome wins over a competing criterion.
                current.seconds_survey_time = simulated_duration
                result = finalize_terminal_redirect(current, {}, attention_error=0, completed=True)
                self.assertEqual(result, frozen)
                self.assertEqual(current.terminal_status, 'quality')
                self.assertEqual(current.terminal_reason, 'quality_over_1200')

    def test_both_quality_causes_preserve_first_reason_and_raw_evidence(self):
        from intro import AttentionCheck1
        from other import AttentionCheck2
        participant = self.participant()
        start = self.timing(participant)
        first = participant.get_player('intro', 1)
        second = participant.get_player('other', 1)
        first.attention_check_1 = 'blue'
        second.attention_check_2 = 'six'
        with patch('survey_common.datetime', wraps=datetime) as clock:
            clock.now.return_value = start
            AttentionCheck1.before_next_page(first, False)
            clock.now.return_value = start + timedelta(seconds=1201)
            AttentionCheck2.before_next_page(second, False)
        # Existing time guard runs before the second-check hook and assigns
        # Quality first. The hook still saves both raw failures afterward.
        self.assertEqual(participant.terminal_status, 'quality')
        self.assertEqual(participant.terminal_reason, 'quality_over_1200')
        self.assertEqual(second.attention_error, 2)
        self.assertTrue(first.attention_check_1_failed)
        self.assertTrue(second.attention_check_2_failed)
        self.assertGreater(participant.seconds_survey_time, 1200)
        from terminal_redirects import finalize_terminal_redirect
        finalize_terminal_redirect(participant, {}, attention_error=2, completed=True)
        self.assertEqual(participant.terminal_reason, 'quality_over_1200')
        simultaneous = self.participant()
        simultaneous.seconds_survey_time = 1201
        finalize_terminal_redirect(simultaneous, {}, attention_error=2, completed=True)
        self.assertEqual(simultaneous.terminal_status, 'quality')
        self.assertEqual(simultaneous.terminal_reason, 'quality_attention_checks')

    def test_metadata_for_all_outcomes_is_persisted_and_exported(self):
        from otree.database import db
        from otree.models import Participant
        from otree.export import export_wide
        scenarios = [
            (300, 'dog', 'cat', 'complete', 'completed_normally'),
            (179, 'dog', 'cat', 'speeder', 'speeder_under_180'),
            (1201, 'dog', 'cat', 'quality', 'quality_over_1200'),
            (179, 'blue', 'six', 'quality', 'quality_attention_checks'),
        ]
        for seconds, first, second, status, reason in scenarios:
            with self.subTest(status=status, reason=reason):
                participant = self.participant()
                player, _ = self.complete(participant, seconds, first, second)
                pk, session_code = participant.id, player.session.code
                db.commit()
                db.expire_all()
                saved = Participant.objects_get(id=pk)
                self.assertEqual(saved.terminal_status, status)
                self.assertEqual(saved.terminal_reason, reason)
                terminal_time = saved.terminal_time_utc
                self.assertEqual(datetime.fromisoformat(terminal_time).utcoffset(), timedelta(0))
                output = io.StringIO()
                export_wide(output, session_code=session_code)
                rows = list(csv.DictReader(io.StringIO(output.getvalue())))
                self.assertEqual(rows[0]['participant.terminal_status'], status)
                self.assertEqual(rows[0]['participant.terminal_reason'], reason)
                self.assertEqual(rows[0]['participant.terminal_time_utc'], terminal_time)
                self.assertEqual(rows[0]['participant.label'], 'U00012345-CaSe')
                self.assertIn('participant.seconds_survey_time', rows[0])

    def test_http_consent_combinations_screenout_metadata_and_export(self):
        from starlette.testclient import TestClient
        from otree.asgi import app
        from otree.database import db
        from otree.models import Participant
        from otree.export import export_wide
        from intro import Consent, Intro, Structure, Demographics1
        from terminal_redirects import finalize_terminal_redirect
        from settings import MAXIMILES_REDIRECT_URLS
        import intro
        import s_c
        import other

        self.assertEqual(intro.page_sequence[:3], [Intro, Structure, Consent])
        # Include both an explicit refusal and an entirely unanswered second
        # item. All missing-consent cases must be processed, not form errors.
        for read, decision in [(True, 'accept'), (True, None), (False, 'accept'),
                               (False, None), (True, 'decline'), (False, 'decline')]:
            with self.subTest(read=read, decision=decision):
                participant = self.participant()
                pk, code = participant.id, participant.code
                db.commit()
                del participant
                client = TestClient(app)
                start = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)
                with patch('survey_common.datetime', wraps=datetime) as clock:
                    clock.now.return_value = start
                    response = client.get('/InitializeParticipant/' + code, allow_redirects=True)
                    for _ in range(2):
                        response = client.post(response.url, data={}, allow_redirects=True)
                    self.assertIn('/Consent/', response.url)
                    # Even very long information/consent reading is not a
                    # questionnaire timing violation.
                    clock.now.return_value = start + timedelta(hours=2)
                    data = {}
                    if read:
                        data['consent_read'] = 'True'
                    if decision is not None:
                        data['consent_accept'] = decision
                    response = client.post(response.url, data=data, allow_redirects=True)
                self.assertEqual(response.status_code, 200)
                db.expire_all()
                current = Participant.objects_get(id=pk)
                player = current.get_player('intro', 1)
                session_code = player.session.code
                self.assertEqual(player.consent_read, read)
                self.assertEqual(player.field_maybe_none('consent_accept') or None, decision)
                self.assertEqual(current.label, 'U00012345-CaSe')
                if read and decision == 'accept':
                    self.assertIn('/Demographics1/', response.url)
                    self.assertTrue(current.vars['phase1_questionnaire_timing_started'])
                    self.assertNotIn('phase1_terminal_redirect', current.vars)
                else:
                    self.assertIn('/ScreenOut/', response.url)
                    self.assertEqual(current.terminal_status, 'screenout')
                    self.assertEqual(current.terminal_reason, 'consent_not_provided')
                    self.assertFalse(current.vars.get('phase1_questionnaire_timing_started', False))
                    for name in ['seconds_survey_time', 'seconds_total_study_time', 'time_ended_utc']:
                        self.assertIsNone(current.vars.get(name))
                    self.assertIn(MAXIMILES_REDIRECT_URLS['screenout'], response.text)
                    self.assertNotIn(MAXIMILES_REDIRECT_URLS['quality'], response.text)
                    frozen = dict(current.vars['phase1_terminal_redirect'])
                    frozen_terminal_time = current.terminal_time_utc
                    self.assertEqual(datetime.fromisoformat(frozen_terminal_time).utcoffset(), timedelta(0))
                    for errors, seconds in [(0, 179), (0, 300), (2, 1201)]:
                        current.seconds_survey_time = seconds
                        result = finalize_terminal_redirect(current, {}, attention_error=errors, completed=True)
                        self.assertEqual(result, frozen)
                        self.assertEqual(current.terminal_status, 'screenout')
                        self.assertEqual(current.terminal_reason, 'consent_not_provided')
                        self.assertEqual(current.terminal_time_utc, frozen_terminal_time)
                    # Undo only the simulated competing timing inputs above.
                    current.vars.pop('seconds_survey_time')
                    Consent.before_next_page(player, False)
                    self.assertEqual(current.vars['phase1_terminal_redirect'], frozen)
                    self.assertTrue(current.vars['screened_out'])
                    for app_module in [intro, s_c, other]:
                        for page in app_module.page_sequence:
                            if page.__name__ not in ['Intro', 'Structure', 'Consent', 'ScreenOut']:
                                target = current.get_player(app_module.C.NAME_IN_URL, 1)
                                self.assertFalse(page.is_displayed(target), page.__name__)
                    # Re-entry stays on ScreenOut; a crafted continue is rejected.
                    db.commit()
                    response = client.get('/InitializeParticipant/' + code, allow_redirects=True)
                    self.assertIn('/ScreenOut/', response.url)
                    response = client.post(response.url, data={}, allow_redirects=True)
                    self.assertIn('/ScreenOut/', response.url)
                    self.assertIn('Non è possibile proseguire', response.text)
                output = io.StringIO()
                export_wide(output, session_code=session_code)
                row = next(csv.DictReader(io.StringIO(output.getvalue())))
                self.assertEqual(row['participant.label'], 'U00012345-CaSe')
                self.assertEqual(row['intro.1.player.consent_read'], '1' if read else '0')
                self.assertEqual(row['intro.1.player.consent_accept'], decision or '')
                if not (read and decision == 'accept'):
                    self.assertEqual(row['participant.terminal_status'], 'screenout')
                    self.assertEqual(row['participant.terminal_reason'], 'consent_not_provided')
                    self.assertEqual(row['participant.terminal_time_utc'], frozen_terminal_time)
                    self.assertEqual(row['participant.seconds_survey_time'], '')


if __name__ == '__main__':
    unittest.main()
