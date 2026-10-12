from otree.api import *

from survey_common import (
    can_continue_questionnaire,
    record_questionnaire_end,
    survey_page_context,
)


doc = """Politica, religione, rischio, norme civiche e capitale sociale locale (Q19-Q28)."""


class C(BaseConstants):
    NAME_IN_URL = 'other'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    LOTTERY = 'lottery'
    SURE = 'sure'
    DONT_KNOW = 'dont_know'
    RISK_STAIRCASE_FIRST_AMOUNT = 80
    RISK_STAIRCASE_NEXT_AMOUNT = {
        80: {LOTTERY: 120, SURE: 40},
        120: {LOTTERY: 140, SURE: 100},
        140: {LOTTERY: 150, SURE: 130},
        150: {LOTTERY: 155, SURE: 145},
        130: {LOTTERY: 135, SURE: 125},
        100: {LOTTERY: 110, SURE: 90},
        110: {LOTTERY: 115, SURE: 105},
        90: {LOTTERY: 95, SURE: 85},
        40: {LOTTERY: 60, SURE: 20},
        60: {LOTTERY: 70, SURE: 50},
        70: {LOTTERY: 75, SURE: 65},
        50: {LOTTERY: 55, SURE: 45},
        20: {LOTTERY: 30, SURE: 10},
        30: {LOTTERY: 35, SURE: 25},
        10: {LOTTERY: 15, SURE: 5},
    }


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    attention_check_2 = models.StringField(
        choices=[('six', '6'), ('five', '5'), ('cat', 'Gatto'), ('eight', '8')],
        widget=widgets.RadioSelect,
    )
    attention_check_2_failed = models.BooleanField(blank=True)
    attention_error = models.IntegerField(blank=True)
    # Q19
    religiosity = models.IntegerField(min=0, max=10)
    # Q20: the Boolean is deliberately separate from the nullable 0-10 value.
    political_position = models.IntegerField(min=0, max=10, blank=True)
    political_no_position = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    # Q21
    worship_attendance = models.StringField(
        choices=[
            ('daily', 'Tutti i giorni'),
            ('several_times_week', 'Qualche volta alla settimana'),
            ('weekly', 'Una volta alla settimana'),
            ('several_times_month', 'Qualche volta al mese (meno di 4 volte)'),
            ('several_times_year', 'Qualche volta l’anno'),
            ('never', 'Mai'),
        ],
        widget=widgets.RadioSelect,
    )
    # Q22
    general_risk_willingness = models.IntegerField(min=0, max=10)

    # Q23 raw adaptive staircase data.
    risk_staircase_amount_1 = models.IntegerField(blank=True)
    risk_staircase_amount_2 = models.IntegerField(blank=True)
    risk_staircase_amount_3 = models.IntegerField(blank=True)
    risk_staircase_amount_4 = models.IntegerField(blank=True)
    risk_staircase_amount_5 = models.IntegerField(blank=True)
    risk_staircase_choice_1 = models.StringField(blank=True, widget=widgets.RadioSelect)
    risk_staircase_choice_2 = models.StringField(widget=widgets.RadioSelect)
    risk_staircase_choice_3 = models.StringField(widget=widgets.RadioSelect)
    risk_staircase_choice_4 = models.StringField(widget=widgets.RadioSelect)
    risk_staircase_choice_5 = models.StringField(widget=widgets.RadioSelect)
    risk_staircase_first_attempt = models.StringField(widget=widgets.RadioSelect)
    risk_staircase_first_retry = models.StringField(widget=widgets.RadioSelect)
    risk_staircase_completed_steps = models.IntegerField(initial=0)
    risk_staircase_terminated_nonresponse = models.BooleanField(initial=False)
    risk_staircase_derived_measure = models.IntegerField(blank=True)

    # Q24a-Q24e
    justify_false_benefits = models.IntegerField(min=1, max=10)
    justify_fare_evasion = models.IntegerField(min=1, max=10)
    justify_tax_evasion = models.IntegerField(min=1, max=10)
    justify_keep_found_money = models.IntegerField(min=1, max=10)
    justify_not_report_vehicle_damage = models.IntegerField(min=1, max=10)
    civic_norms_score = models.IntegerField(blank=True)

    # Q25: two independent booleans for every organisation.
    political_party_member = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    political_party_participated = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    trade_union_member = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    trade_union_participated = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    volunteering_member = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    volunteering_participated = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    civic_environment_member = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    civic_environment_participated = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    sports_member = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    sports_participated = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    cultural_recreational_member = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    cultural_recreational_participated = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    professional_member = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    professional_participated = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    associations_none = models.BooleanField(blank=True, initial=False, widget=widgets.Checkbox)
    associativita_member = models.BooleanField(blank=True)
    associativita_participation = models.BooleanField(blank=True)
    associativita_any = models.BooleanField(blank=True)
    associativita_member_count = models.IntegerField(blank=True, min=0, max=7)
    associativita_participation_count = models.IntegerField(blank=True, min=0, max=7)

    # Q26
    local_collective_action = models.StringField(
        label="Negli ultimi 12 mesi, ti è mai capitato di collaborare con altre persone del luogo in cui vivi, per esempio nel tuo quartiere o nella tua città, per cercare di risolvere un problema di interesse comune?",
        choices=[('yes', 'Sì'), ('no', 'No')], widget=widgets.RadioSelect
    )
    local_collective_action_details = models.LongStringField(
        label="In che modo?",
        blank=True,
    )
    # Q27-Q28
    perceived_altruism = models.IntegerField(min=0, max=10)
    perceived_fairness = models.IntegerField(min=0, max=10)


