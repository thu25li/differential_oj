function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}
function difficultyBadge(d) {
    return '<span class="badge badge-' + d + '">' + d + '</span>';
}
async function loadProblems() {
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
                <td><a href="/problems/${encodeURIComponent(p.id)}">${escapeHtml(p.title)}</a></td>
                <td>${difficultyBadge(p.difficulty)}</td>
                <td>${(p.tags || []).map(t => '<span class="tag">' + escapeHtml(t) + '</span>').join('')}</td>
                <td>${p.time_limit}s</td>
                <td>${p.memory_limit}MB</td>
            </tr>
        `).join('');
        if (table) table.style.display = '';
    } catch (e) {
        if (loading) loading.textContent = '加载失败：' + e.message;
        showError(e.message);
    }
}
async function loadProblem(pid) {
    const loading = document.getElementById('loading');
    const body = document.getElementById('problem-body');
    try {
        const r = await api('GET', '/api/problems/' + encodeURIComponent(pid));
        const p = r && r.data;
        if (!p) {
            if (loading) loading.textContent = '题目不存在';
            return;
        }
        document.getElementById('title').textContent = p.id + '. ' + p.title;
        document.getElementById('difficulty').textContent = p.difficulty;
        document.getElementById('difficulty').className = 'badge badge-' + p.difficulty;
        document.getElementById('tags').innerHTML = (p.tags || []).map(t => '<span class="tag">' + escapeHtml(t) + '</span>').join('');
        document.getElementById('time-limit').textContent = p.time_limit;
        document.getElementById('memory-limit').textContent = p.memory_limit;
        document.getElementById('description').textContent = p.description || '';
        document.getElementById('input-description').textContent = p.input_description || '';
        document.getElementById('output-description').textContent = p.output_description || '';
        const samplesEl = document.getElementById('samples');
        samplesEl.innerHTML = (p.samples || []).map((s, i) => `
            <div class="case-item">
                <div class="case-header"><strong>样例 ${i + 1}</strong></div>
                <div class="case-field"><strong>输入：</strong><pre>${escapeHtml(s.input)}</pre></div>
                <div class="case-field"><strong>输出：</strong><pre>${escapeHtml(s.output)}</pre></div>
            </div>
        `).join('');
        document.getElementById('constraints').textContent = p.constraints || '无';
        if (loading) loading.style.display = 'none';
        if (body) body.style.display = '';
    } catch (e) {
        if (loading) loading.textContent = '加载失败：' + e.message;
        if (e.code === 404) {
            showError('题目不存在');
        } else {
            showError(e.message);
        }
    }
}
