"""OTREE_IN_MEMORY=1 OTREE_EPHEMERAL=1 python3 -m unittest -v test_phase1_timestamps_labels"""
import csv
import io
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch


class Phase1TimestampLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import otree.database as database
        if not database.IN_MEMORY or not os.environ.get('OTREE_EPHEMERAL'):
            raise RuntimeError('Run only with OTREE_IN_MEMORY=1 OTREE_EPHEMERAL=1')
        database.ephemeral_connection = database.engine.connect()
        database.init_orm()

    def assert_iso_utc(self, value):
        self.assertRegex(value, r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}\+00:00$')
        self.assertEqual(datetime.fromisoformat(value).utcoffset(), timedelta(0))

    def test_serializer_requires_aware_and_normalizes_offsets(self):
        from utc_timestamps import utc_isoformat
        with self.assertRaises(ValueError):
            utc_isoformat(datetime(2026, 11, 17, 12))
        self.assertEqual(utc_isoformat(datetime(2026, 11, 17, 12, tzinfo=timezone(timedelta(hours=1)))),
                         '2026-11-17T11:00:00.000000+00:00')

    def test_missing_labels_block_get_and_post_without_terminal_or_timer(self):
        from otree.session import create_session
        from otree.models import Participant
        from otree.database import db
        from otree.asgi import app
        from starlette.testclient import TestClient
        from terminal_redirects import finalize_terminal_redirect
        for label in [None, '', '   ', '\t']:
            with self.subTest(label=repr(label)):
                session = create_session('initial_survey', num_participants=1)
                pp = session.get_participants()[0]
                pp.label = label
                pk, code = pp.id, pp.code
                db.commit()
                del pp
                client = TestClient(app)
                response = client.get('/InitializeParticipant/' + code, allow_redirects=True)
                self.assertEqual(response.status_code, 403)
                self.assertIn('Link non valido o incompleto', response.text)
                self.assertNotIn('<form', response.text)
                self.assertNotIn('survey.maximiles.com', response.text)
                # A forged label in a form/page query is not accepted as an ID.
                response = client.post(response.url, data={
                    'participant_label': 'INJECTED-ID', 'consent_read': 'True',
                    'consent_accept': 'accept'}, allow_redirects=True)
                self.assertEqual(response.status_code, 403)
                db.expire_all()
                current = Participant.objects_get(id=pk)
                self.assertEqual(current.label, label)
                self.assertFalse(current.vars.get('phase1_questionnaire_timing_started', False))
                for key in ['seconds_survey_time', 'terminal_status', 'terminal_reason',
                            'terminal_time_utc', 'phase1_terminal_redirect']:
                    self.assertIsNone(current.vars.get(key))
                self.assertIsNone(current.get_player('intro', 1).field_maybe_none('consent_accept'))
                self.assertIsNone(finalize_terminal_redirect(current, session.config,
                                   attention_error=2, consent_not_provided=True))
                del current

    def test_valid_direct_ids_preserved_and_missing_midflow_label_blocks(self):
        from otree.session import create_session
        from otree.models import Participant
        from otree.database import db
        from otree.asgi import app
        from starlette.testclient import TestClient
        for label in ['U12345', 'U00002-CaseSensitive', ' U00002-CaseSensitive ']:
            session = create_session('initial_survey', num_participants=1)
            pp = session.get_participants()[0]
            pk, code = pp.id, pp.code
            db.commit()
            del pp
            client = TestClient(app)
            response = client.get('/InitializeParticipant/' + code,
                                  params={'participant_label': label}, allow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Benvenuto/a!', response.text)
            for data in [{}, {}, {'consent_read': 'True', 'consent_accept': 'accept'}]:
                response = client.post(response.url, data=data, allow_redirects=True)
                self.assertEqual(response.status_code, 200)
            self.assertIn('/Demographics1/', response.url)
            db.expire_all()
            current = Participant.objects_get(id=pk)
            self.assertEqual(current.label, label)
            self.assert_iso_utc(current.time_started_utc)
            original_start = current.time_started_utc
            current.label = None
            db.commit()
            del current
            blocked = client.get(response.url, allow_redirects=True)
            self.assertEqual(blocked.status_code, 403)
            blocked = client.post(response.url, data={'sex_at_birth': 'female', 'age': 18,
                                  'current_municipality': 'Bologna', 'current_municipality_istat_code': '037006'},
                                  allow_redirects=True)
            self.assertEqual(blocked.status_code, 403)
            db.expire_all()
            current = Participant.objects_get(id=pk)
            self.assertIsNone(current.get_player('intro', 1).field_maybe_none('age'))
            self.assertEqual(current.time_started_utc, original_start)
            self.assertIsNone(current.vars.get('terminal_status'))
            del current

    def test_five_terminal_outcomes_iso_wide_export_and_immutability(self):
        from otree.session import create_session
        from otree.database import db
        from otree.models import Participant
        from otree.asgi import app
        from otree.export import export_wide
        from starlette.testclient import TestClient
        from intro import Consent, AttentionCheck1, Demographics1
        from other import AttentionCheck2, LocalSocialCapital
        from terminal_redirects import finalize_terminal_redirect
        session = create_session('initial_survey', num_participants=5)
        session_code = session.code
        participants = [(p.id, p.code) for p in session.get_participants()]
        cases = [
            ('U12345', 'complete', 'completed_normally', 300),
            ('U00002-CaseSensitive', 'speeder', 'speeder_under_180', 179),
            ('TEST-quality-attention', 'quality', 'quality_attention_checks', 100),
            ('TEST-quality-time', 'quality', 'quality_over_1200', 1201),
            ('TEST-screenout', 'screenout', 'consent_not_provided', None),
        ]
        db.commit()
        for (pk, code), (label, status, reason, seconds) in zip(participants, cases):
            client = TestClient(app)
            response = client.get('/InitializeParticipant/' + code, params={'participant_label': label},
                                  allow_redirects=True)
            self.assertEqual(response.status_code, 200)
            db.expire_all()
            pp = Participant.objects_get(id=pk)
            first = pp.get_player('intro', 1)
            player = pp.get_player('other', 1)
            self.assert_iso_utc(pp.time_otree_entry_utc)
            # Native entry value is untouched until the established questionnaire
            # start hook replaces it. Its project mirror is already ISO UTC.
            self.assertNotIn('T', pp.time_started_utc)
            if status == 'screenout':
                first.consent_read = False
                first.consent_accept = None
                Consent.before_next_page(first, False)
            else:
                first.consent_read = True
                first.consent_accept = 'accept'
                Consent.before_next_page(first, False)
                Demographics1.vars_for_template(first)
                start = datetime.fromisoformat(pp.time_started_utc)
                target = start + timedelta(seconds=seconds)
                with patch('survey_common.datetime', wraps=datetime) as clock, \
                     patch('terminal_redirects.datetime', wraps=datetime) as terminal_clock:
                    clock.now.return_value = target
                    terminal_clock.now.return_value = target
                    if reason == 'quality_attention_checks':
                        first.attention_check_1 = 'blue'
                        player.attention_check_2 = 'six'
                        AttentionCheck1.before_next_page(first, False)
                        AttentionCheck2.before_next_page(player, False)
                    elif reason == 'quality_over_1200':
                        Demographics1.before_next_page(first, False)
                    else:
                        player.attention_error = 0
                        player.local_collective_action = 'no'
                        LocalSocialCapital.before_next_page(player, False)
            terminal_time = pp.terminal_time_utc
            self.assert_iso_utc(terminal_time)
            self.assertEqual((pp.terminal_status, pp.terminal_reason), (status, reason))
            for _ in range(2):
                finalize_terminal_redirect(pp, session.config, attention_error=2, completed=True,
                                           consent_not_provided=True)
                self.assertEqual(pp.terminal_time_utc, terminal_time)
            db.commit()
            del pp, first, player
            # Refresh an early page cannot change a terminal event timestamp.
            response = client.get('/InitializeParticipant/' + code, allow_redirects=True)
            self.assertEqual(Participant.objects_get(id=pk).terminal_time_utc, terminal_time)
        out = io.StringIO()
        export_wide(out, session_code=session_code)
        rows = list(csv.DictReader(io.StringIO(out.getvalue())))
        custom_times = ['time_first_page_utc', 'time_ended_utc', 'terminal_time_utc', 'time_otree_entry_utc']
        for row, case in zip(rows, cases):
            label, status, reason, seconds = case
            self.assertEqual(row['participant.label'], label)
            self.assertEqual(row['participant.terminal_status'], status)
            self.assertEqual(row['participant.terminal_reason'], reason)
            self.assertTrue(row['participant.terminal_time_utc'])
            for field in custom_times:
                value = row['participant.' + field]
                if value:
                    self.assert_iso_utc(value)
            if seconds is not None:
                self.assertEqual(float(row['participant.seconds_survey_time']), seconds)
                self.assert_iso_utc(row['participant.time_started_utc'])
            else:
                self.assertEqual(row['participant.seconds_survey_time'], '')
        # A concrete, re-readable export artifact for audit; synthetic IDs only.
        with open('/tmp/phase1_timestamps_wide_test.csv', 'w', encoding='utf-8', newline='') as fp:
            fp.write(out.getvalue())


if __name__ == '__main__':
    unittest.main()
