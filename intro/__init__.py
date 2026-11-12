from otree.api import *
from municipality_data import MUNICIPALITY_ERROR, valid_municipality

from survey_common import can_continue_questionnaire, record_first_page_time, record_questionnaire_start, survey_page_context


doc = """Introduzione, consenso e domande sociodemografiche (Q1-Q9)."""


INCOME_CHOICES = [
    ('income_01_lt_500', 'Meno di €500'),
    ('income_02_500_999', 'Da €500 a €999'),
    ('income_03_1000_1499', 'Da €1.000 a €1.499'),
    ('income_04_1500_1999', 'Da €1.500 a €1.999'),
    ('income_05_2000_2499', 'Da €2.000 a €2.499'),
    ('income_06_2500_2999', 'Da €2.500 a €2.999'),
    ('income_07_3000_3499', 'Da €3.000 a €3.499'),
    ('income_08_3500_3999', 'Da €3.500 a €3.999'),
    ('income_09_4000_6999', 'Da €4.000 a €6.999'),
    ('income_10_ge_7000', '€7.000 o più'),
    ('prefer_not_to_answer', 'Preferisco non rispondere'),
]

EDUCATION_CHOICES = [
    ('doctorate', 'Dottorato di ricerca o titolo equivalente'),
    ('masters_or_equivalent', 'Laurea magistrale o specialistica, laurea a ciclo unico, laurea del vecchio ordinamento o titolo equivalente'),
    ('bachelors_its_or_equivalent', 'Laurea triennale, diploma universitario, diploma ITS Academy o titolo equivalente'),
    ('upper_secondary_diploma_or_ifts', 'Diploma di scuola secondaria di secondo grado (maturità o equivalente) o certificato di specializzazione tecnica superiore (IFTS)'),
    ('upper_secondary_vocational_no_maturita', 'Qualifica o diploma professionale di livello secondario superiore, senza maturità'),
    ('lower_secondary', 'Licenza di scuola secondaria di primo grado (scuola media)'),
    ('vocational_initiation_school', 'Licenza di scuola di avviamento professionale (percorso triennale dopo la scuola elementare)'),
    ('primary_or_none', 'Licenza di scuola primaria (scuola elementare) o nessun titolo di studio'),
    ('dont_know', 'Non so'),
    ('prefer_not_to_answer', 'Preferisco non rispondere'),
]

EMPLOYMENT_CHOICES = [
    ('employee_full_time', 'Lavoratore/lavoratrice dipendente a tempo pieno'),
    ('employee_part_time', 'Lavoratore/lavoratrice dipendente a tempo parziale'),
    ('self_employed', 'Lavoratore/lavoratrice autonomo/a o libero/a professionista'),
    ('unemployed_seeking', 'Disoccupato/a, in cerca di lavoro'),
    ('not_employed_not_seeking', 'Non occupato/a e non in cerca di lavoro'),
    ('parental_leave', 'In congedo parentale'),
    ('student', 'Studente/studentessa'),
    ('retired', 'Pensionato/a'),
    ('homemaker_caregiver', 'Casalingo/a o caregiver'),
    ('other', 'Altro'),
    ('prefer_not_to_answer', 'Preferisco non rispondere'),
]

OCCUPATION_CHOICES = [
    ('manager', 'Dirigente'),
    ('professional', 'Professione intellettuale, scientifica o di elevata specializzazione'),
    ('technician', 'Professione tecnica'),
    ('clerical', 'Impiegato/a di ufficio'),
    ('services_sales', 'Addetto/a ai servizi o alle vendite'),
    ('skilled_agriculture_forestry_fishing', "Lavoratore/lavoratrice qualificato/a dell'agricoltura, delle foreste o della pesca"),
    ('craft_skilled_worker', 'Artigiano/a o operaio/a specializzato/a'),
    ('plant_machine_operator_assembler', 'Conduttore/conduttrice di impianti o macchinari / addetto/a al montaggio'),
    ('elementary_occupation', 'Professione non qualificata'),
    ('armed_forces', 'Professione nelle forze armate'),
    ('never_worked', 'Non ho mai svolto un’attività lavorativa'),
    ('dont_know', 'Non so'),
    ('prefer_not_to_answer', 'Preferisco non rispondere'),
]


def _has_at_least_two_letters(value):
    """Unicode-safe Q3/Q4 minimum-text rule."""
    return sum(character.isalpha() for character in (value or '').strip()) >= 2


def influential_place_error_message(player, value):
    if not _has_at_least_two_letters(value):
        return 'Per favore, inserisci un luogo valido utilizzando almeno 2 lettere.'


