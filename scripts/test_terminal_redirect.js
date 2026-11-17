// Test the shipped script against automatic/manual races without external requests.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../_static/global/terminal-redirect.js'), 'utf8');
for (const first of ['automatic', 'fallback']) {
    const destinations = [];
    let timer, click;
    const url = 'https://survey.maximiles.com/static-complete?p=177137_7285c59a';
    const link = {href: url, addEventListener: (event, callback) => { click = callback; }};
    vm.runInNewContext(source, {
        document: {getElementById: id => id === 'terminal-redirect' ? link : null},
        window: {
            setTimeout: callback => { timer = callback; },
            location: {replace: destination => destinations.push(destination)},
        },
    });
    const fallback = () => click({preventDefault() {}});
    if (first === 'automatic') { timer(); fallback(); }
    else { fallback(); timer(); }
    fallback(); timer();
    assert.deepEqual(destinations, [url]);
}
vm.runInNewContext(source, {document: {getElementById: () => null}});
console.log('Automatic/fallback ordering: exactly one redirect, no added URL parameters.');
