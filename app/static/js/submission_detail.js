function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}
function renderStatus(status) {
    return '<span class="badge badge-' + status + '">' + status + '</span>';
}
function renderResult(result) {
    if (!result) return '<span class="muted">（评测中）</span>';
    return '<span class="badge badge-' + result.toLowerCase() + '">' + result + '</span>';
}
async function fetchSubmission(sid) {
    return await api('GET', '/api/submissions/' + encodeURIComponent(sid));
}
async function fetchLogs(sid) {
    try {
        return await api('GET', '/api/submissions/' + encodeURIComponent(sid) + '/logs');
    } catch (e) {
        return null;
    }
}
function renderSubmission(sub) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('body').style.display = '';
    const pl = document.getElementById('problem-link');
    pl.textContent = sub.problem_id;
    pl.href = '/problems/' + encodeURIComponent(sub.problem_id);
    document.getElementById('status').outerHTML = '<span id="status" class="badge badge-' + sub.status + '">' + sub.status + '</span>';
    const resultEl = document.getElementById('result');
    if (sub.result) {
        resultEl.outerHTML = '<span id="result"><span class="badge badge-' + sub.result.toLowerCase() + '">' + sub.result + '</span></span>';
    } else {
        resultEl.textContent = '（评测中）';
    }
    document.getElementById('score').textContent = sub.score;
    document.getElementById('total-time').textContent = sub.total_time === null || sub.total_time === undefined ? '（评测中）' : (sub.total_time + 's');
    const hint = document.getElementById('hint');
    if (sub.status === 'pending' || sub.status === 'running') {
        hint.textContent = '正在评测，请稍候...';
    } else {
        hint.textContent = '';
    }
}
function renderCases(cases) {
    const el = document.getElementById('cases');
    if (!cases || cases.length === 0) {
        el.innerHTML = '<p class="muted">暂无测试点日志</p>';
        return;
    }
    el.innerHTML = cases.map((c, i) => {
        const parts = [`<div class="case-item">`];
        parts.push(`<div class="case-header"><strong>#${i + 1} ${escapeHtml(c.case_id)}</strong> ${renderResult(c.result)} ${c.is_hidden ? '<span class="tag">hidden</span>' : ''}</div>`);
        parts.push(`<div class="case-field"><strong>得分：</strong>${c.score}</div>`);
        parts.push(`<div class="case-field"><strong>用时：</strong>${c.time_used}s</div>`);
        if (c.message) parts.push(`<div class="case-field"><strong>说明：</strong>${escapeHtml(c.message)}</div>`);
        if (c.stdout !== undefined && c.stdout !== null) {
            parts.push(`<div class="case-field"><strong>你的输出：</strong><pre>${escapeHtml(c.stdout)}</pre></div>`);
        }
        if (c.expected_output !== undefined && c.expected_output !== null) {
            parts.push(`<div class="case-field"><strong>期望输出：</strong><pre>${escapeHtml(c.expected_output)}</pre></div>`);
        }
        if (c.stderr) {
            parts.push(`<div class="case-field"><strong>错误输出：</strong><pre>${escapeHtml(c.stderr)}</pre></div>`);
        }
        parts.push(`</div>`);
        return parts.join('');
    }).join('');
}
async function pollSubmission(sid) {
    let done = false;
    while (!done) {
        try {
            const r = await fetchSubmission(sid);
            const sub = r && r.data;
            if (!sub) {
                document.getElementById('loading').textContent = '提交不存在';
                return;
            }
            renderSubmission(sub);
            if (sub.status === 'finished' || sub.status === 'failed') {
                done = true;
                const logs = await fetchLogs(sid);
                renderCases(logs && logs.data ? logs.data.cases : []);
            } else {
                await new Promise(r => setTimeout(r, 800));
            }
        } catch (e) {
            document.getElementById('loading').textContent = '加载失败：' + e.message;
            return;
        }
    }
}
