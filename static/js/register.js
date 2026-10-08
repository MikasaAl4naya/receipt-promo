(function () {
  'use strict';

  var form       = document.getElementById('receipt-form');
  var submitBtn  = document.getElementById('submit-btn');
  var btnText    = submitBtn.querySelector('.btn__text');
  var btnLoading = submitBtn.querySelector('.btn__loading');
  var formMsg    = document.getElementById('form-msg');
  var errGeneral = document.getElementById('err_general');

  /* -------- QR-парсер -------- */
  document.getElementById('qr-btn').addEventListener('click', function () {
    var raw    = document.getElementById('qr_string').value.trim();
    var errEl  = document.getElementById('qr-error');
    errEl.style.display = 'none';

    if (!raw) { errEl.textContent = 'Вставьте строку из QR-кода'; errEl.style.display = 'block'; return; }

    try {
      var str    = raw.indexOf('?') !== -1 ? raw.split('?')[1] : raw;
      var params = {};
      str.split('&').forEach(function (pair) {
        var kv = pair.split('=');
        if (kv[0] && kv[1] !== undefined) params[kv[0]] = decodeURIComponent(kv[1]);
      });

      if (params.t) {
        var t    = params.t;
        var year = t.slice(0, 4), month = t.slice(4, 6), day = t.slice(6, 8);
        var ti   = t.indexOf('T');
        var hour = '00', min = '00';
        if (ti !== -1) { var tp = t.slice(ti + 1); hour = tp.slice(0, 2) || '00'; min = tp.slice(2, 4) || '00'; }
        document.getElementById('id_purchase_date').value = year + '-' + month + '-' + day + 'T' + hour + ':' + min;
      }
      if (params.s)  document.getElementById('id_amount').value = parseFloat(params.s).toFixed(2);
      if (params.fn) document.getElementById('id_fn').value = params.fn;
      if (params.i)  document.getElementById('id_fd').value = params.i;
      if (params.fp) document.getElementById('id_fp').value = params.fp;

    } catch (e) {
      errEl.textContent = 'Не удалось разобрать строку. Проверьте формат.';
      errEl.style.display = 'block';
    }
  });

  /* -------- Правила клиентской валидации -------- */
  var rules = [
    { id: 'id_fn',            errId: 'err_fn',            check: function (v) {
        if (!v) return 'Обязательное поле';
        if (!/^\d{16}$/.test(v)) return 'ФН: ровно 16 цифр';
        return null;
    }},
    { id: 'id_fd',            errId: 'err_fd',            check: function (v) {
        if (!v) return 'Обязательное поле';
        if (!/^\d{1,10}$/.test(v)) return 'ФД: только цифры, до 10 знаков';
        return null;
    }},
    { id: 'id_fp',            errId: 'err_fp',            check: function (v) {
        if (!v) return 'Обязательное поле';
        if (!/^\d{1,10}$/.test(v)) return 'ФП: только цифры, до 10 знаков';
        return null;
    }},
    { id: 'id_purchase_date', errId: 'err_purchase_date', check: function (v) {
        if (!v) return 'Обязательное поле';
        if (isNaN(new Date(v).getTime())) return 'Некорректная дата';
        return null;
    }},
    { id: 'id_amount',        errId: 'err_amount',        check: function (v) {
        if (!v) return 'Обязательное поле';
        if (isNaN(parseFloat(v)) || parseFloat(v) < 1000) return 'Сумма не менее 1 000 ₽';
        return null;
    }},
  ];

  function clearErrors() {
    rules.forEach(function (r) {
      var el  = document.getElementById(r.id);
      var err = document.getElementById(r.errId);
      if (el)  el.classList.remove('field__input--invalid');
      if (err) err.textContent = '';
    });
    formMsg.style.display    = 'none';
    errGeneral.style.display = 'none';
    errGeneral.textContent   = '';
  }

  function validateAll() {
    var ok = true;
    rules.forEach(function (r) {
      var el  = document.getElementById(r.id);
      var err = document.getElementById(r.errId);
      if (!el) return;
      var msg = r.check(el.value.trim());
      if (msg) {
        el.classList.add('field__input--invalid');
        if (err) err.textContent = msg;
        ok = false;
      }
    });
    return ok;
  }

  function setLoading(on) {
    submitBtn.disabled       = on;
    btnText.style.display    = on ? 'none' : '';
    btnLoading.style.display = on ? '' : 'none';
  }

  function getCsrf() {
    var m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
  }

  function showSuccess(msg) {
    formMsg.className   = 'form-msg form-msg--ok';
    formMsg.textContent = msg;
    formMsg.style.display = 'block';
    form.reset();
    formMsg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function showServerErrors(errors) {
    Object.keys(errors).forEach(function (field) {
      var msgs = errors[field].join(' ');
      if (field === '__all__') {
        errGeneral.textContent = msgs;
        errGeneral.style.display = 'block';
        return;
      }
      var el  = document.getElementById('id_' + field);
      var err = document.getElementById('err_' + field);
      if (el)  el.classList.add('field__input--invalid');
      if (err) err.textContent = msgs;
    });
    var first = form.querySelector('.field__input--invalid');
    if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  /* -------- Submit -------- */
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    clearErrors();
    if (!validateAll()) return;
    setLoading(true);

    var fd = new FormData(form);
    fetch(window.location.href, {
      method: 'POST',
      body: fd,
      headers: { 'X-CSRFToken': getCsrf() },
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          showSuccess(data.message || 'Чек успешно зарегистрирован!');
        } else {
          showServerErrors(data.errors || {});
        }
      })
      .catch(function () {
        formMsg.className   = 'form-msg form-msg--error';
        formMsg.textContent = 'Ошибка сети — попробуйте ещё раз.';
        formMsg.style.display = 'block';
      })
      .finally(function () { setLoading(false); });
  });

  /* -------- Валидация по blur -------- */
  rules.forEach(function (r) {
    var el = document.getElementById(r.id);
    if (!el) return;
    el.addEventListener('blur', function () {
      var err = document.getElementById(r.errId);
      var msg = r.check(el.value.trim());
      if (msg) { el.classList.add('field__input--invalid'); if (err) err.textContent = msg; }
      else     { el.classList.remove('field__input--invalid'); if (err) err.textContent = ''; }
    });
  });

})();
