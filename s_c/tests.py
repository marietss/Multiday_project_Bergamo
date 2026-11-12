import re

from otree.api import Bot, SubmissionMustFail

from intro import INCOME_CHOICES

from . import SocialCapital1, SocialCapital2, SocialCapital3, SocialCapital4

INCOME_TEST_CODES = [code for code, label in INCOME_CHOICES]

CASES = [
    'path_a', 'path_b', 'path_c', 'path_d',
    'retry_lottery', 'retry_sure', 'retry_dont_know',
    'intermediate_dont_know', 'final_dont_know', 'screenout',
] + INCOME_TEST_CODES + ['attention_both_wrong']


class PlayerBot(Bot):
    cases = CASES

    def play_round(self):
        if self.case == 'screenout':
            return
        assert '4 di 13' in self.participant_bot.html
        assert re.search(r'<h2[^>]*id="_otree-title"[^>]*>\s*</h2>', self.participant_bot.html)
        assert 'Fiducia e scelte sociali' not in self.participant_bot.html
        yield SubmissionMustFail(
            SocialCapital1,
            dict(generalized_trust='need_to_be_careful', unexpected_money_donation=701),
        )
        assert 'Il numero deve essere compreso tra 0 e 700.' in self.participant_bot.html
        boundary_donation = 0 if self.case == 'path_a' else 700
        yield SocialCapital1, dict(generalized_trust='need_to_be_careful', unexpected_money_donation=boundary_donation)
        q12_values_and_labels = [
            (0, 'Nessun regalo'),
            (4, 'Un regalo del valore di 4 euro'),
            (8, 'Un regalo del valore di 8 euro'),
            (12, 'Un regalo del valore di 12 euro'),
            (16, 'Un regalo del valore di 16 euro'),
            (20, 'Un regalo del valore di 20 euro'),
            (24, 'Un regalo del valore di 24 euro'),
        ]
        for value, label in q12_values_and_labels:
            assert f'value="{value}"' in self.participant_bot.html
            assert label in self.participant_bot.html
        yield SocialCapital2, dict(reciprocity_gift_value=16)
        assert self.player.reciprocity_gift_value == 16

        # The visible ranges have no name, while the named database inputs are
        # blank. Therefore an untouched browser slider cannot submit a midpoint.
        html = self.participant_bot.html
        range_tags = re.findall(r'<input class="survey-slider__range"[^>]*>', html)
        assert len(range_tags) == 3
        assert html.count('Valore selezionato') == 3
        assert html.count('<output class="survey-slider__value"') == 3
        assert all(' name=' not in tag for tag in range_tags)
        for field_name in ['best_intentions', 'positive_reciprocity', 'revenge']:
            storage_tag = re.search(rf'<input[^>]*name="{field_name}"[^>]*>', html).group(0)
            assert 'value=""' in storage_tag

        yield SubmissionMustFail(SocialCapital3, dict(best_intentions=5, positive_reciprocity=8))
        assert 'This field is required' not in self.participant_bot.html
        assert 'Questo campo è obbligatorio' in self.participant_bot.html
        html = self.participant_bot.html
        for field_name, value in [('best_intentions', '5'), ('positive_reciprocity', '8')]:
            storage_tag = re.search(rf'<input[^>]*name="{field_name}"[^>]*>', html).group(0)
            assert f'value="{value}"' in storage_tag
        revenge_tag = re.search(r'<input[^>]*name="revenge"[^>]*>', html).group(0)
        assert 'value=""' in revenge_tag

        yield SocialCapital3, dict(best_intentions=5, positive_reciprocity=8, revenge=2)
        yield SocialCapital4, dict(
            punish_personal_unfairness=4,
            punish_unfairness_to_others=6,
            unconditional_charitable_giving=7,
        )
