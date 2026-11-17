from os import environ

MAXIMILES_REDIRECT_URLS = {
    'complete': 'https://survey.maximiles.com/static-complete?p=177137_7285c59a',
    'quality': 'https://survey.maximiles.com/static-quality?p=177137',
    'speeder': 'https://survey.maximiles.com/static-speeder?p=177137',
    # Available only: no current condition routes participants here.
    'screenout': 'https://survey.maximiles.com/static-screenout?p=177137_17a5978d',
}

SESSION_CONFIGS = [
     dict(
         name='initial_survey',
         app_sequence=['intro', 's_c', 'other'],
         num_demo_participants=4,
         attention_screenout_url=MAXIMILES_REDIRECT_URLS['quality'],
         complete_redirect_url=MAXIMILES_REDIRECT_URLS['complete'],
         speeder_redirect_url=MAXIMILES_REDIRECT_URLS['speeder'],
         screenout_redirect_url=MAXIMILES_REDIRECT_URLS['screenout'],
     ),
]

ROOMS = [
    dict(
        name='my_room',
        display_name='My_room',
        # Recruitment ID arrives unchanged through ?participant_label=... .
        # Native oTree room handling stores/exports it as participant.label.
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

# Cross-phase recruitment ID: native participant.label via participant_label.
# unique_id is a retained legacy field, not the Phase-1/Phase-2 linking key.
# Maximiles terminal URLs are configured above; consent refusal remains independent.
# time_started_utc is already a built-in oTree Participant column; Phase-1 code
# resets it once at Demographics1 rather than declaring a duplicate custom field.
PARTICIPANT_FIELDS = [
    'unique_id', 'time_ended_utc', 'seconds_survey_time',
    'time_first_page_utc', 'seconds_total_study_time',
    'terminal_status', 'terminal_reason',
]
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'it'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '2741793931571'
