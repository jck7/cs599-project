/**
 * 企业报销管理系统 v2.0 - 公共交互逻辑
 * 职责：侧边栏折叠、Modal、Toast、Tab 切换、全选、HTTP 封装
 */

/* ── 侧边栏折叠 ── */
function toggleSidebar() {
    var sb = document.getElementById('sidebar');
    var ic = document.getElementById('collapseIcon');
    sb.classList.toggle('collapsed');
    if (ic) ic.style.transform = sb.classList.contains('collapsed') ? 'rotate(180deg)' : 'rotate(0)';
}

/* ── Modal ── */
function openModal(id) {
    var m = document.getElementById(id);
    if (m) { m.classList.add('show'); m.onclick = function(e) { if (e.target === m) closeModal(id); }; }
}
function closeModal(id) {
    var m = document.getElementById(id);
    if (m) m.classList.remove('show');
}
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') document.querySelectorAll('.modal.show').forEach(function(m) { m.classList.remove('show'); });
});

/* ── Toast ── */
function showToast(msg, type) {
    type = type || 'info';
    var icons = { ok: '✓', err: '✕', warn: '⚠', info: 'ℹ' };
    var t = document.createElement('div');
    t.className = 'toast toast-' + type;
    t.innerHTML = '<span style="font-weight:700">' + (icons[type] || 'ℹ') + '</span>' + msg;
    document.body.appendChild(t);
    setTimeout(function() { t.remove(); }, 3000);
}

/* ── HTTP ── */
function postJSON(url, data) {
    return fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
        .then(function(r) { return r.json(); });
}

/* ── 金额格式化 ── */
function fmtMoney(n) {
    return parseFloat(n).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/* ── Tab 切换 ── */
function switchTab(group, tab) {
    document.querySelectorAll('[data-tg="' + group + '"]').forEach(function(el) { el.classList.toggle('active', el.dataset.tab === tab); });
    document.querySelectorAll('[data-tc="' + group + '"]').forEach(function(el) { el.classList.toggle('active', el.dataset.tab === tab); });
}

/* ── 全选 ── */
function toggleAll(master, name) {
    var c = document.getElementById(master).checked;
    document.querySelectorAll('input[name="' + name + '"]').forEach(function(cb) { cb.checked = c; });
}
function getChecked(name) {
    var v = [];
    document.querySelectorAll('input[name="' + name + '"]:checked').forEach(function(cb) { v.push(parseInt(cb.value)); });
    return v;
}
