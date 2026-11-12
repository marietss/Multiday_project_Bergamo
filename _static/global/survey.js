(function () {
    'use strict';

    function setSliderAnswered(component, value) {
        const range = component.querySelector('.survey-slider__range');
        const storage = component.querySelector('.survey-slider__storage input');
        const output = component.querySelector('.survey-slider__value');
        if (value !== '' && value !== null && value !== undefined) {
            range.value = value;
            storage.value = value;
            output.textContent = value;
            component.classList.remove('survey-slider--unanswered');
            component.dataset.answered = 'true';
        } else {
            storage.value = '';
            output.textContent = '—';
            component.classList.add('survey-slider--unanswered');
            component.dataset.answered = 'false';
        }
    }

    function initialiseSlider(component) {
        const range = component.querySelector('.survey-slider__range');
        const storage = component.querySelector('.survey-slider__storage input');
        const error = component.querySelector('.survey-client-error');
        if (!range || !storage) return;

        storage.type = 'hidden';
        setSliderAnswered(component, storage.value);

        range.addEventListener('input', function () {
            setSliderAnswered(component, range.value);
            if (error) error.hidden = true;
            component.dispatchEvent(new CustomEvent('survey-slider-change', { bubbles: true }));
        });
    }

    function initialisePoliticalExclusiveOption() {
        const wrapper = document.querySelector('[data-political-exclusive]');
        if (!wrapper) return;
        const slider = wrapper.querySelector('.survey-slider');
        const storage = slider && slider.querySelector('.survey-slider__storage input');
        const noPosition = wrapper.querySelector('#id_political_no_position');
        if (!slider || !storage || !noPosition) return;

        noPosition.addEventListener('change', function () {
            if (noPosition.checked) setSliderAnswered(slider, '');
        });
        slider.addEventListener('survey-slider-change', function () {
            noPosition.checked = false;
        });
    }

    function initialiseAssociationExclusivity() {
        const wrapper = document.querySelector('[data-association-exclusive]');
        if (!wrapper) return;
        const none = wrapper.querySelector('#id_associations_none');
        const organisationBoxes = Array.from(wrapper.querySelectorAll('[data-organisation-checkbox] input'));
        if (!none) return;

        none.addEventListener('change', function () {
            if (none.checked) organisationBoxes.forEach(function (box) { box.checked = false; });
        });
        organisationBoxes.forEach(function (box) {
            box.addEventListener('change', function () {
                if (box.checked) none.checked = false;
            });
        });
    }

    const minimumAlphabeticFields = {
        id_influential_place: 'Per favore, inserisci un luogo valido.',
        id_local_collective_action_details: 'Per favore, descrivi in che modo utilizzando qualche frase.'
    };

    function alphabeticCharacterCount(value) {
        // Unicode property escapes cover accented letters used in Italian and
        // names in other writing systems. Current supported browser targets
        // all implement this ES2018 feature.
        return Array.from(value.trim()).filter(function (character) {
            return /\p{L}/u.test(character);
        }).length;
    }

    function validateMinimumAlphabeticText(input) {
        const message = minimumAlphabeticFields[input.id];
        if (!message) return;
        if (input.disabled) {
            input.setCustomValidity('');
            return;
        }
        input.setCustomValidity(alphabeticCharacterCount(input.value) >= 2 ? '' : message);
    }

    function initialiseCollectiveActionDetails() {
        const wrapper = document.querySelector('[data-collective-action-details]');
        const details = document.getElementById('id_local_collective_action_details');
        const choices = Array.from(document.querySelectorAll('input[name="local_collective_action"]'));
        if (!wrapper || !details || !choices.length) return;

        function updateVisibility() {
            const selected = choices.find(function (choice) { return choice.checked; });
            const isApplicable = selected && selected.value === 'yes';
            wrapper.hidden = !isApplicable;
            details.disabled = !isApplicable;
            details.required = Boolean(isApplicable);
            if (!isApplicable) details.value = '';
            validateMinimumAlphabeticText(details);
        }

        choices.forEach(function (choice) {
            choice.addEventListener('change', updateVisibility);
        });
        updateVisibility();
    }

    function participantValidationMessage(input) {
        if (input.id === 'municipality-search') return 'Seleziona un comune dall’elenco.';
        if (minimumAlphabeticFields[input.id]) {
            return minimumAlphabeticFields[input.id];
        }
        if (input.validity.valueMissing) {
            return 'Per favore, rispondi a questa domanda.';
        }
        if (input.id === 'id_age') {
            return "Inserisci un'età compresa tra 18 e 100 anni.";
        }
        if (input.id === 'id_unexpected_money_donation') {
            return 'Inserisci un importo compreso tra 0 e 700 euro.';
        }
        return 'Per favore, inserisci un valore valido.';
    }

    function clearValidityForField(form, input) {
        if (!input.name) {
            input.setCustomValidity('');
            return;
        }
        Array.from(form.elements).forEach(function (field) {
            if (field.name === input.name && typeof field.setCustomValidity === 'function') {
                field.setCustomValidity('');
            }
        });
    }

    function translateServerValidationErrors() {
        const directTranslations = {
            'Please fix the errors.': 'Per favore, correggi gli errori indicati.',
            'This field is required.': 'Per favore, rispondi a questa domanda.',
            'Questo campo è obbligatorio.': 'Per favore, rispondi a questa domanda.',
            'Questo campo è obbligatorio': 'Per favore, rispondi a questa domanda.',
            'Not a valid integer value.': 'Per favore, inserisci un valore valido.',
            'Number must be between 18 and 100.': "Inserisci un'età compresa tra 18 e 100 anni.",
            'Number must be between 0 and 700.': 'Inserisci un importo compreso tra 0 e 700 euro.',
            'Il numero deve essere compreso tra 18 e 100.': "Inserisci un'età compresa tra 18 e 100 anni.",
            'Il numero deve essere compreso tra 0 e 700.': 'Inserisci un importo compreso tra 0 e 700 euro.'
        };
        document.querySelectorAll('.otree-form-errors, .form-control-errors').forEach(function (element) {
            const text = element.textContent.trim();
            if (directTranslations[text]) element.textContent = directTranslations[text];
        });
    }

    function initialiseFormValidation() {
        const form = document.getElementById('form');
        if (!form) return;
        Array.from(form.elements).forEach(function (input) {
            if (typeof input.setCustomValidity !== 'function') return;
            validateMinimumAlphabeticText(input);
            input.addEventListener('invalid', function () {
                input.setCustomValidity('');
                validateMinimumAlphabeticText(input);
                if (!input.validity.valid) {
                    input.setCustomValidity(participantValidationMessage(input));
                }
            });
            ['input', 'change'].forEach(function (eventName) {
                input.addEventListener(eventName, function () {
                    clearValidityForField(form, input);
                    validateMinimumAlphabeticText(input);
                });
            });
        });
        form.addEventListener('submit', function (event) {
            const unanswered = Array.from(form.querySelectorAll('.survey-slider[data-required="true"]'))
                .filter(function (slider) { return slider.dataset.answered !== 'true'; })
                .filter(function (slider) {
                    const exclusiveId = slider.dataset.exclusiveAlternative;
                    return !exclusiveId || !document.getElementById(exclusiveId).checked;
                });
            if (unanswered.length) {
                event.preventDefault();
                const first = unanswered[0];
                unanswered.forEach(function (slider) {
                    const error = slider.querySelector('.survey-client-error');
                    if (error) error.hidden = false;
                });
                first.querySelector('.survey-slider__range').focus();
                first.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    }

    function initialise() {
        document.querySelectorAll('.survey-slider').forEach(initialiseSlider);
        document.querySelectorAll('input[type="number"]').forEach(function (input) {
            input.setAttribute('inputmode', 'numeric');
        });
        initialisePoliticalExclusiveOption();
        initialiseAssociationExclusivity();
        initialiseCollectiveActionDetails();
        translateServerValidationErrors();
        initialiseFormValidation();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialise);
    } else {
        initialise();
    }
})();
