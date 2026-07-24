async function doLogin(username, password) {
    await api('POST', '/api/auth/login', { username, password });
    window.location.href = '/problems';
}
async function doRegister(username, password) {
    await api('POST', '/api/auth/register', { username, password });
}
async function doLogout() {
    try { await api('POST', '/api/auth/logout', {}); }
    catch (e) { }
    window.location.href = '/login';
}
async function getCurrentUser() {
    try {
        const r = await api('GET', '/api/auth/me');
        return r && r.data ? r.data : null;
    } catch (e) {
        if (e.code === 401) return null;
        if (e.code === 403) return { disabled: true, message: e.message };
        throw e;
    }
}
async function requireLogin() {
    const user = await getCurrentUser();
    if (!user) {
        window.location.href = '/login';
        return null;
    }
    return user;
}
async function requireRole(roles) {
    const user = await requireLogin();
    if (!user) return null;
    if (!roles.includes(user.role)) {
        const main = document.querySelector('main.container');
        if (main) {
            main.innerHTML = '<section class="card"><h1>403</h1><p>权限不足，需要角色：' + roles.join(' 或 ') + '</p></section>';
        }
        return null;
    }
    return user;
}
function renderNav(user) {
    const nav = document.getElementById('nav-links');
    const info = document.getElementById('user-info');
    const logoutBtn = document.getElementById('logout-btn');
    if (!nav) return;
    nav.innerHTML = '';
    if (!user) {
        if (info) info.textContent = '';
        if (logoutBtn) logoutBtn.style.display = 'none';
        return;
    }
    if (info) info.textContent = user.username + ' (' + user.role + ')';
    if (logoutBtn) logoutBtn.style.display = 'inline-block';
    const links = [
        { href: '/problems', text: '题目列表' },
    ];
    if (user.role === 'student') {
        links.push({ href: '/submissions', text: '我的提交' });
    } else {
        links.push({ href: '/submissions', text: '全部提交记录' });
    }
    if (user.role === 'teacher' || user.role === 'admin') {
        links.push({ href: '/teacher/problems', text: '题目管理' });
        links.push({ href: '/admin/logs', text: '测试点日志' });
    }
    if (user.role === 'admin') {
        links.push({ href: '/admin/users', text: '用户管理' });
        links.push({ href: '/admin/audit-logs', text: '审计日志' });
        links.push({ href: '/admin/backups', text: '备份管理' });
    }
    for (const l of links) {
        const a = document.createElement('a');
        a.href = l.href;
        a.textContent = l.text;
        nav.appendChild(a);
    }
}
async function refreshNav() {
    const user = await getCurrentUser();
    renderNav(user);
    return user;
}
(async function init() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', refreshNav);
    } else {
        await refreshNav();
    }
})();