ORGANISATION_FIELDS = [
    'political_party_member', 'political_party_participated',
    'trade_union_member', 'trade_union_participated',
    'volunteering_member', 'volunteering_participated',
    'civic_environment_member', 'civic_environment_participated',
    'sports_member', 'sports_participated',
    'cultural_recreational_member', 'cultural_recreational_participated',
    'professional_member', 'professional_participated',
]
MEMBER_FIELDS = [
    'political_party_member',
    'trade_union_member',
    'volunteering_member',
    'civic_environment_member',
    'sports_member',
    'cultural_recreational_member',
    'professional_member',
]
PARTICIPATION_FIELDS = [
    'political_party_participated',
    'trade_union_participated',
    'volunteering_participated',
    'civic_environment_participated',
    'sports_participated',
    'cultural_recreational_participated',
    'professional_participated',
]


def risk_choice_options(amount):
    return [
        (
            C.LOTTERY,
            'Lotteria: 50% di probabilità di ricevere 150 euro e 50% di probabilità di non ricevere nulla',
        ),
        (C.SURE, f'Pagamento sicuro di {amount} euro'),
        (C.DONT_KNOW, 'Non so / Preferisco non rispondere'),
    ]


def risk_staircase_first_attempt_choices(player):
    return risk_choice_options(C.RISK_STAIRCASE_FIRST_AMOUNT)


def risk_staircase_first_retry_choices(player):
    return risk_choice_options(C.RISK_STAIRCASE_FIRST_AMOUNT)


def risk_staircase_choice_1_choices(player):
    return risk_choice_options(player.risk_staircase_amount_1)


def risk_staircase_choice_2_choices(player):
    return risk_choice_options(player.risk_staircase_amount_2)


def risk_staircase_choice_3_choices(player):
    return risk_choice_options(player.risk_staircase_amount_3)


def risk_staircase_choice_4_choices(player):
    return risk_choice_options(player.risk_staircase_amount_4)


def risk_staircase_choice_5_choices(player):
    return risk_choice_options(player.risk_staircase_amount_5)


def set_next_staircase_amount(player, step, choice):
    amount = getattr(player, f'risk_staircase_amount_{step}')
    next_amount = C.RISK_STAIRCASE_NEXT_AMOUNT[amount][choice]
    setattr(player, f'risk_staircase_amount_{step + 1}', next_amount)


def calculate_risk_staircase_score(amount, choice):
    """Return the specified 1-32 score for a substantive fifth decision."""
    if amount not in range(5, 156, 10) or choice not in [C.SURE, C.LOTTERY]:
        return None
    k = (amount - 5) // 10
    return 2 * k + (1 if choice == C.SURE else 2)


def calculate_civic_norms_score(values):
    """Reverse-code all five Q24 items and return CIVIC; never score partial data."""
    raw_items = [
        values.get('justify_false_benefits'),
        values.get('justify_fare_evasion'),
        values.get('justify_tax_evasion'),
        values.get('justify_keep_found_money'),
        values.get('justify_not_report_vehicle_damage'),
    ]
    if any(value is None for value in raw_items):
        return None
    return 55 - sum(raw_items)


def calculate_associativita(values):
    """Derive Q25 engagement indicators and 0-7 category counts."""
    member_count = sum(bool(values.get(field)) for field in MEMBER_FIELDS)
    participation_count = sum(bool(values.get(field)) for field in PARTICIPATION_FIELDS)
    member = member_count > 0
    participation = participation_count > 0
    return {
        'associativita_member': member,
        'associativita_participation': participation,
        'associativita_any': member or participation,
        'associativita_member_count': member_count,
        'associativita_participation_count': participation_count,
    }


