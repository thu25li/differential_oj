function parseSamples(text) {
    if (!text || !text.trim()) return [];
    const blocks = text.trim().split(/\n\s*\n/);
    return blocks.map(b => {
        const idx = b.indexOf('|||');
        if (idx < 0) return { input: b, output: '' };
        const input = b.substring(0, idx).replace(/\s+$/, '');
        const output = b.substring(idx + 3).replace(/^\s+/, '');
        return { input, output };
    }).filter(s => s.input || s.output);
}
function parseTestCases(text) {
    if (!text || !text.trim()) return [];
    const blocks = text.trim().split(/\n\s*\n/);
    return blocks.map(b => {
        const parts = b.split('|||').map(s => s.replace(/\s+$/, '').replace(/^\s+/, ''));
        if (parts.length < 5) return null;
        return {
            case_id: parts[0],
            input: parts[1],
            output: parts[2],
            score: parseInt(parts[3], 10),
            is_hidden: parts[4].toLowerCase() === 'true',
        };
    }).filter(c => c !== null);
}
function samplesToText(samples) {
    return (samples || []).map(s => s.input + ' ||| ' + s.output).join('\n\n');
}
function testCasesToText(cases) {
    return (cases || []).map(c =>
        c.case_id + ' ||| ' + c.input + ' ||| ' + c.output + ' ||| ' + c.score + ' ||| ' + (c.is_hidden ? 'true' : 'false')
    ).join('\n\n');
}
async function initForm(mode, problemId) {
    if (mode !== 'edit') return;
    try {
        const r = await api('GET', '/api/problems/' + encodeURIComponent(problemId));
        const p = r && r.data;
        if (!p) {
            showError('题目不存在');
            return;
        }
        document.getElementById('title').value = p.title || '';
        document.getElementById('description').value = p.description || '';
        document.getElementById('input_description').value = p.input_description || '';
        document.getElementById('output_description').value = p.output_description || '';
        document.getElementById('samples').value = samplesToText(p.samples);
        document.getElementById('constraints').value = p.constraints || '';
        document.getElementById('time_limit').value = p.time_limit;
        document.getElementById('memory_limit').value = p.memory_limit;
        document.getElementById('difficulty').value = p.difficulty;
        document.getElementById('tags').value = (p.tags || []).join(', ');
        if (p.test_cases) {
            document.getElementById('test_cases').value = testCasesToText(p.test_cases);
        }
    } catch (e) {
        showError('加载题目失败：' + e.message);
    }
}
async function handleSubmit() {
    const errorEl = document.getElementById('error-msg');
    errorEl.textContent = '';
    const mode = window.location.pathname.includes('/new') ? 'create' : 'edit';
    const problemId = mode === 'edit' ? window.location.pathname.split('/')[3] : null;
    const title = document.getElementById('title').value;
    const description = document.getElementById('description').value;
    const input_description = document.getElementById('input_description').value;
    const output_description = document.getElementById('output_description').value;
    const constraints = document.getElementById('constraints').value || null;
    const time_limit = parseFloat(document.getElementById('time_limit').value);
    const memory_limit = parseInt(document.getElementById('memory_limit').value, 10);
    const difficulty = document.getElementById('difficulty').value;
    const tags = document.getElementById('tags').value.split(',').map(t => t.trim()).filter(t => t);
    const samples = parseSamples(document.getElementById('samples').value);
    const test_cases = parseTestCases(document.getElementById('test_cases').value);
    if (samples.length === 0) {
        errorEl.textContent = '至少需要一个样例';
        return;
    }
    if (test_cases.length === 0) {
        errorEl.textContent = '至少需要一个测试点';
        return;
    }
    const scoreSum = test_cases.reduce((a, c) => a + (c.score || 0), 0);
    if (scoreSum !== 100) {
        errorEl.textContent = '测试点分值总和必须为 100，当前为 ' + scoreSum;
        return;
    }
    const payload = {
        title, description, input_description, output_description,
        samples, constraints, time_limit, memory_limit, difficulty, tags, test_cases,
    };
    try {
        if (mode === 'create') {
            payload.id = document.getElementById('id').value;
            await api('POST', '/api/problems', payload);
        } else {
            await api('PUT', '/api/problems/' + encodeURIComponent(problemId), payload);
        }
        window.location.href = '/teacher/problems';
    } catch (e) {
        errorEl.textContent = e.message;
    }
}
