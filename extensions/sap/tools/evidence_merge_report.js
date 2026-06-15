#!/usr/bin/env node
/**
 * evidence_merge_report.js — 統合エビデンスレポート生成
 *
 * 個別シナリオ HTML（evidence_SC-*.html）を走査し、
 * サイドメニュー付き統合レポート HTML（evidence_report.html）を生成する。
 *
 * evidence_capture.js とは独立したスクリプト。
 * 全シナリオのエビデンス取得完了後に実行する。
 * 1シナリオだけ再実行した後に再度実行しても正しく統合される。
 *
 * Usage:
 *   node extensions/sap/tools/evidence_merge_report.js <feature_dir>
 *
 * Example:
 *   node extensions/sap/tools/evidence_merge_report.js specs/test_integration/
 *
 * Output:
 *   <feature_dir>/tests/reports/evidence_report.html
 */

'use strict';

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// ---------------------------------------------------------------------------
// evidence_pack_sap.md から s_evidence.scenarios を読み取る
// ---------------------------------------------------------------------------
function loadScenarioResults(featureDir) {
  const sapPath = path.join(featureDir, 'implementation-details', 'evidence_pack_sap.md');
  if (!fs.existsSync(sapPath)) {
    console.warn(`Info: evidence_pack_sap.md が見つかりません。HTML-only モードで続行します`);
    return [];
  }

  const content = fs.readFileSync(sapPath, 'utf-8');
  const yamlMatch = content.match(/```yaml\n([\s\S]*?)```/);
  if (!yamlMatch) {
    console.warn('Info: evidence_pack_sap.md に YAML ブロックが見つかりません。HTML-only モードで続行します');
    return [];
  }

  try {
    const doc = yaml.load(yamlMatch[1]);
    // evidence_pack_sap.md のルートキーは evidence_pack_sap
    const root = doc?.evidence_pack_sap || doc || {};
    const scenarios = root?.s_evidence?.scenarios || [];
    return scenarios.map(sc => ({
      scenarioId: sc.test_id || sc.scenario_id || sc.id || '',
      name: sc.name || '',
      type: sc.type || '',
      status: sc.status || '',
      detail: sc.detail || sc.verification_detail || '',
    }));
  } catch (e) {
    console.error('Error: evidence_pack_sap.md の YAML パースに失敗:', e.message);
    return [];
  }
}

// ---------------------------------------------------------------------------
// reports/ 配下の evidence_SC-*.html からシナリオ一覧を取得
// ---------------------------------------------------------------------------
function discoverScenarioHTMLs(reportDir) {
  if (!fs.existsSync(reportDir)) return [];
  const files = fs.readdirSync(reportDir).filter(f => /^evidence_(SC|TS)[-\w]+\.html$/.test(f));
  files.sort();
  return files.map(f => {
    const id = f.replace(/^evidence_/, '').replace(/\.html$/, '');
    // 個別 HTML からシナリオ名と PASS/FAIL を読み取る
    let name = '';
    let status = '';
    try {
      const html = fs.readFileSync(path.join(reportDir, f), 'utf-8');
      // タイトルから名前を取得: "SC-01: 正常系（...）"
      const titleMatch = html.match(new RegExp(id + ':\\s*(.+?)\\s*<'));
      if (titleMatch) name = titleMatch[1].replace(/<[^>]*>/g, '').trim();
      // PASS/FAIL/NOT_TESTABLE を検出
      if (html.includes('>NOT_TESTABLE<')) status = 'NOT_TESTABLE';
      else if (html.includes('>PASS<')) status = 'PASS';
      else if (html.includes('>FAIL<')) status = 'FAIL';
    } catch (_) {}
    return { scenarioId: id, htmlFile: f, name, status };
  });
}

// ---------------------------------------------------------------------------
// common_class_decisions.yaml 読み取り
// ---------------------------------------------------------------------------
function loadCommonClassDecisions(featureDir) {
  const decPath = path.join(featureDir, 'tests', 'common_class_decisions.yaml');
  if (!fs.existsSync(decPath)) return null;

  try {
    const content = fs.readFileSync(decPath, 'utf-8');
    const doc = yaml.load(content);
    return doc?.common_class_decisions || null;
  } catch (e) {
    console.warn('Warning: common_class_decisions.yaml のパースに失敗:', e.message);
    return null;
  }
}

