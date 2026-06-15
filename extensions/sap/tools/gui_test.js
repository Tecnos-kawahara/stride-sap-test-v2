#!/usr/bin/env node
/**
 * gui_test.js — SAP GUI Scripting Test Runner
 *
 * Runs GUI test WSF scripts to verify test GREEN status.
 * Evidence (screenshots, HTML) is NOT generated here — use evidence_capture.js.
 *
 * Usage:
 *   node extensions/sap/tools/gui_test.js <test.wsf> [--auto] [--output <report.md>]
 *
 * Options:
 *   --auto          SAP GUI の起動・ログインからテスト後のセッション終了まで自動実行
 *   --output <path> 全テスト PASS 時のみ Markdown レポートを出力する
 *
 * Exit codes:
 *   0 — all tests passed
 *   1 — one or more tests failed or error occurred
 */

'use strict';

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const { writeEvidenceIfStepId, getStepIdFromArgs } = require('./lib/evidence_writer');

function parseArgs() {
  const args = process.argv.slice(2);
  const result = { scriptPath: null, auto: false, output: null };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--auto') {
      result.auto = true;
    } else if (args[i] === '--output' && i + 1 < args.length) {
      result.output = args[++i];
    } else if (!result.scriptPath) {
      result.scriptPath = args[i];
    }
  }
  return result;
}

function runGuiLaunch(action) {
  const launchScript = path.join(__dirname, 'gui_launch.js');
  const args = action === 'close' ? ['--close'] : [];
  try {
    execSync(`node "${launchScript}" ${args.join(' ')}`, {
      stdio: 'inherit',
      timeout: 90000,
      shell: true,
      cwd: process.cwd(),
    });
    return true;
  } catch (e) {
    return false;
  }
}

function parseKV(output) {
  const kv = {};
  for (const line of output.split(/\r?\n/)) {
    const idx = line.indexOf('=');
    if (idx > 0) {
      kv[line.substring(0, idx).trim()] = line.substring(idx + 1).trim();
    }
  }
  return kv;
}

function runWSF(wsfPath) {
  const cmd = `cscript //NoLogo "${wsfPath}"`;
  let output;
  try {
    const buf = execSync(cmd, { timeout: 180000, shell: true });
    output = decodeShiftJIS(buf);
  } catch (err) {
    const stdoutBuf = err.stdout || Buffer.alloc(0);
    const stderrBuf = err.stderr || Buffer.alloc(0);
    output = decodeShiftJIS(Buffer.concat([stdoutBuf, stderrBuf]));
  }
  return output;
}

function decodeShiftJIS(buf) {
  try {
    return new TextDecoder('shift_jis').decode(buf);
  } catch (e) {
    return buf.toString('utf-8');
  }
}

function getTests(kv) {
  const count = parseInt(kv.TEST_COUNT) || 0;
  const tests = [];
  for (let i = 0; i < count; i++) {
    tests.push({
      id: kv[`TEST_${i}_ID`] || `T${i}`,
      desc: kv[`TEST_${i}_DESC`] || '',
      status: kv[`TEST_${i}_STATUS`] || 'UNKNOWN',
      detail: kv[`TEST_${i}_DETAIL`] || '',
    });
  }
  return tests;
}

function generateMarkdownReport(scriptName, tests, kv, passed, failed) {
  const now = new Date().toISOString().replace('T', ' ').substring(0, 19);
  const lines = [
    `# GUI Test Report: ${scriptName}`,
    '',
    `> このレポートは \`gui_test.js --output\` により自動生成されました。`,
    `> 生成日時: ${now}`,
    '',
    '## Environment',
    '',
    `| Item | Value |`,
    `|------|-------|`,
    `| System | ${kv.SYSTEM || '?'} |`,
    `| Client | ${kv.CLIENT || '?'} |`,
    `| User | ${kv.USER || '?'} |`,
    '',
    '## Test Results',
    '',
    `| # | ID | Description | Status |`,
    `|---|-----|-------------|--------|`,
  ];

  for (let i = 0; i < tests.length; i++) {
    const t = tests[i];
    const status = t.status === 'PASS' ? 'PASS' : `FAIL: ${t.detail}`;
    lines.push(`| ${i + 1} | ${t.id} | ${t.desc} | ${status} |`);
  }

  lines.push('');
  lines.push('## Summary');
  lines.push('');
  lines.push(`- Total: ${tests.length}`);
  lines.push(`- Passed: ${passed}`);
  lines.push(`- Failed: ${failed}`);
  lines.push(`- Result: **${failed > 0 ? 'FAILED' : 'ALL PASSED'}**`);
  lines.push('');

  return lines.join('\n');
}

