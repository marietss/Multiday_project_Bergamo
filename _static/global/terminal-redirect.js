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
        window.setTimeout(redirect, 1500);
    }
})();