function renderCommonClassSection(decisions) {
  if (!decisions) return '';

  const usages = decisions.usages || [];
  const exclusions = decisions.exclusions || [];
  const evaluatedAt = decisions.evaluated_at || '';

  let usageRows = '';
  for (const u of usages) {
    usageRows += `<tr>
      <td style="padding:8px 10px;">${u.processing || ''}</td>
      <td style="padding:8px 10px;">${u.rule_id || ''}</td>
      <td style="padding:8px 10px;">${u.class || ''}</td>
      <td style="padding:8px 10px;">${(u.methods || []).join(', ')}</td>
    </tr>`;
  }

  let exclusionRows = '';
  for (const ex of exclusions) {
    const riskColor = ex.risk_assessment === 'high' ? '#c62828'
      : ex.risk_assessment === 'medium' ? '#e65100' : '#2e7d32';
    exclusionRows += `<tr>
      <td style="padding:8px 10px;">${ex.processing || ''}</td>
      <td style="padding:8px 10px;">${ex.rule_id || ''}</td>
      <td style="padding:8px 10px;">${ex.expected_class || ''}</td>
      <td style="padding:8px 10px;">${ex.actual_implementation || ''}</td>
      <td style="padding:8px 10px;">${ex.reason || ''}</td>
      <td style="padding:8px 10px;"><span style="color:${riskColor};font-weight:bold">${ex.risk_assessment || ''}</span></td>
    </tr>`;
  }

  const exclusionAlert = exclusions.length > 0
    ? `<div style="background:#fff3e0;border-left:4px solid #e65100;padding:12px 16px;margin-bottom:16px;border-radius:4px;">
        <strong>\u26a0 \u30ec\u30d3\u30e5\u30fc\u5bfe\u8c61:</strong> ${exclusions.length} \u4ef6\u306e\u51e6\u7406\u3067\u5171\u901a\u30af\u30e9\u30b9\u3092\u4f7f\u7528\u3057\u3066\u3044\u307e\u305b\u3093\u3002\u4e0d\u4f7f\u7528\u7406\u7531\u306e\u59a5\u5f53\u6027\u3092\u78ba\u8a8d\u3057\u3066\u304f\u3060\u3055\u3044\u3002
      </div>`
    : `<div style="background:#e8f5e9;border-left:4px solid #4caf50;padding:12px 16px;margin-bottom:16px;border-radius:4px;">
        \u2713 \u5168\u3066\u306e\u51e6\u7406\u3067\u5171\u901a\u30af\u30e9\u30b9\u3092\u4f7f\u7528\u3057\u3066\u3044\u307e\u3059\u3002
      </div>`;

  return `
    <div id="common-class-section" style="margin-top:32px;">
      <h2 style="font-size:1.2em;border-bottom:2px solid #1565c0;padding-bottom:6px;margin-bottom:12px;color:#1565c0;">\u5171\u901a\u30af\u30e9\u30b9\u4f7f\u7528\u5224\u65ad</h2>
      <p style="font-size:0.85em;color:#666;margin-bottom:12px;">\u8a55\u4fa1\u65e5: ${evaluatedAt} | \u4f7f\u7528: ${usages.length} \u4ef6 | \u4e0d\u4f7f\u7528: ${exclusions.length} \u4ef6</p>
      ${exclusionAlert}
      ${usages.length > 0 ? `
      <h3 style="font-size:1.0em;margin:16px 0 8px;">\u4f7f\u7528\u3057\u305f\u5171\u901a\u30af\u30e9\u30b9</h3>
      <table class="result-table">
        <thead><tr><th>\u51e6\u7406</th><th>\u30eb\u30fc\u30eb</th><th>\u30af\u30e9\u30b9</th><th>\u30e1\u30bd\u30c3\u30c9</th></tr></thead>
        <tbody>${usageRows}</tbody>
      </table>` : ''}
      ${exclusions.length > 0 ? `
      <h3 style="font-size:1.0em;margin:16px 0 8px;color:#e65100;">\u4e0d\u4f7f\u7528\u4e00\u89a7\uff08\u30ec\u30d3\u30e5\u30fc\u5bfe\u8c61\uff09</h3>
      <table class="result-table">
        <thead><tr><th>\u51e6\u7406</th><th>\u30eb\u30fc\u30eb</th><th>\u671f\u5f85\u30af\u30e9\u30b9</th><th>\u5b9f\u969b\u306e\u5b9f\u88c5</th><th>\u4e0d\u4f7f\u7528\u7406\u7531</th><th>\u30ea\u30b9\u30af</th></tr></thead>
        <tbody>${exclusionRows}</tbody>
      </table>` : ''}
    </div>`;
}

