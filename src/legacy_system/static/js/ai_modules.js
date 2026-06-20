/**
 * AI 智能中台前端交互模块
 * =========================
 * 封装所有 AI 功能的前端交互逻辑
 */

var AIModule = (function() {
    'use strict';

    var _cache = {};
    var _loading = {};

    /**
     * 调用 AI 分析接口
     */
    function analyze(expenseId, callbacks) {
        callbacks = callbacks || {};
        if (_loading[expenseId]) return;
        _loading[expenseId] = true;

        var cached = _cache[expenseId];
        if (cached && (Date.now() - cached._ts < 300000)) {
            _loading[expenseId] = false;
            if (callbacks.onSuccess) callbacks.onSuccess(cached);
            return;
        }

        if (callbacks.onStart) callbacks.onStart();

        fetch('/api/ai/analyze/' + expenseId)
            .then(function(r) { return r.json(); })
            .then(function(res) {
                _loading[expenseId] = false;
                if (res.code === 0) {
                    res.data._ts = Date.now();
                    _cache[expenseId] = res.data;
                    if (callbacks.onSuccess) callbacks.onSuccess(res.data);
                } else {
                    if (callbacks.onError) callbacks.onError(res.message);
                }
            })
            .catch(function(e) {
                _loading[expenseId] = false;
                if (callbacks.onError) callbacks.onError(e.message || '请求失败');
            });
    }

    /**
     * 填报助手
     */
    function fillAssist(text, callbacks) {
        callbacks = callbacks || {};
        fetch('/api/ai/fill_assist', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text: text})
        }).then(function(r) { return r.json(); })
        .then(function(res) {
            if (res.code === 0 && callbacks.onSuccess) callbacks.onSuccess(res.data);
            else if (callbacks.onError) callbacks.onError(res.message);
        })
        .catch(function(e) {
            if (callbacks.onError) callbacks.onError(e.message);
        });
    }

    /**
     * 知识问答
     */
    function askQuestion(question, history, callbacks) {
        callbacks = callbacks || {};
        fetch('/api/ai/qa', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question: question, history: history || []})
        }).then(function(r) { return r.json(); })
        .then(function(res) {
            if (res.code === 0 && callbacks.onSuccess) callbacks.onSuccess(res.data);
            else if (callbacks.onError) callbacks.onError(res.message);
        })
        .catch(function(e) {
            if (callbacks.onError) callbacks.onError(e.message);
        });
    }

    /**
     * 合规审计
     */
    function runAudit(days, riskLevel, callbacks) {
        callbacks = callbacks || {};
        fetch('/api/ai/audit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({days: days || 30, risk_level: riskLevel || 'all'})
        }).then(function(r) { return r.json(); })
        .then(function(res) {
            if (res.code === 0 && callbacks.onSuccess) callbacks.onSuccess(res.data);
            else if (callbacks.onError) callbacks.onError(res.message);
        })
        .catch(function(e) {
            if (callbacks.onError) callbacks.onError(e.message);
        });
    }

    /**
     * 数据分析
     */
    function analyzeData(query, callbacks) {
        callbacks = callbacks || {};
        fetch('/api/ai/analysis', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: query})
        }).then(function(r) { return r.json(); })
        .then(function(res) {
            if (res.code === 0 && callbacks.onSuccess) callbacks.onSuccess(res.data);
            else if (callbacks.onError) callbacks.onError(res.message);
        })
        .catch(function(e) {
            if (callbacks.onError) callbacks.onError(e.message);
        });
    }

    /**
     * 渲染 AI 分析结果面板
     */
    function renderAnalysisPanel(data) {
        var info = data.info_check || {};
        var budget = data.budget_check || {};
        var risk = data.risk_analysis || {};
        var decision = data.final_decision || {};

        var ciMap = {
            'auto_approve': '✅ 自动通过',
            'auto_reject': '❌ 自动驳回',
            'manual_review': '👤 转人工审批',
            'error': '⚠️ 分析异常',
        };

        var html = '<div class="space-y-3">';
        html += '<div class="p-3 rounded-lg text-center" style="background:var(--c-primary-bg);border:1px solid var(--c-primary-bd)">';
        html += '<div class="text-lg font-bold">' + (ciMap[decision.conclusion] || decision.conclusion) + '</div>';
        html += '<div class="text-xs mt-1" style="color:var(--c-text-3)">置信度 ' + Math.round((decision.confidence || 0) * 100) + '%</div>';
        html += '</div>';

        if (decision.reasoning) {
            html += '<div class="p-2 rounded bg-gray-50 text-xs" style="color:var(--c-text-2)"><strong>推理：</strong>' + decision.reasoning + '</div>';
        }

        html += '<div class="grid" style="grid-template-columns:1fr 1fr;gap:8px">';
        html += '<div class="p-2 rounded text-xs ' + (info.passed ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700') + '">📋 信息：' + (info.passed ? '通过' : '不通过') + '</div>';
        html += '<div class="p-2 rounded text-xs ' + (budget.passed ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700') + '">💰 预算：' + (budget.passed ? '充足' : '不足') + '</div>';
        html += '</div>';

        var rc = risk.risk_score >= 60 ? 'var(--c-danger)' : risk.risk_score >= 30 ? 'var(--c-warning)' : 'var(--c-success)';
        html += '<div class="p-2 rounded bg-gray-50">';
        html += '<div class="flex items-center justify-between mb-1"><span class="text-xs font-medium">风险评分</span><span class="text-xs font-bold" style="color:' + rc + '">' + (risk.risk_score || 0) + '/100</span></div>';
        html += '<div class="pbar"><div class="pbar-i" style="width:' + (risk.risk_score || 0) + '%;background:' + rc + '"></div></div>';
        html += '</div>';

        if (decision.approval_advice) {
            html += '<div class="p-2 rounded text-xs" style="background:var(--c-primary-bg)"><strong>建议：</strong>' + decision.approval_advice + '</div>';
        }

        html += '</div>';
        return html;
    }

    return {
        analyze: analyze,
        fillAssist: fillAssist,
        askQuestion: askQuestion,
        runAudit: runAudit,
        analyzeData: analyzeData,
        renderAnalysisPanel: renderAnalysisPanel,
        renderLoading: function() {
            return '<div class="text-center py-4"><div class="inline-block w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mb-2"></div><p class="text-sm" style="color:var(--c-text-3)">AI 分析中...</p></div>';
        },
        renderError: function(msg) {
            return '<div class="text-center py-4"><p class="text-sm text-red-500">' + (msg || '分析失败') + '</p></div>';
        },
    };
})();
