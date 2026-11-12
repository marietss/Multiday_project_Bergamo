(function () {
    'use strict';
    function normalize(value) {
        return value.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
    }
    function search(rows, query) {
        const key = normalize(query);
        return key ? rows.filter(row => normalize(row.name + row.province_abbreviation).includes(key)) : [];
    }
    // Also expose the identical matching algorithm to the Node regression tests.
    if (typeof module !== 'undefined') module.exports = { normalize, search };
    if (typeof document === 'undefined') return;
    const wrapper = document.querySelector('[data-municipality-url]');
    if (!wrapper) return;
    const input = document.getElementById('municipality-search');
    const name = document.getElementById('id_current_municipality');
    const code = document.getElementById('id_current_municipality_istat_code');
    name.type = 'hidden';
    code.type = 'hidden';
    const list = document.getElementById('municipality-results');
    const status = document.getElementById('municipality-status');
    const message = 'Seleziona un comune dall’elenco.';
    let rows = [], matches = [], active = -1, selected = null;
    function label(row) { return row.name + ' (' + row.province_abbreviation + ')'; }
    function validate() {
        const valid = selected && input.value === label(selected) && name.value === selected.name && code.value === selected.istat_code;
        input.setCustomValidity(valid ? '' : message);
        return Boolean(valid);
    }
    function close() {
        list.hidden = true;
        input.setAttribute('aria-expanded', 'false');
        input.removeAttribute('aria-activedescendant');
        active = -1;
    }
    function choose(row) {
        selected = row;
        name.value = row.name;
        code.value = row.istat_code;
        input.value = label(row);
        validate();
        close();
        status.textContent = '';
    }
    function render() {
        matches = search(rows, input.value);
        list.replaceChildren();
        active = -1;
        input.removeAttribute('aria-activedescendant');
        // All matches remain available by scrolling; never silently truncate data.
        matches.forEach((row, index) => {
            const item = document.createElement('li');
            item.id = 'municipality-option-' + index;
            item.setAttribute('role', 'option');
            item.setAttribute('aria-selected', 'false');
            item.textContent = label(row);
            item.addEventListener('mousedown', event => event.preventDefault());
            item.addEventListener('click', () => choose(row));
            list.appendChild(item);
        });
        list.hidden = !matches.length;
        input.setAttribute('aria-expanded', String(matches.length > 0));
        status.textContent = matches.length ? matches.length + ' comuni trovati. Seleziona un risultato.' :
            (input.value ? 'Nessun comune trovato.' : 'Digita il nome del comune e seleziona un risultato.');
    }
    input.addEventListener('input', () => {
        selected = null; name.value = ''; code.value = '';
        validate(); render();
    });
    input.addEventListener('focus', () => { if (!selected) render(); });
    input.addEventListener('blur', () => window.setTimeout(close, 150));
    input.addEventListener('keydown', event => {
        if (event.key === 'Escape') { close(); return; }
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            event.preventDefault();
            if (list.hidden) render();
            if (!matches.length) return;
            active = (active + (event.key === 'ArrowDown' ? 1 : -1) + matches.length) % matches.length;
            Array.from(list.children).forEach((item, index) => item.setAttribute('aria-selected', String(index === active)));
            input.setAttribute('aria-activedescendant', list.children[active].id);
            list.children[active].scrollIntoView({ block: 'nearest' });
        }
        if (event.key === 'Enter' && !list.hidden) {
            event.preventDefault();
            if (active >= 0) choose(matches[active]);
        }
    });
    input.form.addEventListener('submit', event => {
        if (!validate()) { event.preventDefault(); input.reportValidity(); }
    });
    input.setCustomValidity(message);
    input.disabled = true;
    status.textContent = 'Caricamento dei comuni…';
    fetch(wrapper.dataset.municipalityUrl).then(response => {
        if (!response.ok) throw new Error('Dataset unavailable');
        return response.json();
    }).then(data => {
        rows = data;
        input.disabled = false;
        const restored = rows.find(row => row.istat_code === code.value && row.name === name.value);
        if (restored) choose(restored);
        else { name.value = ''; code.value = ''; render(); }
    }).catch(() => {
        input.disabled = false;
        status.textContent = 'Impossibile caricare i comuni. Ricarica la pagina per riprovare.';
    });
})();
