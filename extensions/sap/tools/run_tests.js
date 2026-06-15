#!/usr/bin/env node
/**
 * run_tests.js — "テストを実行する"
 *
 * SAPオブジェクトのABAP Unitテストを実行し、結果を表示するスクリプト。
 *
 * Usage:
 *   node scripts/run_tests.js <name> [--type class|program|function_group] [--output <report.md>]
 *
 * Default type: class
 *
 * Options:
 *   --type <type>    オブジェクト種別（class|program|function_group）。省略時は class
 *   --output <path>  テスト結果をMarkdownレポートとしてファイル出力する
 *
 * Examples:
 *   node scripts/run_tests.js ZCL_MY_CLASS
 *   node scripts/run_tests.js ZCL_MY_CLASS --type class
 *   node scripts/run_tests.js ZREPORT --type program
 *   node scripts/run_tests.js ZREPORT --type program --output tests/abap_unit_report.md
 *   node scripts/run_tests.js ZFUGR_EXAMPLE --type function_group
 *
 * Note:
 *   正式エビデンス（画面スクショ）は evidence_capture.js で取得する。
 *   本スクリプトはテスト GREEN の確認のみを目的とする。
 *
 * Exit codes:
 *   0 — all tests passed
 *   1 — one or more tests failed or error occurred
 *
 * Environment (.env):
 *   SAP_URL       — SAP system URL
 *   SAP_USERNAME  — SAP user
 *   SAP_PASSWORD  — SAP password
 *   SAP_CLIENT    — SAP client number
 */

'use strict';

const { ADTClient } = require('abap-adt-api');
const fs = require('fs');
const path = require('path');
const { writeEvidenceIfStepId, getStepIdFromArgs } = require('./lib/evidence_writer');
require('dotenv').config();
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'; // 自己署名証明書対応

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function createClient() {
  const { SAP_URL, SAP_USERNAME, SAP_PASSWORD, SAP_CLIENT } = process.env;
  if (!SAP_URL || !SAP_USERNAME || !SAP_PASSWORD) {
    console.error('Error: SAP_URL, SAP_USERNAME, SAP_PASSWORD must be set in .env');
    process.exit(1);
  }
  return new ADTClient(SAP_URL, SAP_USERNAME, SAP_PASSWORD, SAP_CLIENT, '');
}

const URI_MAP = {
  class:          (name) => `/sap/bc/adt/oo/classes/${name.toLowerCase()}`,
  program:        (name) => `/sap/bc/adt/programs/programs/${name.toLowerCase()}`,
  function_group: (name) => `/sap/bc/adt/functions/groups/${name.toLowerCase()}`,
};

function printUsage() {
  console.log(`Usage:
  node scripts/run_tests.js <name> [--type class|program|function_group]

Default type: class`);
}

function parseArgs(argv) {
  const args = argv.slice(2);
  if (args.length < 1) {
    printUsage();
    process.exit(1);
  }

  const name = args[0].toUpperCase();
  let type = 'class';
  let typeExplicit = false;

  const typeIdx = args.indexOf('--type');
  if (typeIdx !== -1 && args[typeIdx + 1]) {
    type = args[typeIdx + 1];
    typeExplicit = true;
  }

  if (!typeExplicit) {
    console.warn(`WARNING: --type not specified. Defaulting to "class".`);
    console.warn(`  For programs use: --type program`);
    console.warn(`  For function groups use: --type function_group`);
    console.warn('');
  }

  if (!URI_MAP[type]) {
    console.error(`Error: Unsupported type "${type}". Use class, program, or function_group.`);
    process.exit(1);
  }

  let output = null;
  const outIdx = args.indexOf('--output');
  if (outIdx !== -1 && args[outIdx + 1]) {
    output = args[outIdx + 1];
  }

  return { name, type, output };
}

// ---------------------------------------------------------------------------
// Result formatting
// ---------------------------------------------------------------------------