def finish_staircase_step(player, step, choice):
    """Persist completion/termination state and create only the relevant branch."""
    player.risk_staircase_completed_steps = step
    if choice == C.DONT_KNOW:
        player.risk_staircase_terminated_nonresponse = True
    elif step < 5:
        set_next_staircase_amount(player, step, choice)
    elif step == 5:
        player.risk_staircase_derived_measure = calculate_risk_staircase_score(
            player.risk_staircase_amount_5,
            choice,
        )


def staircase_context(player, decision_field, decision_number, amount, *, show_introduction=False, retry=False):
    context = survey_page_context(stage='risk_staircase')
    context.update(
        decision_field=decision_field,
        decision_number=decision_number,
        certain_amount=amount,
        show_staircase_introduction=show_introduction,
        is_first_retry=retry,
    )
    return context


class PoliticsReligion(Page):
    form_model = 'player'
    form_fields = ['religiosity', 'political_position', 'political_no_position', 'worship_attendance']

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        return survey_page_context(stage='politics_religion')

    @staticmethod
    def error_message(player, values):
        position = values.get('political_position')
        no_position = values.get('political_no_position')
        if no_position and position is not None:
            return 'Per la collocazione politica, scegli una sola modalità di risposta.'
        if not no_position and position is None:
            return 'Indica una posizione politica oppure seleziona “Non mi colloco su questa scala”.'


class RiskGeneral(Page):
    form_model = 'player'
    form_fields = ['general_risk_willingness']

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        return survey_page_context(stage='risk_general')


class AttentionCheck2(Page):
    form_model = 'player'
    form_fields = ['attention_check_2']
    template_name = 'global/AttentionCheck.html'

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        context = survey_page_context('Domanda di attenzione', stage='risk_general')
        context.update(
            attention_question='Ecco la seconda domanda in azzurro. Quanto fa 3 × 2 (tre moltiplicato per due)?',
            attention_instruction='Ti chiediamo di ignorare la domanda e di rispondere selezionando il nome di un animale.',
            attention_field='attention_check_2',
        )
        return context

    @staticmethod
    def before_next_page(player, timeout_happened):
        first = player.participant.get_player('intro', 1)
        player.attention_check_2_failed = player.attention_check_2 != 'cat'
        player.attention_error = int(first.attention_check_1_failed) + int(player.attention_check_2_failed)
        player.participant.vars['attention_screened_out'] = player.attention_error == 2


class AttentionScreenOut(Page):
    @staticmethod
    def is_displayed(player):
        return player.participant.vars.get('attention_screened_out', False)

    @staticmethod
    def vars_for_template(player):
        context = survey_page_context('Grazie', stage='risk_general')
        context['attention_redirect_url'] = player.session.config.get('attention_screenout_url', '')
        return context

    @staticmethod
    def error_message(player, values):
        # Also prevent a manually crafted POST from advancing this terminal page.
        return 'Non è possibile proseguire con il questionario.'


class RiskStaircase1(Page):
    form_model = 'player'
    form_fields = ['risk_staircase_first_attempt']
    template_name = 'other/RiskStaircase.html'

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        if player.field_maybe_none('risk_staircase_amount_1') is None:
            # Store the amount only when it is actually shown; screen-outs keep
            # every staircase amount NULL.
            player.risk_staircase_amount_1 = C.RISK_STAIRCASE_FIRST_AMOUNT
        return staircase_context(
            player,
            'risk_staircase_first_attempt',
            1,
            C.RISK_STAIRCASE_FIRST_AMOUNT,
            show_introduction=True,
        )

    @staticmethod
    def before_next_page(player, timeout_happened):
        choice = player.risk_staircase_first_attempt
        player.risk_staircase_choice_1 = choice
        player.risk_staircase_completed_steps = 1
        if choice in [C.LOTTERY, C.SURE]:
            set_next_staircase_amount(player, 1, choice)


class RiskStaircaseRetry(Page):
    form_model = 'player'
    form_fields = ['risk_staircase_first_retry']
    template_name = 'other/RiskStaircase.html'

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player) and player.risk_staircase_first_attempt == C.DONT_KNOW

    @staticmethod
    def vars_for_template(player):
        return staircase_context(
            player,
            'risk_staircase_first_retry',
            1,
            C.RISK_STAIRCASE_FIRST_AMOUNT,
            retry=True,
        )

    @staticmethod
    def before_next_page(player, timeout_happened):
        choice = player.risk_staircase_first_retry
        player.risk_staircase_choice_1 = choice
        if choice == C.DONT_KNOW:
            player.risk_staircase_terminated_nonresponse = True
        else:
            set_next_staircase_amount(player, 1, choice)


