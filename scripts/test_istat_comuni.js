const assert = require('node:assert/strict');
const rows = require('../_static/global/istat_comuni.json');
const {search, normalize} = require('../_static/global/municipality.js');
assert.equal(rows.length, 7894);
assert.equal(new Set(rows.map(r => r.istat_code)).size, 7894);
assert(search(rows, 'Bolo').some(r => r.name === 'Bologna' && r.province_abbreviation === 'BO'));
// Exercise every row, including all punctuation/Unicode names and dataset ends.
for (const row of rows) {
    assert(search(rows, normalize(row.name)).some(r => r.istat_code === row.istat_code));
}
for (const name of ['Samone', 'Livo', 'Peglio', 'Castro', 'San Teodoro']) {
    const duplicates = rows.filter(r => r.name === name);
    assert.equal(duplicates.length, 2);
    assert.equal(new Set(duplicates.map(r => r.province_abbreviation)).size, 2);
}
assert.equal(search(rows, 'zzzznotamunicipality').length, 0);
console.log('All 7,894 municipalities retrievable with normalized search; duplicate names preserved.');

// Lightweight DOM harness exercises the actual shipped component's event
// handlers (selection, edits, keyboard, and restoration), without dependencies.
const vm = require('node:vm');
const fs = require('node:fs');
class Element {
    constructor() { this.value = ''; this.children = []; this.events = {}; this.attributes = {}; this.hidden = false; }
    addEventListener(name, fn) { (this.events[name] ||= []).push(fn); }
    fire(name, event = {}) { for (const fn of this.events[name] || []) fn(event); }
    setAttribute(key, value) { this.attributes[key] = value; }
    removeAttribute(key) { delete this.attributes[key]; }
    setCustomValidity(value) { this.validationMessage = value; }
    replaceChildren() { this.children = []; }
    appendChild(child) { this.children.push(child); }
    scrollIntoView() {}
    reportValidity() {}
}
async function component(name = '', code = '') {
    const elements = Object.fromEntries(['municipality-search', 'id_current_municipality',
        'id_current_municipality_istat_code', 'municipality-results', 'municipality-status']
        .map(key => [key, new Element()]));
    elements['id_current_municipality'].value = name;
    elements['id_current_municipality_istat_code'].value = code;
    elements['municipality-search'].form = new Element();
    const document = {
        querySelector: () => ({dataset: {municipalityUrl: 'bundled.json'}}),
        getElementById: key => elements[key], createElement: () => new Element(),
    };
    vm.runInNewContext(fs.readFileSync(require.resolve('../_static/global/municipality.js'), 'utf8'), {
        document, fetch: async () => ({ok: true, json: async () => rows}),
        window: {setTimeout: fn => fn()},
    });
    await new Promise(resolve => setImmediate(resolve));
    return elements;
}
(async () => {
    const elements = await component();
    const input = elements['municipality-search'];
    input.value = 'Bolo'; input.fire('input');
    assert.equal(elements['id_current_municipality_istat_code'].value, '');
    let prevented = false;
    input.form.fire('submit', {preventDefault: () => { prevented = true; }});
    assert(prevented);
    const option = elements['municipality-results'].children.find(e => e.textContent === 'Bologna (BO)');
    assert(option); option.fire('click');
    assert.equal(input.value, 'Bologna (BO)');
    assert.equal(input.validationMessage, '');
    assert.equal(elements['id_current_municipality'].value, 'Bologna');
    assert.equal(elements['id_current_municipality_istat_code'].value, '037006');
    input.value = 'Bologna edited'; input.fire('input');
    assert.equal(elements['id_current_municipality'].value, '');
    assert.equal(elements['id_current_municipality_istat_code'].value, '');
    assert.equal(input.validationMessage, 'Seleziona un comune dall’elenco.');
    input.value = 'Bologna'; input.fire('input');
    input.fire('keydown', {key: 'ArrowDown', preventDefault() {}});
    input.fire('keydown', {key: 'Enter', preventDefault() {}});
    assert.equal(elements['id_current_municipality_istat_code'].value, '037006');
    const restored = await component('Bologna', '037006');
    assert.equal(restored['municipality-search'].value, 'Bologna (BO)');
    console.log('Component selection, keyboard, unselected rejection, editing invalidation and restoration passed.');
})().catch(error => { console.error(error); process.exitCode = 1; });