// ---------------------------------------------------------------------------
// 統合レポート HTML 生成
// ---------------------------------------------------------------------------
function generateReportHTML(allScenarioResults, commonClassDecisions) {
  const now = new Date().toISOString().replace('T', ' ').substring(0, 19);

  const totalScenarios = allScenarioResults.length;
  const passCount = allScenarioResults.filter(r => r.status === 'PASS').length;
  const failCount = allScenarioResults.filter(r => r.status === 'FAIL').length;
  const ntCount = allScenarioResults.filter(r => r.status === 'NOT_TESTABLE').length;

  let sidebarLinks = '';
  let resultRows = '';

  for (const r of allScenarioResults) {
    const statusIcon = r.status === 'PASS' ? '\u2713' : r.status === 'FAIL' ? '\u2717' : r.status === 'NOT_TESTABLE' ? '\u2014' : '\u2014';
    const statusColor = r.status === 'PASS' ? '#4caf50' : r.status === 'FAIL' ? '#ef5350' : '#9e9e9e';
    const statusBadge = r.status === 'PASS'
      ? '<span style="color:#2e7d32;font-weight:bold">PASS</span>'
      : r.status === 'FAIL'
        ? '<span style="color:#c62828;font-weight:bold">FAIL</span>'
        : r.status === 'NOT_TESTABLE'
          ? '<span style="color:#9e9e9e;font-weight:bold">NOT_TESTABLE</span>'
          : '<span style="color:#999">\u2014</span>';
    const htmlFile = `evidence_${r.scenarioId}.html`;

    sidebarLinks += `
  <a href="#" class="sidebar-link" onclick="showScenario('${htmlFile}', this); return false;">
    <span style="color:${statusColor}">${statusIcon}</span> ${r.scenarioId}: ${r.name || ''}
  </a>`;

    resultRows += `
  <tr>
    <td style="padding:8px 10px;">${r.scenarioId}</td>
    <td style="padding:8px 10px;">${r.name || ''}</td>
    <td style="padding:8px 10px;">${r.type || ''}</td>
    <td style="padding:8px 10px;">${statusBadge}</td>
    <td style="padding:8px 10px;font-size:0.85em;">${r.detail ? r.detail.split(' | ').map(d => {
      const pass = d.startsWith('PASS:');
      const text = d.replace(/^(PASS|FAIL):\s*/, '');
      return `<span style="color:${pass ? '#2e7d32' : '#c62828'}">${pass ? '\u2713' : '\u2717'} ${text}</span>`;
    }).join('<br>') : (r.status === 'PASS' ? '<span style="color:#2e7d32">\u2713 個別 HTML 参照</span>' : r.status === 'FAIL' ? '<span style="color:#c62828">\u2717 個別 HTML 参照</span>' : r.status === 'NOT_TESTABLE' ? '<span style="color:#9e9e9e">\u2014 個別 HTML 参照（テスト制約）</span>' : '\u2014')}</td>
  </tr>`;
  }

  return `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>S3-A1: \u6b63\u5f0f\u30a8\u30d3\u30c7\u30f3\u30b9</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', Arial, sans-serif; background: #f5f5f5; color: #333; display: flex; height: 100vh; }
  .sidebar { width: 280px; min-width: 280px; background: #1a237e; color: #fff; overflow-y: auto; flex-shrink: 0; display: flex; flex-direction: column; }
  .sidebar-header { padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.1); }
  .sidebar-header h2 { font-size: 1.0em; font-weight: 600; margin-bottom: 4px; }
  .sidebar-header .sub { font-size: 0.8em; color: rgba(255,255,255,0.6); }
  .sidebar-nav { flex: 1; overflow-y: auto; }
  .sidebar-section-label { font-size: 0.7em; text-transform: uppercase; letter-spacing: 0.1em; color: rgba(255,255,255,0.4); padding: 12px 16px 4px; }
  .sidebar-link { display: block; padding: 8px 16px; color: rgba(255,255,255,0.8); text-decoration: none; font-size: 0.85em; border-left: 3px solid transparent; }
  .sidebar-link:hover { background: rgba(255,255,255,0.1); }
  .sidebar-link.active { background: rgba(255,255,255,0.15); border-left-color: #fff; color: #fff; }
  .sidebar-summary-link { display: block; padding: 8px 16px; color: rgba(255,255,255,0.8); text-decoration: none; font-size: 0.85em; font-weight: 600; border-left: 3px solid transparent; }
  .sidebar-summary-link:hover { background: rgba(255,255,255,0.1); }
  .sidebar-summary-link.active { background: rgba(255,255,255,0.15); border-left-color: #fff; color: #fff; }
  .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
  #summary-page { flex: 1; overflow-y: auto; padding: 24px 32px; }
  #scenario-frame { flex: 1; border: none; display: none; }
  h1 { font-size: 1.5em; margin-bottom: 16px; border-bottom: 2px solid #1a237e; padding-bottom: 8px; }
  .summary-cards { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
  .summary-card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); min-width: 160px; }
  .summary-card .label { font-size: 0.85em; color: #666; }
  .summary-card .value { font-size: 1.1em; font-weight: bold; margin-top: 4px; }
  .result-table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.12); }
  .result-table th { background: #e8eaf6; padding: 10px; text-align: left; font-size: 0.85em; color: #283593; }
  .result-table td { border-top: 1px solid #eee; }
  .footer { padding: 12px; text-align: center; font-size: 0.8em; color: #999; }
  @media print { .sidebar { display: none; } }
</style>
<script>
function showSummary(link) {
  document.getElementById('summary-page').style.display = 'block';
  document.getElementById('scenario-frame').style.display = 'none';
  document.querySelectorAll('.sidebar-link, .sidebar-summary-link').forEach(a => a.classList.remove('active'));
  if (link) link.classList.add('active');
}
function showScenario(htmlFile, link) {
  document.getElementById('summary-page').style.display = 'none';
  var frame = document.getElementById('scenario-frame');
  frame.style.display = 'block';
  frame.src = htmlFile;
  document.querySelectorAll('.sidebar-link, .sidebar-summary-link').forEach(a => a.classList.remove('active'));
  if (link) link.classList.add('active');
}
</script>
</head>
<body>
<nav class="sidebar">
  <div class="sidebar-header">
    <h2>S3-A1</h2>
    <div class="sub">\u6b63\u5f0f\u30a8\u30d3\u30c7\u30f3\u30b9</div>
  </div>
  <div class="sidebar-nav">
    <div class="sidebar-section-label">\u6982\u8981</div>
    <a href="#" class="sidebar-summary-link active" onclick="showSummary(this); return false;">\u30b5\u30de\u30ea</a>
    ${commonClassDecisions ? '<div class="sidebar-section-label">\u54c1\u8cea</div><a href="#" class="sidebar-summary-link" onclick="showSummary(this); document.getElementById(\'common-class-section\').scrollIntoView({behavior:\'smooth\'}); return false;">\u5171\u901a\u30af\u30e9\u30b9\u5224\u65ad</a>' : ''}
    <div class="sidebar-section-label">\u30b7\u30ca\u30ea\u30aa</div>
    ${sidebarLinks}
  </div>
</nav>
<div class="main">
  <div id="summary-page">
    <h1>S3-A1: \u6b63\u5f0f\u30a8\u30d3\u30c7\u30f3\u30b9</h1>
    <div class="summary-cards">
      <div class="summary-card"><div class="label">\u53d6\u5f97\u65e5\u6642</div><div class="value">${now}</div></div>
      <div class="summary-card"><div class="label">\u30b7\u30ca\u30ea\u30aa</div><div class="value">${totalScenarios} \u4ef6</div></div>
      <div class="summary-card"><div class="label">\u691c\u8a3c\u7d50\u679c</div><div class="value">${passCount} PASS / ${failCount} FAIL${ntCount > 0 ? ` / ${ntCount} NOT_TESTABLE` : ''}</div></div>
    </div>
    <table class="result-table">
      <thead><tr><th>ID</th><th>\u30b7\u30ca\u30ea\u30aa\u540d</th><th>\u7a2e\u5225</th><th>\u7d50\u679c</th><th>\u8a73\u7d30</th></tr></thead>
      <tbody>${resultRows}</tbody>
    </table>
    ${renderCommonClassSection(commonClassDecisions)}
  </div>
  <iframe id="scenario-frame"></iframe>
  <div class="footer">\u751f\u6210: ${now}</div>
</div>
</body></html>`;
}

