function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}
async function loadTeacherProblems() {
    const loading = document.getElementById('loading');
    const table = document.getElementById('problems-table');
    const empty = document.getElementById('empty');
    const body = document.getElementById('problems-body');
    try {
        const r = await api('GET', '/api/problems?page=1&page_size=100');
        const items = (r && r.data && r.data.items) || [];
        if (loading) loading.style.display = 'none';
        if (items.length === 0) {
            if (empty) empty.style.display = '';
            return;
        }
        body.innerHTML = items.map(p => `
            <tr>
                <td>${escapeHtml(p.id)}</td>
                <td>${escapeHtml(p.title)}</td>
                <td><span class="badge badge-${p.difficulty}">${p.difficulty}</span></td>
                <td>-</td>
                <td class="muted">-</td>
                <td>
                    <a href="/teacher/problems/${encodeURIComponent(p.id)}/edit" class="btn">编辑</a>
                    <button class="btn btn-danger" onclick="deleteProblem('${escapeHtml(p.id)}', '${escapeHtml(p.title)}')">删除</button>
                </td>
            </tr>
        `).join('');
        if (table) table.style.display = '';
    } catch (e) {
        if (loading) loading.textContent = '加载失败：' + e.message;
        showError(e.message);
    }
}
async function deleteProblem(pid, title) {
    if (!confirm(`确认删除题目 ${pid} (${title}) ？\n历史提交和日志会保留，但题目配置和测试点会被清除。`)) return;
    try {
        await api('DELETE', '/api/problems/' + encodeURIComponent(pid));
        await loadTeacherProblems();
    } catch (e) {
        showError('删除失败：' + e.message);
    }
}
