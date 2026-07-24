function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}
function fmtPct(v) {
    if (v === null || v === undefined) return '-';
    return (Number(v) * 100).toFixed(2) + '%';
}
async function loadReports(pid) {
    const loading = document.getElementById('loading');
    const table = document.getElementById('sim-table');
    const empty = document.getElementById('empty');
    const body = document.getElementById('sim-body');
    try {
        const r = await api('GET', '/api/problems/' + encodeURIComponent(pid) + '/similarity-reports');
        const items = (r && r.data && r.data.items) || [];
        if (loading) loading.style.display = 'none';
        if (empty) empty.style.display = 'none';
        if (items.length === 0) {
            if (empty) empty.style.display = '';
            if (table) table.style.display = 'none';
            return;
        }
        body.innerHTML = items.map(s => `
            <tr>
                <td><a href="/submissions/${encodeURIComponent(s.submission_a)}">${escapeHtml(s.submission_a)}</a></td>
                <td><a href="/submissions/${encodeURIComponent(s.submission_b)}">${escapeHtml(s.submission_b)}</a></td>
                <td>${fmtPct(s.similarity)}</td>
                <td>${escapeHtml(s.method)}</td>
                <td>${escapeHtml(s.created_at)}</td>
            </tr>
        `).join('');
        if (table) table.style.display = '';
    } catch (e) {
        if (loading) loading.textContent = '加载失败：' + e.message;
        showError(e.message);
    }
}
async function runCheck(pid) {
    const btn = document.getElementById('run-btn');
    const msg = document.getElementById('run-msg');
    const thresholdInput = document.getElementById('threshold');
    if (btn) btn.disabled = true;
    if (msg) msg.textContent = '检测中...';
    const t = thresholdInput ? thresholdInput.value : '';
    const url = '/api/problems/' + encodeURIComponent(pid) + '/similarity-check'
        + (t ? ('?threshold=' + encodeURIComponent(t)) : '');
    try {
        const r = await api('POST', url);
        const d = (r && r.data) || {};
        if (msg) {
            msg.textContent = `完成：比对 ${d.compared_count} 份提交，发现 ${d.report_count} 对相似（阈值 ${(Number(d.threshold) * 100).toFixed(0)}%）`;
        }
        await loadReports(pid);
    } catch (e) {
        if (msg) msg.textContent = '检测失败：' + e.message;
        showError(e.message);
    } finally {
        if (btn) btn.disabled = false;
    }
}
