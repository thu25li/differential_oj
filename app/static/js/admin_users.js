function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}
function roleBadge(role) {
    return '<span class="badge badge-' + escapeHtml(role) + '">' + escapeHtml(role) + '</span>';
}
function statusBadge(isActive) {
    return isActive
        ? '<span class="badge badge-active">active</span>'
        : '<span class="badge badge-disabled">disabled</span>';
}
async function loadUsers() {
    const loading = document.getElementById('loading');
    const table = document.getElementById('users-table');
    const empty = document.getElementById('empty');
    const body = document.getElementById('users-body');
    try {
        const r = await api('GET', '/api/users?page=1&page_size=100');
        const items = (r && r.data && r.data.items) || [];
        if (loading) loading.style.display = 'none';
        if (items.length === 0) {
            if (empty) empty.style.display = '';
            return;
        }
        body.innerHTML = items.map(u => {
            const isSelf = window.__currentUser && u.id === window.__currentUser.id;
            return `
            <tr data-uid="${escapeHtml(u.id)}" data-username="${escapeHtml(u.username)}" data-role="${escapeHtml(u.role)}" data-active="${u.is_active ? '1' : '0'}">
                <td>${escapeHtml(u.username)}${isSelf ? ' <span class="muted">(你)</span>' : ''}</td>
                <td>${roleBadge(u.role)}</td>
                <td>${statusBadge(u.is_active)}</td>
                <td>${escapeHtml(u.created_at)}</td>
                <td>
                    ${isSelf ? '<span class="muted">-</span>' : `
                        <button class="btn" onclick="changeRole('${escapeHtml(u.id)}', '${escapeHtml(u.username)}', '${escapeHtml(u.role)}')">改角色</button>
                        <button class="btn ${u.is_active ? 'btn-danger' : 'btn-primary'}" onclick="toggleActive('${escapeHtml(u.id)}', '${escapeHtml(u.username)}', ${u.is_active ? 'true' : 'false'})">${u.is_active ? '禁用' : '启用'}</button>
                        <button class="btn btn-danger" onclick="deleteUser('${escapeHtml(u.id)}', '${escapeHtml(u.username)}', '${escapeHtml(u.role)}')">删除</button>
                    `}
                </td>
            </tr>
            `;
        }).join('');
        if (table) table.style.display = '';
    } catch (e) {
        if (loading) loading.textContent = '加载失败：' + e.message;
        showError(e.message);
    }
}
async function changeRole(uid, username, currentRole) {
    const choices = ['student', 'teacher', 'admin'];
    const next = prompt(`修改 ${username} 的角色（当前：${currentRole}）\n可选：student / teacher / admin`, currentRole);
    if (next === null) return;
    if (!choices.includes(next)) {
        showError('角色必须是 student / teacher / admin');
        return;
    }
    if (next === currentRole) return;
    if (!confirm(`确认将 ${username} 的角色改为 ${next}？`)) return;
    try {
        await api('PUT', '/api/users/' + encodeURIComponent(uid), { role: next });
        await loadUsers();
    } catch (e) {
        showError('修改失败：' + e.message);
    }
}
async function toggleActive(uid, username, isActive) {
    const action = isActive ? '禁用' : '启用';
    if (!confirm(`确认${action}用户 ${username}？`)) return;
    try {
        await api('PUT', '/api/users/' + encodeURIComponent(uid), { is_active: !isActive });
        await loadUsers();
    } catch (e) {
        showError(`${action}失败：` + e.message);
    }
}
async function deleteUser(uid, username, role) {
    if (!confirm(`确认删除用户 ${username}（${role}）？\n该用户的提交和日志会保留，但账号将被永久删除。`)) return;
    try {
        await api('DELETE', '/api/users/' + encodeURIComponent(uid));
        await loadUsers();
    } catch (e) {
        showError('删除失败：' + e.message);
    }
}
