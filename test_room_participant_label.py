"""HTTP integration test; run only in an isolated in-memory oTree database:

OTREE_IN_MEMORY=1 OTREE_EPHEMERAL=1 python3 -m unittest -v test_room_participant_label
"""
import csv
import io
import os
import unittest
from urllib.parse import urlsplit


class RoomParticipantLabelTest(unittest.TestCase):
    def test_distinct_labels_reentry_and_exports(self):
        from otree.database import IN_MEMORY, db, init_orm
        self.assertTrue(IN_MEMORY and os.environ.get('OTREE_EPHEMERAL'),
                        'Use the documented isolated in-memory invocation.')
        import otree.database
        otree.database.ephemeral_connection = otree.database.engine.connect()
        init_orm()
        from otree.asgi import app
        from otree.session import create_session
        from otree.room import ROOM_DICT
        from otree.models import Participant
        from otree.export import export_app, export_wide
        from starlette.testclient import TestClient

        room = ROOM_DICT['my_room']
        self.assertFalse(room.use_secure_urls)
        session = create_session('initial_survey', num_participants=3, room_name='my_room')
        session_code = session.code
        db.commit()
        client = TestClient(app)
        labels = ['U12345', 'U00002-CaseSensitive']
        assigned = {}
        for label in labels:
            # Native room landing page, followed by its normal validation/start
            # sequence. Same browser cookies are deliberately used for both IDs.
            response = client.get('/room/my_room/', params={'participant_label': label})
            self.assertEqual(response.status_code, 200)
            self.assertIn('welcome_page_ok', response.text)
            # oTree canonicalizes the trailing slash; its welcome JS posts to
            # window.location.pathname after that redirect.
            room_path = urlsplit(response.url).path
            response = client.post(room_path, params={'participant_label': label}, json={})
            self.assertEqual(response.status_code, 200, response.text[:1000])
            self.assertEqual(response.json(), {'status': 'ok'})
            response = client.get('/room/my_room/', params={
                'participant_label': label, 'welcome_page_ok': '1'}, allow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Benvenuto/a!', response.text)
            participant = Participant.objects_get(label=label)
            assigned[label] = participant.id
            self.assertEqual(participant.label, label)
        self.assertEqual(len(set(assigned.values())), 2)

        for label in labels:
            response = client.get('/room/my_room/', params={
                'participant_label': label, 'welcome_page_ok': '1'}, allow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(Participant.objects_get(label=label).id, assigned[label])
        for label, pk in assigned.items():
            self.assertEqual(Participant.objects_get(id=pk).label, label)

        for export in [lambda fp: export_app('intro', fp, session_code=session_code),
                       lambda fp: export_wide(fp, session_code=session_code)]:
            output = io.StringIO()
            export(output)
            rows = list(csv.DictReader(io.StringIO(output.getvalue())))
            self.assertIn('participant.label', rows[0])
            exported = {row['participant.label'] for row in rows if row['participant.label']}
            self.assertEqual(exported, set(labels))


if __name__ == '__main__':
    unittest.main()