class C(BaseConstants):
    NAME_IN_URL = 'intro'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    # TODO(study team): replace this placeholder with the approved screen-out URL.
    SCREENOUT_REDIRECT_URL = 'https://google.com'
    SCREENOUT_REDIRECT_DELAY_MS = 1500


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    attention_check_1 = models.StringField(
        choices=[('blue', 'Azzurro'), ('green', 'Verde'), ('dog', 'Cane'), ('red', 'Rosso')],
        widget=widgets.RadioSelect,
    )
    attention_check_1_failed = models.BooleanField(blank=True)
    consent_read = models.BooleanField(
        label="Ho letto le informazioni sullo studio.", widget=widgets.Checkbox
    )
    consent_accept = models.StringField(
        label="Acconsento a partecipare allo studio.",
        choices=[('accept', 'Acconsento'), ('decline', 'Non acconsento')],
        widget=widgets.RadioSelect,
    )

    # Q1
    sex_at_birth = models.StringField(
        label="Qual è il sesso che ti è stato assegnato alla nascita?",
        choices=[
            ('male', 'Maschio'),
            ('female', 'Femmina'),
            ('prefer_not_to_answer', 'Preferisco non rispondere'),
        ],
        widget=widgets.RadioSelect,
    )
    # Q2
    age = models.IntegerField(label="Quanti anni hai?", min=18, max=100)
    # Q3
    # Required together by Demographics1.error_message; blank=True allows the
    # same Italian selection error for missing and mismatched submissions.
    current_municipality = models.StringField(label="In quale comune vivi attualmente?", blank=True)
    current_municipality_istat_code = models.StringField(blank=True)
    # Q4
    influential_place = models.LongStringField(
        label=(
            "Tra i luoghi in cui hai vissuto durante l’infanzia o l’adolescenza, "
            "quale ritieni abbia influenzato maggiormente il tuo attuale modo di vivere e di pensare?"
        )
    )
    # Q5
    marital_status = models.StringField(
        label="Qual è il tuo stato civile?",
        choices=[
            ('unmarried_not_cohabiting', 'Non sposato/a e non convivente con un partner'),
            ('married', 'Sposato/a'),
            ('cohabiting_unmarried', 'Convivente con un partner senza essere sposato/a'),
            ('separated_or_divorced', 'Separato/a o divorziato/a'),
            ('widowed', 'Vedovo/a'),
            ('prefer_not_to_answer', 'Preferisco non rispondere'),
        ],
        widget=widgets.RadioSelect,
    )
    # Q6
    number_of_children = models.StringField(
        label="Quanti figli hai?",
        choices=[('0', 'Nessun figlio'), ('1', '1'), ('2', '2'), ('3', '3'), ('4_plus', '4 o più')],
        widget=widgets.RadioSelect,
    )
    # Q7
    education_level = models.StringField(
        label="Qual è il livello di istruzione più alto che hai completato?",
        choices=EDUCATION_CHOICES,
        widget=widgets.RadioSelect,
    )
    # Q8
    employment_status = models.StringField(
        label="Quale delle seguenti opzioni descrive meglio la tua attuale condizione occupazionale?",
        choices=EMPLOYMENT_CHOICES,
        widget=widgets.RadioSelect,
    )
    # Q8 occupation follow-up; demographic covariate only, no index membership.
    occupation_category = models.StringField(
        label="Quale delle seguenti opzioni descrive meglio la tua professione attuale o, se non lavori attualmente, l'ultima svolta?",
        choices=OCCUPATION_CHOICES,
        widget=widgets.RadioSelect,
    )
    # Q9
    net_monthly_income = models.StringField(
        label="Qual è approssimativamente il tuo reddito personale mensile netto?",
        choices=INCOME_CHOICES,
        widget=widgets.RadioSelect,
    )


class Intro(Page):
    @staticmethod
    def vars_for_template(player):
        record_first_page_time(player.participant)
        return survey_page_context('Introduzione')


class Structure(Page):
    @staticmethod
    def vars_for_template(player):
        return survey_page_context('Struttura dello studio')


class Consent(Page):
    form_model = 'player'
    form_fields = ['consent_read', 'consent_accept']

    @staticmethod
    def vars_for_template(player):
        return survey_page_context('Consenso informato')

    @staticmethod
    def before_next_page(player, timeout_happened):
        gave_consent = player.consent_read and player.consent_accept == 'accept'
        player.participant.vars['screened_out'] = not gave_consent


class ScreenOut(Page):
    @staticmethod
    def is_displayed(player):
        return player.participant.vars.get('screened_out', False)

    @staticmethod
    def vars_for_template(player):
        context = survey_page_context('Grazie')
        context.update(redirect_url=C.SCREENOUT_REDIRECT_URL, redirect_delay_ms=C.SCREENOUT_REDIRECT_DELAY_MS)
        return context


class Demographics1(Page):
    form_model = 'player'
    form_fields = ['sex_at_birth', 'age', 'current_municipality', 'current_municipality_istat_code']

    @staticmethod
    def error_message(player, values):
        if not valid_municipality(values.get('current_municipality'), values.get('current_municipality_istat_code')):
            return {'current_municipality': MUNICIPALITY_ERROR}

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        record_questionnaire_start(player.participant)
        return survey_page_context(stage='demographics1')


class Demographics2(Page):
    form_model = 'player'
    form_fields = ['influential_place', 'marital_status', 'number_of_children']

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        return survey_page_context(stage='demographics2')


class Demographics3(Page):
    form_model = 'player'
    form_fields = ['education_level', 'employment_status', 'occupation_category', 'net_monthly_income']

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        return survey_page_context(stage='demographics3')


class AttentionCheck1(Page):
    form_model = 'player'
    form_fields = ['attention_check_1']
    template_name = 'global/AttentionCheck.html'

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        context = survey_page_context('Domanda di attenzione', stage='demographics3')
        context.update(
            attention_question='Ecco la prima domanda in azzurro. Di che colore è questo testo?',
            attention_instruction='Ti chiediamo di ignorare la domanda e di rispondere selezionando il nome di un animale.',
            attention_field='attention_check_1',
        )
        return context

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.attention_check_1_failed = player.attention_check_1 != 'dog'


page_sequence = [Intro, Structure, Consent, ScreenOut, Demographics1, Demographics2, Demographics3, AttentionCheck1]