function main() {
  const { scriptPath, auto, output } = parseArgs();

  if (!scriptPath) {
    console.error('Usage: node gui_test.js <test.wsf> [--auto] [--output <report.md>]');
    process.exit(1);
  }

  const fullPath = path.resolve(scriptPath);
  if (!fs.existsSync(fullPath)) {
    console.error(`テストスクリプトが見つかりません: ${fullPath}`);
    process.exit(1);
  }

  const testName = path.basename(scriptPath, '.wsf');
  console.log(`=== SAP GUI テストランナー ===`);
  console.log(`スクリプト: ${fullPath}`);
  if (auto) console.log(`モード: 自動（起動→テスト→終了）`);
  console.log('');

  // --- SAP GUI 起動（常に実行 — 既存セッションがあればそのまま使用、なければ新規起動） ---
  console.log('[自動起動] SAP GUI セッションを準備...\n');
  if (!runGuiLaunch('start')) {
    console.error('[失敗] SAP GUI の起動に失敗しました。');
    process.exit(1);
  }
  console.log('');

  // --- テスト実行（GREEN 確認のみ） ---
  console.log('[実行] テスト実行中...');
  const raw = runWSF(fullPath);
  const kv = parseKV(raw);

  if (kv.CONNECT === 'FAIL') {
    console.error('[失敗] SAP GUI に接続できません:', kv.ERROR || '不明');
    process.exit(1);
  }

  const tests = getTests(kv);
  let passed = 0, failed = 0;

  console.log(`システム: ${kv.SYSTEM || '?'} | クライアント: ${kv.CLIENT || '?'} | ユーザー: ${kv.USER || '?'}\n`);

  for (const t of tests) {
    if (t.status === 'PASS') {
      passed++;
      console.log(`  [合格] ${t.id}: ${t.desc}`);
    } else {
      failed++;
      console.log(`  [不合格] ${t.id}: ${t.desc} -- ${t.detail}`);
    }
  }

  console.log(`\n結果: ${passed}/${tests.length} 合格`);

  // --- 全テスト PASS 時のみレポートを出力する ---
  if (failed === 0 && tests.length > 0 && output) {
    const reportContent = generateMarkdownReport(testName, tests, kv, passed, failed);
    const outputDir = path.dirname(output);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    fs.writeFileSync(output, reportContent, 'utf-8');
    console.log(`\nReport: ${output}`);
  }

  // --- SAP GUI 終了（常に実行） ---
  console.log('\n[自動終了] SAP GUI セッションを終了...');
  runGuiLaunch('close');

  // Evidence output
  const stepId = getStepIdFromArgs();
  if (stepId) {
    // Derive feature-dir from WSF file path (specs/<feature>/tests/e2e/...)
    const fdIdx = process.argv.indexOf('--feature-dir');
    let featureDir = (fdIdx !== -1 && process.argv[fdIdx + 1]) ? process.argv[fdIdx + 1] : null;
    if (!featureDir) {
      const absScript = path.resolve(scriptPath);
      const specsIdx = absScript.indexOf(path.sep + 'specs' + path.sep);
      if (specsIdx !== -1) {
        const afterSpecs = absScript.substring(specsIdx + 6);
        const featureName = afterSpecs.split(path.sep)[0];
        if (featureName) {
          featureDir = absScript.substring(0, specsIdx) + path.sep + 'specs' + path.sep + featureName;
        }
      }
    }
    if (featureDir) {
      writeEvidenceIfStepId({
        featureDir,
        stepId,
        toolName: 'gui_test.js',
        command: process.argv.join(' '),
        options: [scriptPath, auto ? '--auto' : '', output ? `--output ${output}` : ''].filter(Boolean),
        resultSummary: `${passed}/${tests.length} passed, ${failed} failed`,
      });
    } else {
      console.error('Warning: --step-id specified but --feature-dir not provided and could not be inferred. Skipping evidence output.');
    }
  }

  process.exit(failed > 0 ? 1 : 0);
}

main();