function formatResults(results) {
  let totalTests = 0;
  let totalPassed = 0;
  let totalFailed = 0;
  let totalSkipped = 0;
  const failures = [];

  const testClasses = extractTestClasses(results);

  for (const tc of testClasses) {
    const className = tc.name || tc['adtcore:name'] || tc['uriType'] || 'UnknownClass';
    const methods = tc.testMethods || tc.methods || [];

    console.log(`\n  Test Class: ${className}`);
    console.log('  ' + '-'.repeat(60));

    // Check class-level alerts (e.g., class_setup exceptions)
    const classAlerts = tc.alerts || [];
    const classHasCritical = classAlerts.some(a =>
      (a.severity || '').toLowerCase() === 'critical' ||
      (a.severity || '').toLowerCase() === 'fatal' ||
      (a.kind || '').toLowerCase() === 'exception'
    );
    if (classHasCritical && methods.length === 0) {
      totalTests++;
      totalFailed++;
      console.log(`    FAIL (class_setup exception)`);
      for (const alert of classAlerts) {
        const title = alert.title || alert.kind || '';
        const details = Array.isArray(alert.details) ? alert.details.join('; ') : (alert.details || alert.message || '');
        console.log(`         Alert: ${title}`);
        if (details) console.log(`         Details: ${details}`);
        failures.push({ className, methodName: 'class_setup', title, details });
      }
    }

    for (const m of methods) {
      totalTests++;
      const methodName = m.name || m['adtcore:name'] || 'unknown';

      // Check alerts for failures
      const alerts = m.alerts || [];
      const hasFail = alerts.some(a =>
        (a.severity || '').toLowerCase() === 'critical' ||
        (a.severity || '').toLowerCase() === 'fatal' ||
        (a.kind || '').toLowerCase() === 'failedassertion' ||
        (a.kind || '').toLowerCase() === 'failure'
      );

      if (hasFail) {
        totalFailed++;
        console.log(`    FAIL ${methodName}`);
        for (const alert of alerts) {
          const title = alert.title || alert.kind || '';
          const details = alert.details || alert.message || '';
          const stack = alert.stack || '';
          console.log(`         Alert: ${title}`);
          if (details) console.log(`         Details: ${details}`);
          if (stack) console.log(`         Stack: ${stack}`);
          failures.push({ className, methodName, title, details });
        }
      } else if (alerts.length > 0) {
        totalSkipped++;
        console.log(`    SKIP ${methodName}`);
        for (const alert of alerts) {
          console.log(`         ${alert.title || alert.kind || alert.message || ''}`);
        }
      } else {
        totalPassed++;
        const execTime = m.executionTime !== undefined ? ` (${m.executionTime}ms)` : '';
        console.log(`    PASS ${methodName}${execTime}`);
      }
    }
  }

  return { totalTests, totalPassed, totalFailed, totalSkipped, failures, testClasses };
}

// ---------------------------------------------------------------------------
// Markdown report generation
// ---------------------------------------------------------------------------

