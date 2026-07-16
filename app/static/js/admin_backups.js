function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}
function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
}
async function loadBackups() {
    const loading = document.getElementById('loading');
    const table = document.getElementById('backups-table');
    const empty = document.getElementById('empty');
    const body = document.getElementById('backups-body');
    try {
        const r = await api('GET', '/api/admin/backups');
        const items = (r && r.data && r.data.items) || [];
        if (loading) loading.style.display = 'none';
        if (items.length === 0) {
            if (empty) empty.style.display = '';
            return;
        }
        body.innerHTML = items.map(b => `
            <tr>
                <td><code>${escapeHtml(b.backup_id)}</code></td>
                <td>${escapeHtml(b.created_at)}</td>
                <td>${escapeHtml(b.storage_type)}</td>
                <td>${b.file_count}</td>
                <td>${formatSize(b.total_size_bytes)}</td>
                <td><button class="btn btn-danger" onclick="restoreBackup('${escapeHtml(b.backup_id)}')">恢复</button></td>
            </tr>
        `).join('');
        if (table) table.style.display = '';
    } catch (e) {
        if (loading) loading.textContent = '加载失败：' + e.message;
        showError(e.message);
    }
}
async function createBackup() {
    try {
        const r = await api('POST', '/api/admin/backups');
        const flash = document.getElementById('flash');
        flash.className = 'flash flash-info';
        flash.style.display = '';
        flash.textContent = '备份已创建：' + r.data.backup_id;
        await loadBackups();
    } catch (e) {
        showError('创建失败：' + e.message);
    }
}
async function restoreBackup(backupId) {
    if (!confirm(`确认从备份 ${backupId} 恢复？\n当前数据会被备份内容替换。`)) return;
    const flash = document.getElementById('flash');
    flash.className = 'flash flash-warn';
    flash.style.display = '';
    flash.textContent = '正在恢复，请稍候...';
    try {
        await api('POST', '/api/admin/backups/' + encodeURIComponent(backupId) + '/restore');
        flash.className = 'flash flash-info';
        flash.textContent = '恢复成功：' + backupId;
    } catch (e) {
        flash.className = 'flash flash-error';
        flash.textContent = '恢复失败：' + e.message;
    }
}
