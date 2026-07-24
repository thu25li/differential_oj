function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}
let currentPage = 1;
let currentPageSize = 20;
function buildQuery(page) {
    const params = new URLSearchParams();
    params.set('page', page);
    params.set('page_size', currentPageSize);
    const op = document.getElementById('filter-operator').value.trim();
    const action = document.getElementById('filter-action').value;
    const start = document.getElementById('filter-start').value.trim();
    const end = document.getElementById('filter-end').value.trim();
    if (op) params.set('operator_username', op);
    if (action) params.set('action', action);
    if (start) params.set('start_time', start);
    if (end) params.set('end_time', end);
    return params.toString();
}
async function loadAuditLogs(page) {
    currentPage = page;
    const loading = document.getElementById('loading');
    const table = document.getElementById('logs-table');
    const empty = document.getElementById('empty');
    const body = document.getElementById('logs-body');
    const pager = document.getElementById('pager');
    try {
        const qs = buildQuery(page);
        const r = await api('GET', '/api/audit-logs?' + qs);
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
        body.innerHTML = items.map(a => `
            <tr>
                <td>${escapeHtml(a.created_at)}</td>
                <td>${escapeHtml(a.operator_username || a.operator_id)}</td>
                <td><span class="badge">${escapeHtml(a.action)}</span></td>
                <td>${escapeHtml(a.target_type)}</td>
                <td>${escapeHtml(a.target_id || '-')}</td>
                <td>${a.success ? '<span class="badge badge-active">成功</span>' : '<span class="badge badge-failed">失败</span>'}</td>
                <td>${escapeHtml(a.detail || '')}</td>
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
    document.getElementById('filter-operator').value = '';
    document.getElementById('filter-action').value = '';
    document.getElementById('filter-start').value = '';
    document.getElementById('filter-end').value = '';
    loadAuditLogs(1);
}
