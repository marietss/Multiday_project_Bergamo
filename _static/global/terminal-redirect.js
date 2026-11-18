(function () {
    'use strict';
    const link = document.getElementById('terminal-redirect');
    if (link) {
        let dispatched = false;
        function redirect() {
            if (dispatched) return;
            dispatched = true;
            window.location.replace(link.href);
        }
        link.addEventListener('click', function (event) {
            event.preventDefault();
            redirect();
        });
        const requestedDelay = Number(link.dataset.redirectDelayMs);
        const delay = Number.isFinite(requestedDelay) && requestedDelay > 0 ? requestedDelay : 1500;
        window.setTimeout(redirect, delay);
    }
})();
