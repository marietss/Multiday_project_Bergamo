(function () {
    'use strict';
    const link = document.getElementById('attention-redirect');
    if (link) {
        window.setTimeout(function () { window.location.assign(link.href); }, 1500);
    }
})();
