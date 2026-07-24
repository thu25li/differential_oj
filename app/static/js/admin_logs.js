function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}
function badge(value) {
    if (!value) return '<span class="muted">-</span>';
    return '<span class="badge badge-' + String(value).toLowerCase() + '">' + value + '</span>';
}
let currentPage = 1;
let currentPageSize = 20;
function buildQuery(page) {
    const params = new URLSearchParams();
    params.set('page', page);
    params.set('page_size', currentPageSize);
    const problem = document.getElementById('filter-problem').value.trim();
    const result = document.getElementById('filter-result').value;
    const start = document.getElementById('filter-start').value.trim();
    const end = document.getElementById('filter-end').value.trim();
    if (problem) params.set('problem_id', problem);
    if (result) params.set('result', result);
    if (start) params.set('start_time', start);
    if (end) params.set('end_time', end);
    return params.toString();
}
async function loadLogs(page) {
    currentPage = page;
    const loading = document.getElementById('loading');
    const table = document.getElementById('logs-table');
    const empty = document.getElementById('empty');
    const body = document.getElementById('logs-body');
    const pager = document.getElementById('pager');
    try {
        const qs = buildQuery(page);
        const r = await api('GET', '/api/logs?' + qs);
        const data = (r && r.data) || {};
        const items = data.items || [];
        const total = data.total || 0;
        if (loading) loading.style.display = 'none';
        if (empty) empty.style.display = 'none';
        if (items.length === 0) {
            if (empty) empty.style.display = '';
            if (table) table.style.display = 'none';
            if (pager) pager.textContent = '';
            return;
        }
        body.innerHTML = items.map(c => `
            <tr>
                <td>${escapeHtml(c.created_at)}</td>
                <td><a href="/submissions/${encodeURIComponent(c.submission_id)}">${escapeHtml(c.submission_id.slice(0, 8))}…</a></td>
                <td>${escapeHtml(c.username || '-')}</td>
                <td>${escapeHtml(c.case_id)}</td>
                <td>${badge(c.result)}</td>
                <td>${c.score}</td>
                <td>${c.time_used}s</td>
                <td>${c.is_hidden ? '是' : '否'}</td>
                <td>${escapeHtml(c.message || '')}</td>
            </tr>
        `).join('');
        if (table) table.style.display = '';
        const totalPages = Math.ceil(total / currentPageSize);
        if (pager) pager.textContent = `第 ${page} / ${totalPages} 页，共 ${total} 条`;
    } catch (e) {
        if (loading) loading.textContent = '加载失败：' + e.message;
        showError(e.message);
    }
}
function resetFilters() {
    document.getElementById('filter-problem').value = '';
    document.getElementById('filter-result').value = '';
    document.getElementById('filter-start').value = '';
    document.getElementById('filter-end').value = '';
    loadLogs(1);
}
