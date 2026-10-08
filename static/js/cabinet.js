/* Обновление статусов чеков без перезагрузки страницы (опрос раз в 15 сек) */
(function () {
  'use strict';

  var pendingIds = [];
  document.querySelectorAll('[data-id]').forEach(function (row) {
    var badge = row.querySelector('[data-badge]');
    if (badge && badge.classList.contains('badge--pending')) {
      pendingIds.push(row.getAttribute('data-id'));
    }
  });

  if (!pendingIds.length) return;

  function escHtml(s) {
    var d = document.createElement('div');
    d.appendChild(document.createTextNode(s));
    return d.innerHTML;
  }

  function poll(id) {
    fetch('/receipts/status/' + id + '/')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var badge  = document.querySelector('[data-badge="' + id + '"]');
        var reason = document.querySelector('[data-reason="' + id + '"]');
        if (!badge) return;

        var newClass = 'badge badge--' + data.status;
        if (badge.className !== newClass || badge.textContent !== data.status_display) {
          badge.className   = newClass;
          badge.textContent = data.status_display;
        }

        if (reason && data.status === 'rejected' && data.rejection_reason) {
          reason.innerHTML = escHtml(data.rejection_reason);
        }

        if (data.status !== 'pending') {
          pendingIds = pendingIds.filter(function (i) { return i !== id; });
        }
      })
      .catch(function () {});
  }

  function tick() {
    pendingIds.forEach(poll);
    if (pendingIds.length) setTimeout(tick, 15000);
  }

  setTimeout(tick, 15000);
})();
