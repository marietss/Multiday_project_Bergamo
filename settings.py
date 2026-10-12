from os import environ

SESSION_CONFIGS = [
     dict(
         name='initial_survey',
         app_sequence=['intro', 's_c', 'other'],
         num_demo_participants=4,
         # TODO(Bilendi): supply the dedicated attention-check screen-out URL.
         attention_screenout_url='',
     ),
]

ROOMS = [
    dict(
        name='my_room',
        display_name='My_room',
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

# TODO(Bilendi): supply the respondent-ID URL parameter before populating unique_id.
# TODO(Bilendi): supply the approved consent, attention-check, and completion redirect URLs.
# time_started_utc is already a built-in oTree Participant column; Phase-1 code
# resets it once at Demographics1 rather than declaring a duplicate custom field.
PARTICIPANT_FIELDS = [
    'unique_id', 'time_ended_utc', 'seconds_survey_time',
    'time_first_page_utc', 'seconds_total_study_time',
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