function generateMarkdownReport(name, type, testClasses, summary) {
  const now = new Date().toISOString().split('T')[0];
  const lines = [];

  lines.push('# ABAP Unit テスト結果レポート');
  lines.push('');
  lines.push('| 項目 | 値 |');
  lines.push('|------|-----|');
  lines.push(`| 対象オブジェクト | ${name} (${type}) |`);
  lines.push(`| テスト実行日時 | ${now} |`);
  lines.push(`| 実行方法 | run_tests.js --type ${type} |`);
  lines.push(`| 結果 | **全${summary.totalTests}件中 ${summary.totalPassed}件 PASS / ${summary.totalFailed}件 FAIL / ${summary.totalSkipped}件 SKIP** |`);
  lines.push('');
  lines.push('---');
  lines.push('');

  lines.push('## テストケース詳細');
  lines.push('');

  let seq = 0;
  for (const tc of testClasses) {
    const className = tc.name || 'UnknownClass';
    lines.push(`### テストクラス: ${className}`);
    lines.push('');
    lines.push('| # | メソッド | 結果 | 実行時間 | エラー詳細 |');
    lines.push('|---|---------|------|---------|-----------|');

    const methods = tc.testMethods || tc.methods || [];
    for (const m of methods) {
      seq++;
      const methodName = m.name || m['adtcore:name'] || 'unknown';
      const alerts = m.alerts || [];
      const hasFail = alerts.some(a =>
        (a.severity || '').toLowerCase() === 'critical' ||
        (a.severity || '').toLowerCase() === 'fatal' ||
        (a.kind || '').toLowerCase() === 'failedassertion' ||
        (a.kind || '').toLowerCase() === 'failure'
      );
      let status = 'PASS';
      let errorDetail = '';
      if (hasFail) {
        status = 'FAIL';
        errorDetail = alerts.map(a => `${a.title || a.kind || ''}: ${a.details || a.message || ''}`).join('; ');
      } else if (alerts.length > 0) {
        status = 'SKIP';
        errorDetail = alerts.map(a => a.title || a.kind || a.message || '').join('; ');
      }
      const execTime = m.executionTime !== undefined ? `${m.executionTime}ms` : '-';
      lines.push(`| ${seq} | ${methodName} | ${status} | ${execTime} | ${errorDetail} |`);
    }
    lines.push('');
  }

  lines.push('---');
  lines.push('');
  lines.push('> このレポートは `run_tests.js --output` により自動生成されました。');
  lines.push('');

  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// Extract test classes from various possible result structures
// ---------------------------------------------------------------------------

function extractTestClasses(results) {
  if (!results) return [];

  // Direct testClasses array
  if (Array.isArray(results.testClasses)) {
    return results.testClasses.map(tc => ({
      name: tc.name || tc['adtcore:name'] || tc.testClass?.name || tc.testClass?.['adtcore:name'] || '',
      testMethods: tc.testMethods || tc.testmethods || tc.methods || [],
    }));
  }

  // Nested under programs
  if (Array.isArray(results.programs)) {
    const classes = [];
    for (const prog of results.programs) {
      const tcs = prog.testClasses || [];
      for (const tc of tcs) {
        classes.push({
          name: tc.name || tc['adtcore:name'] || tc.testClass?.name || '',
          testMethods: tc.testMethods || tc.testmethods || tc.methods || [],
        });
      }
    }
    return classes;
  }

  // If it's an array itself
  if (Array.isArray(results)) {
    return results.map(tc => ({
      name: tc.name || tc['adtcore:name'] || '',
      testMethods: tc.testMethods || tc.testmethods || tc.methods || [],
    }));
  }

  // Fallback: dump what we have
  console.log('\n  (Unexpected result structure — raw output below)');
  console.log(JSON.stringify(results, null, 2));
  return [];
}

function formatCoverage(results) {
  const coverage = results.coverageInfo || results.coverage || null;
  if (!coverage) return;

  console.log('\n--- Coverage ---');

  if (Array.isArray(coverage)) {
    for (const c of coverage) {
      const name = c.name || c.objectName || '';
      const total = c.totalStatements || c.total || 0;
      const covered = c.coveredStatements || c.covered || 0;
      const pct = total > 0 ? ((covered / total) * 100).toFixed(1) : '0.0';
      console.log(`  ${name}: ${covered}/${total} (${pct}%)`);
    }
  } else if (typeof coverage === 'object') {
    const total = coverage.totalStatements || coverage.total || 0;
    const covered = coverage.coveredStatements || coverage.covered || 0;
    const pct = total > 0 ? ((covered / total) * 100).toFixed(1) : '0.0';
    console.log(`  Coverage: ${covered}/${total} (${pct}%)`);
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function emitRunTestsEvidence(resultSummary, outputPath) {
  const stepId = getStepIdFromArgs();
  if (!stepId) return;
  const fdIdx = process.argv.indexOf('--feature-dir');
  let featureDir = (fdIdx !== -1 && process.argv[fdIdx + 1]) ? process.argv[fdIdx + 1] : null;
  if (!featureDir && outputPath) {
    // Try to infer from --output path (e.g. specs/<feature>/tests/...)
    const absOutput = path.resolve(outputPath);
    const specsIdx = absOutput.indexOf(path.sep + 'specs' + path.sep);
    if (specsIdx !== -1) {
      const afterSpecs = absOutput.substring(specsIdx + 6);
      const featureName = afterSpecs.split(path.sep)[0];
      if (featureName) {
        featureDir = absOutput.substring(0, specsIdx) + path.sep + 'specs' + path.sep + featureName;
      }
    }
  }
  if (featureDir) {
    writeEvidenceIfStepId({
      featureDir,
      stepId,
      toolName: 'run_tests.js',
      command: process.argv.join(' '),
      options: process.argv.slice(2),
      resultSummary,
    });
  } else {
    console.error('Warning: --step-id specified but --feature-dir not provided and could not be inferred. Skipping evidence output.');
  }
}

async function main() {
  const { name, type, output } = parseArgs(process.argv);
  const client = createClient();
  const uri = URI_MAP[type](name);

  console.log(`Running ABAP Unit tests for ${type} ${name}...`);
  console.log(`URI: ${uri}`);

  try {
    let results;
    if (typeof client.runUnitTest === 'function') {
      results = await client.runUnitTest(uri);
    } else if (typeof client.unitTestRun === 'function') {
      results = await client.unitTestRun(uri);
    } else {
      console.error('Error: No unit test method found on ADTClient. Check abap-adt-api version.');
      process.exit(1);
    }

    console.log('\n=== Test Results ===');

    const { totalTests, totalPassed, totalFailed, totalSkipped, testClasses: parsedClasses } = formatResults(results);

    // Coverage
    formatCoverage(results);

    // Summary
    console.log('\n=== Summary ===');
    console.log(`  Total:   ${totalTests}`);
    console.log(`  Passed:  ${totalPassed}`);
    console.log(`  Failed:  ${totalFailed}`);
    console.log(`  Skipped: ${totalSkipped}`);

    if (totalFailed > 0) {
      console.log('\nResult: FAILED');
      emitRunTestsEvidence(`FAILED: ${totalPassed} passed, ${totalFailed} failed, ${totalSkipped} skipped (total: ${totalTests})`, output);
      process.exit(1);
    } else if (totalTests === 0) {
      console.log('\nResult: NO TESTS FOUND');
      emitRunTestsEvidence('NO TESTS FOUND', output);
      process.exit(0);
    } else {
      // 全テスト PASS 時のみレポートを出力する
      if (output) {
        const reportContent = generateMarkdownReport(name, type, parsedClasses, {
          totalTests, totalPassed, totalFailed, totalSkipped,
        });
        const outputDir = path.dirname(output);
        if (!fs.existsSync(outputDir)) {
          fs.mkdirSync(outputDir, { recursive: true });
        }
        fs.writeFileSync(output, reportContent, 'utf-8');
        console.log(`\nReport: ${output}`);
      }
      console.log('\nResult: ALL PASSED');
      emitRunTestsEvidence(`ALL PASSED: ${totalPassed} passed, ${totalFailed} failed, ${totalSkipped} skipped (total: ${totalTests})`, output);
      process.exit(0);
    }
  } catch (err) {
    console.error(`\nError: ${err.message || err}`);
    if (err.response) {
      console.error(`HTTP ${err.response.status}: ${err.response.statusText || ''}`);
    }
    process.exit(1);
  }
}

main();