// ---------------------------------------------------------------------------
// メイン
// ---------------------------------------------------------------------------
function main() {
  const featureDir = process.argv[2];
  if (!featureDir) {
    console.error('Usage: node evidence_merge_report.js <feature_dir>');
    process.exit(1);
  }

  const resolvedDir = path.resolve(featureDir);
  const reportDir = path.join(resolvedDir, 'tests', 'reports');

  // 1. reports/ 配下の個別 HTML を走査
  const htmlFiles = discoverScenarioHTMLs(reportDir);
  if (htmlFiles.length === 0) {
    console.error(`Error: ${reportDir} に evidence_*.html が見つかりません`);
    process.exit(1);
  }
  console.log(`個別 HTML: ${htmlFiles.length} 件検出`);
  htmlFiles.forEach(f => console.log(`  - ${f.htmlFile}`));

  // 2. evidence_pack_sap.md からシナリオ結果を読み取り
  const sapResults = loadScenarioResults(resolvedDir);
  console.log(`evidence_pack_sap.md: ${sapResults.length} シナリオ`);

  // 3. HTML ファイルと結果をマージ（個別 HTML の情報を優先、evidence_pack_sap.md で補完）
  const mergedResults = htmlFiles.map(hf => {
    const sapMatch = sapResults.find(r => r.scenarioId === hf.scenarioId);
    return {
      scenarioId: hf.scenarioId,
      name: hf.name || (sapMatch && sapMatch.name) || '',
      type: (sapMatch && sapMatch.type) || '',
      status: hf.status || (sapMatch && sapMatch.status) || '',
      detail: (sapMatch && sapMatch.detail) || '',
    };
  });

  // 3b. common_class_decisions.yaml 読み取り
  const commonClassDecisions = loadCommonClassDecisions(resolvedDir);
  if (commonClassDecisions) {
    const usages = commonClassDecisions.usages || [];
    const exclusions = commonClassDecisions.exclusions || [];
    console.log(`共通クラス判断: ${usages.length} 使用 / ${exclusions.length} 不使用`);
  }

  // 4. 統合レポート HTML 生成
  const reportHtml = generateReportHTML(mergedResults, commonClassDecisions);
  const outputPath = path.join(reportDir, 'evidence_report.html');
  fs.writeFileSync(outputPath, reportHtml, 'utf-8');

  const passCount = mergedResults.filter(r => r.status === 'PASS').length;
  const failCount = mergedResults.filter(r => r.status === 'FAIL').length;
  const ntCount = mergedResults.filter(r => r.status === 'NOT_TESTABLE').length;
  console.log(`\n統合レポート生成完了: ${outputPath}`);
  console.log(`  ${mergedResults.length} シナリオ: ${passCount} PASS / ${failCount} FAIL${ntCount > 0 ? ` / ${ntCount} NOT_TESTABLE` : ''}`);
}

main();
