async function api(method, url, body) {
    const opts = {
        method: method,
        credentials: 'same-origin',
        headers: {},
    };
    if (body !== undefined && body !== null) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(body);
    }
    let resp;
    try {
        resp = await fetch(url, opts);
    } catch (e) {
        const err = new Error('网络请求失败：' + e.message);
        err.code = 0;
        throw err;
    }
    let data = null;
    const text = await resp.text();
    if (text) {
        try { data = JSON.parse(text); }
        catch (e) { data = null; }
    }
    if (!resp.ok) {
        const msg = (data && data.message) ? data.message : ('请求失败：HTTP ' + resp.status);
        const err = new Error(msg);
        err.code = resp.status;
        err.data = data;
        throw err;
    }
    return data;
}
function showError(msg) {
    const el = document.getElementById('error-msg');
    if (el) el.textContent = msg;
    const flash = document.getElementById('flash');
    if (flash) {
        flash.className = 'flash flash-error';
        flash.textContent = msg;
    }
}
function clearError() {
    const el = document.getElementById('error-msg');
    if (el) el.textContent = '';
    const flash = document.getElementById('flash');
    if (flash) flash.textContent = '';
}