class RiskStaircase2(Page):
    form_model = 'player'
    form_fields = ['risk_staircase_choice_2']
    template_name = 'other/RiskStaircase.html'

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player) and not player.risk_staircase_terminated_nonresponse and player.risk_staircase_amount_2 is not None

    @staticmethod
    def vars_for_template(player):
        return staircase_context(player, 'risk_staircase_choice_2', 2, player.risk_staircase_amount_2)

    @staticmethod
    def before_next_page(player, timeout_happened):
        finish_staircase_step(player, 2, player.risk_staircase_choice_2)


class RiskStaircase3(Page):
    form_model = 'player'
    form_fields = ['risk_staircase_choice_3']
    template_name = 'other/RiskStaircase.html'

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player) and not player.risk_staircase_terminated_nonresponse and player.risk_staircase_amount_3 is not None

    @staticmethod
    def vars_for_template(player):
        return staircase_context(player, 'risk_staircase_choice_3', 3, player.risk_staircase_amount_3)

    @staticmethod
    def before_next_page(player, timeout_happened):
        finish_staircase_step(player, 3, player.risk_staircase_choice_3)


class RiskStaircase4(Page):
    form_model = 'player'
    form_fields = ['risk_staircase_choice_4']
    template_name = 'other/RiskStaircase.html'

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player) and not player.risk_staircase_terminated_nonresponse and player.risk_staircase_amount_4 is not None

    @staticmethod
    def vars_for_template(player):
        return staircase_context(player, 'risk_staircase_choice_4', 4, player.risk_staircase_amount_4)

    @staticmethod
    def before_next_page(player, timeout_happened):
        finish_staircase_step(player, 4, player.risk_staircase_choice_4)


class RiskStaircase5(Page):
    form_model = 'player'
    form_fields = ['risk_staircase_choice_5']
    template_name = 'other/RiskStaircase.html'

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player) and not player.risk_staircase_terminated_nonresponse and player.risk_staircase_amount_5 is not None

    @staticmethod
    def vars_for_template(player):
        return staircase_context(player, 'risk_staircase_choice_5', 5, player.risk_staircase_amount_5)

    @staticmethod
    def before_next_page(player, timeout_happened):
        finish_staircase_step(player, 5, player.risk_staircase_choice_5)


class CivicNorms(Page):
    form_model = 'player'
    form_fields = [
        'justify_false_benefits', 'justify_fare_evasion', 'justify_tax_evasion',
        'justify_keep_found_money', 'justify_not_report_vehicle_damage',
    ]

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        return survey_page_context(stage='civic_norms')

    @staticmethod
    def before_next_page(player, timeout_happened):
        values = {
            field_name: getattr(player, field_name)
            for field_name in CivicNorms.form_fields
        }
        player.civic_norms_score = calculate_civic_norms_score(values)


class Associations(Page):
    form_model = 'player'
    form_fields = ORGANISATION_FIELDS + ['associations_none']

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        return survey_page_context(stage='associations')

    @staticmethod
    def error_message(player, values):
        any_organisation = any(bool(values.get(field)) for field in ORGANISATION_FIELDS)
        none_selected = bool(values.get('associations_none'))
        if any_organisation and none_selected:
            return '“Nessuna delle precedenti” non può essere selezionata insieme ad altre risposte.'
        if not any_organisation and not none_selected:
            return 'Seleziona almeno una risposta oppure “Nessuna delle precedenti”.'

    @staticmethod
    def before_next_page(player, timeout_happened):
        raw_values = {
            field_name: getattr(player, field_name)
            for field_name in ORGANISATION_FIELDS
        }
        for field_name, value in calculate_associativita(raw_values).items():
            setattr(player, field_name, value)


class LocalSocialCapital(Page):
    form_model = 'player'
    form_fields = [
        'local_collective_action',
        'local_collective_action_details',
        'perceived_altruism',
        'perceived_fairness',
    ]

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        return survey_page_context(stage='local_social_capital')

    @staticmethod
    def error_message(player, values):
        if values.get('local_collective_action') == 'yes':
            details = (values.get('local_collective_action_details') or '').strip()
            if sum(character.isalpha() for character in details) < 2:
                return {
                    'local_collective_action_details':
                        'Per favore, descrivi in che modo utilizzando almeno 2 lettere.'
                }

    @staticmethod
    def before_next_page(player, timeout_happened):
        if player.local_collective_action != 'yes':
            player.local_collective_action_details = None
        record_questionnaire_end(player.participant)


class End(Page):
    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        return survey_page_context('Questionario completato', 'local_social_capital')


page_sequence = [
    PoliticsReligion,
    RiskGeneral,
    AttentionCheck2,
    AttentionScreenOut,
    RiskStaircase1,
    RiskStaircaseRetry,
    RiskStaircase2,
    RiskStaircase3,
    RiskStaircase4,
    RiskStaircase5,
    CivicNorms,
    Associations,
    LocalSocialCapital,
    End,
]
