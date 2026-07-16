function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}
function badgeHtml(value) {
    if (!value) return '<span class="muted">-</span>';
    const v = String(value).toLowerCase();
    return '<span class="badge badge-' + v + '">' + value + '</span>';
}
async function loadMySubmissions() {
    const loading = document.getElementById('loading');
    const table = document.getElementById('subs-table');
    const empty = document.getElementById('empty');
    const body = document.getElementById('subs-body');
    try {
        const r = await api('GET', '/api/submissions?page=1&page_size=50');
        const items = (r && r.data && r.data.items) || [];
        if (loading) loading.style.display = 'none';
        if (items.length === 0) {
            if (empty) empty.style.display = '';
            return;
        }
        body.innerHTML = items.map(s => `
            <tr>
                <td>${escapeHtml(s.created_at)}</td>
                <td><a href="/problems/${encodeURIComponent(s.problem_id)}">${escapeHtml(s.problem_id)}</a></td>
                <td>${badgeHtml(s.status)}</td>
                <td>${badgeHtml(s.result)}</td>
                <td>${s.score}</td>
                <td>${s.total_time === null || s.total_time === undefined ? '-' : (s.total_time + 's')}</td>
                <td><a href="/submissions/${encodeURIComponent(s.id)}">详情</a></td>
            </tr>
        `).join('');
        if (table) table.style.display = '';
    } catch (e) {
        if (loading) loading.textContent = '加载失败：' + e.message;
        showError(e.message);
    }
}
