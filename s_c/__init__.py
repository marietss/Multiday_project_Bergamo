from otree.api import *

from survey_common import can_continue_questionnaire, survey_page_context


doc = """Capitale sociale, fiducia e reciprocità (Q10-Q18)."""


class C(BaseConstants):
    NAME_IN_URL = 's_c'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Q10
    generalized_trust = models.StringField(
        label="Generalmente pensi che ci si possa fidare della maggior parte della gente oppure bisogna stare molto attenti?",
        choices=[
            ('most_people_trustworthy', 'Gran parte della gente è degna di fiducia'),
            ('need_to_be_careful', 'Bisogna stare molto attenti'),
        ],
        widget=widgets.RadioSelect,
    )
    # Q11
    unexpected_money_donation = models.IntegerField(min=0, max=700)
    # Q12
    reciprocity_gift_value = models.IntegerField(
        choices=[
            (0, 'Nessun regalo'),
            (4, 'Un regalo del valore di 4 euro'),
            (8, 'Un regalo del valore di 8 euro'),
            (12, 'Un regalo del valore di 12 euro'),
            (16, 'Un regalo del valore di 16 euro'),
            (20, 'Un regalo del valore di 20 euro'),
            (24, 'Un regalo del valore di 24 euro'),
        ],
        widget=widgets.RadioSelect,
    )
    # Q13-Q15
    best_intentions = models.IntegerField(min=0, max=10)
    positive_reciprocity = models.IntegerField(min=0, max=10)
    revenge = models.IntegerField(min=0, max=10)
    # Q16-Q18
    punish_personal_unfairness = models.IntegerField(min=0, max=10)
    punish_unfairness_to_others = models.IntegerField(min=0, max=10)
    unconditional_charitable_giving = models.IntegerField(min=0, max=10)


class SocialCapital1(Page):
    form_model = 'player'
    form_fields = ['generalized_trust', 'unexpected_money_donation']

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        return survey_page_context(stage='social_capital1')


class SocialCapital2(Page):
    form_model = 'player'
    form_fields = ['reciprocity_gift_value']

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        return survey_page_context(stage='social_capital2')


class SocialCapital3(Page):
    form_model = 'player'
    form_fields = ['best_intentions', 'positive_reciprocity', 'revenge']

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        return survey_page_context(stage='social_capital3')


class SocialCapital4(Page):
    form_model = 'player'
    form_fields = ['punish_personal_unfairness', 'punish_unfairness_to_others', 'unconditional_charitable_giving']

    @staticmethod
    def is_displayed(player):
        return can_continue_questionnaire(player)

    @staticmethod
    def vars_for_template(player):
        return survey_page_context(stage='social_capital4')


page_sequence = [SocialCapital1, SocialCapital2, SocialCapital3, SocialCapital4]
