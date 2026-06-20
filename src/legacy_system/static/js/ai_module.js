/**
 * AI 智能审批前端交互模块
 * =========================
 * 封装与 AI 服务的交互逻辑，供各页面复用
 */

var AIModule = (function() {
    'use strict';

    var _cache = {};
    var _loading = {};

    /**
     * 调用 AI 分析接口
     * @param {number} expenseId 报销单 ID
     * @param {object} callbacks { onStart, onSuccess, onError }
     */
    function analyze(expenseId, callbacks) {
        callbacks = callbacks || {};

        // 防重复提交
        if (_loading[expenseId]) return;
        _loading[expenseId] = true;

        // 检查缓存（5 分钟有效）
        var cached = _cache[expenseId];
        if (cached && (Date.now() - cached._ts < 300000)) {
            _loading[expenseId] = false;
            if (callbacks.onSuccess) callbacks.onSuccess(cached);
            return cached;
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
     * 渲染 AI 分析结果为 HTML
     * @param {object} data analyze 返回的数据
     * @returns {string} HTML 字符串
     */
    function renderResult(data) {
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

        // 决策结论
        html += '<div class="p-3 rounded-lg text-center" style="background:var(--c-primary-bg);border:1px solid var(--c-primary-bd)">';
        html += '<div class="text-lg font-bold">' + (ciMap[decision.conclusion] || decision.conclusion) + '</div>';
        html += '<div class="text-xs mt-1" style="color:var(--c-text-3)">置信度 ' + Math.round((decision.confidence || 0) * 100) + '%</div>';
        html += '</div>';

        // 推理过程
        if (decision.reasoning) {
            html += '<div class="p-2 rounded bg-gray-50 text-xs" style="color:var(--c-text-2)"><strong>推理：</strong>' + decision.reasoning + '</div>';
        }

        // 校验结果
        html += '<div class="grid" style="grid-template-columns:1fr 1fr;gap:8px">';
        html += '<div class="p-2 rounded text-xs ' + (info.passed ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700') + '">📋 信息：' + (info.passed ? '通过' : '不通过') + '</div>';
        html += '<div class="p-2 rounded text-xs ' + (budget.passed ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700') + '">💰 预算：' + (budget.passed ? '充足' : '不足') + '</div>';
        html += '</div>';

        // 风险评分
        var rc = risk.risk_score >= 60 ? 'var(--c-danger)' : risk.risk_score >= 30 ? 'var(--c-warning)' : 'var(--c-success)';
        html += '<div class="p-2 rounded bg-gray-50">';
        html += '<div class="flex items-center justify-between mb-1"><span class="text-xs font-medium">风险评分</span><span class="text-xs font-bold" style="color:' + rc + '">' + (risk.risk_score || 0) + '/100</span></div>';
        html += '<div class="pbar"><div class="pbar-i" style="width:' + (risk.risk_score || 0) + '%;background:' + rc + '"></div></div>';
        html += '</div>';

        // 审批建议
        if (decision.approval_advice) {
            html += '<div class="p-2 rounded text-xs" style="background:var(--c-primary-bg)"><strong>建议：</strong>' + decision.approval_advice + '</div>';
        }

        html += '</div>';
        return html;
    }

    /**
     * 渲染加载中状态
     */
    function renderLoading() {
        return '<div class="text-center py-4"><div class="inline-block w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mb-2"></div><p class="text-sm" style="color:var(--c-text-3)">AI 分析中...</p></div>';
    }

    /**
     * 渲染错误状态
     */
    function renderError(message) {
        return '<div class="text-center py-4"><p class="text-sm text-red-500">' + (message || '分析失败') + '</p></div>';
    }

    /**
     * 渲染空状态
     */
    function renderEmpty() {
        return '<div class="text-center py-4" style="color:var(--c-text-3)"><svg class="w-10 h-10 mx-auto mb-2 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg><p class="text-sm">点击「一键分析」获取 AI 审批建议</p></div>';
    }

    // 公开 API
    return {
        analyze: analyze,
        renderResult: renderResult,
        renderLoading: renderLoading,
        renderError: renderError,
        renderEmpty: renderEmpty,
    };
})();
