#!/usr/bin/env node
const path = require('path');
const fs = require('fs');
/**
 * data_preview.js — テーブル/CDSビューのデータプレビュー（SE16相当）
 *
 * テストデータの存在確認、選択条件に使うプラント値等の特定に使用する。
 * ADT REST API の /sap/bc/adt/datapreview/ddic エンドポイントを使用。
 *
 * Usage:
 *   node extensions/sap/tools/data_preview.js <table_name> [options]
 *
 * Options:
 *   --rows <n>       取得件数（デフォルト: 10、最大: 500）
 *   --where <cond>   WHERE条件（例: "WERKS = '1000'"）
 *   --columns <cols> 表示カラム（カンマ区切り、例: "MATNR,WERKS,CHARG"）
 *   --distinct <col> 指定カラムのユニーク値一覧を表示
 *   --format json    JSON形式で出力（エビデンス取得用）
 *   --output <file>  結果をファイルに保存（未指定時は標準出力）
 *
 * Examples:
 *   node extensions/sap/tools/data_preview.js MCHB
 *   node extensions/sap/tools/data_preview.js MCHB --rows 5 --where "WERKS = '1000'"
 *   node extensions/sap/tools/data_preview.js MCHB --distinct WERKS
 *   node extensions/sap/tools/data_preview.js MCHB --columns MATNR,WERKS,CHARG,CLABS
 *
 * Environment (.env):
 *   SAP_URL       — SAP system URL
 *   SAP_USERNAME  — SAP user
 *   SAP_PASSWORD  — SAP password
 *   SAP_CLIENT    — SAP client number
 */

'use strict';

const { ADTClient } = require('abap-adt-api');
const { writeEvidenceIfStepId, getStepIdFromArgs } = require('./lib/evidence_writer');
require('dotenv').config();
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

function createClient() {
  const { SAP_URL, SAP_USERNAME, SAP_PASSWORD, SAP_CLIENT } = process.env;
  if (!SAP_URL || !SAP_USERNAME || !SAP_PASSWORD) {
    console.error('Error: SAP_URL, SAP_USERNAME, SAP_PASSWORD must be set in .env');
    process.exit(1);
  }
  return new ADTClient(SAP_URL, SAP_USERNAME, SAP_PASSWORD, SAP_CLIENT, '');
}

function parseArgs(argv) {
  const args = argv.slice(2);
  if (args.length < 1 || args[0] === '--help' || args[0] === '-h') {
    console.log(`Usage: node data_preview.js <table_name> [options]

Options:
  --rows <n>       取得件数（デフォルト: 10、最大: 500）
  --where <cond>   WHERE条件（例: "WERKS = '1000'"）
  --columns <cols> 表示カラム（カンマ区切り）
  --distinct <col> 指定カラムのユニーク値一覧
  --format json    JSON形式で出力（エビデンス取得用）
  --output <file>  結果をファイルに保存

Examples:
  node data_preview.js MCHB
  node data_preview.js MCHB --rows 5 --where "WERKS = '1000'"
  node data_preview.js MCHB --distinct WERKS
  node data_preview.js MCHB --format json --output evidence_data/pre.json`);
    process.exit(args.length < 1 ? 1 : 0);
  }

  const tableName = args[0].toUpperCase();
  let rows = 10;
  let where = '';
  let columns = null;
  let distinct = null;
  let columnLabels = false;
  let format = 'table';  // table | json
  let output = null;     // output file path

  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--rows' && args[i + 1]) { rows = parseInt(args[++i], 10); }
    else if (args[i] === '--where' && args[i + 1]) { where = args[++i]; }
    else if (args[i] === '--columns' && args[i + 1]) { columns = args[++i].split(',').map(c => c.trim().toUpperCase()); }
    else if (args[i] === '--distinct' && args[i + 1]) { distinct = args[++i].toUpperCase(); }
    else if (args[i] === '--column-labels') { columnLabels = true; }
    else if (args[i] === '--format' && args[i + 1]) { format = args[++i].toLowerCase(); }
    else if (args[i] === '--output' && args[i + 1]) { output = args[++i]; }
    // --feature-dir and --step-id are handled by evidence_writer, skip them here
    else if (args[i] === '--feature-dir' && args[i + 1]) { ++i; }
    else if (args[i] === '--step-id' && args[i + 1]) { ++i; }
  }

  rows = Math.min(Math.max(rows, 1), 500);
  return { tableName, rows, where, columns, distinct, columnLabels, format, output };
}

/**
 * 結果を出力する（標準出力 or ファイル）
 */
function writeOutput(text, outputPath) {
  if (outputPath) {
    const fs = require('fs');
    const path = require('path');
    const dir = path.dirname(outputPath);
    if (dir && !fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(outputPath, text, 'utf-8');
    console.error(`Output saved to: ${outputPath}`);
  } else {
    console.log(text);
  }
}

/**
 * データを JSON 形式に変換する
 */
function formatJson(result, displayCols, colDefs) {
  const rows = [];
  for (const row of result.values) {
    const obj = {};
    for (const col of displayCols) {
      const val = Array.isArray(row) ? row[colDefs.indexOf(col)] : row[col.name];
      obj[col.name] = val !== undefined && val !== null ? val : null;
    }
    rows.push(obj);
  }
  return JSON.stringify(rows, null, 2);
}

function getFeatureDirFromArgs() {
  const idx = process.argv.indexOf('--feature-dir');
  if (idx !== -1 && idx + 1 < process.argv.length) {
    return process.argv[idx + 1];
  }
  return null;
}

function emitEvidence(tableName, resultSummary) {
  const stepId = getStepIdFromArgs();
  if (stepId) {
    const featureDir = getFeatureDirFromArgs();
    if (featureDir) {
      // 既存のエビデンスファイルから checked_tables を読み取り、マージする
      const { evidenceFilename, EVIDENCE_DIR_NAME } = require('./lib/evidence_writer');
      const evidenceDir = path.join(featureDir, EVIDENCE_DIR_NAME);
      const filename = evidenceFilename(stepId, 'data_preview.js');
      const filepath = path.join(evidenceDir, filename);
      let checkedTables = [tableName];
      if (fs.existsSync(filepath)) {
        const content = fs.readFileSync(filepath, 'utf8');
        const match = content.match(/checked_tables:\s*\[([^\]]*)\]/);
        if (match) {
          const existing = match[1].split(',').map(s => s.trim().replace(/"/g, '')).filter(s => s);
          if (!existing.includes(tableName)) {
            checkedTables = [...existing, tableName];
          } else {
            checkedTables = existing;
          }
        }
      }
      writeEvidenceIfStepId({
        featureDir,
        stepId,
        toolName: 'data_preview.js',
        command: process.argv.join(' '),
        options: [tableName],
        resultSummary,
        extraData: { checked_tables: checkedTables },
      });
    } else {
      console.error('Warning: --step-id specified but --feature-dir not provided. Skipping evidence output.');
    }
  }
}

async function main() {
  const { tableName, rows, where, columns, distinct, columnLabels, format, output } = parseArgs(process.argv);

  const client = createClient();

  // Build SQL query if WHERE specified
  let sqlQuery = '';
  if (where) {
    sqlQuery = `SELECT * FROM ${tableName} WHERE ${where}`;
  }

  // --column-labels: カラム名と日本語ラベルのみ出力（JSON形式）
  if (columnLabels) {
    try {
      const result = await client.tableContents(tableName, 1, true, '');
      const colDefs = result?.columns || [];
      const labels = {};
      for (const c of colDefs) {
        if (c.name && c.name.toUpperCase() !== 'MANDT') {
          labels[c.name.toUpperCase()] = c.description || c.name;
        }
      }
      console.log(JSON.stringify(labels));
    } catch (err) {
      console.error(`Error: ${err.message || err}`);
      process.exit(1);
    }
    return;
  }

  // JSON モードでは情報メッセージを stderr に出力（stdout を JSON パイプ用に保つ）
  const infoLog = format === 'json' ? console.error : console.log;
  infoLog(`Previewing ${tableName} (max ${rows} rows)${where ? ` WHERE ${where}` : ''}...\n`);

  try {
    const result = await client.tableContents(tableName, distinct ? 500 : rows, true, sqlQuery);

    if (!result || !result.values || result.values.length === 0) {
      console.log('(データなし)');
      console.log(`\n${tableName} にデータが存在しないか、条件に合致するレコードがありません。`);
      emitEvidence(tableName, '0 row(s)');
      process.exit(0);
    }

    const colDefs = result.columns || [];

    // --distinct mode
    if (distinct) {
      const colIdx = colDefs.findIndex(c => c.name.toUpperCase() === distinct);
      if (colIdx === -1) {
        console.error(`Error: カラム '${distinct}' が ${tableName} に見つかりません。`);
        console.error(`利用可能なカラム: ${colDefs.map(c => c.name).join(', ')}`);
        process.exit(1);
      }
      const values = new Set();
      for (const row of result.values) {
        const val = Array.isArray(row) ? row[colIdx] : row[colDefs[colIdx].name];
        if (val !== undefined && val !== null && val !== '') values.add(String(val));
      }
      const sorted = [...values].sort();
      console.log(`${distinct} のユニーク値 (${sorted.length} 件):`);
      for (const v of sorted) {
        console.log(`  ${v}`);
      }
      emitEvidence(tableName, `${sorted.length} distinct value(s) for ${distinct}`);
      process.exit(0);
    }

    // Filter columns if specified
    let displayCols = colDefs;
    if (columns) {
      displayCols = colDefs.filter(c => columns.includes(c.name.toUpperCase()));
      if (displayCols.length === 0) {
        console.error(`Error: 指定カラムが見つかりません: ${columns.join(', ')}`);
        console.error(`利用可能なカラム: ${colDefs.map(c => c.name).join(', ')}`);
        process.exit(1);
      }
    }

    // JSON format output
    if (format === 'json') {
      const jsonOutput = formatJson(result, displayCols, colDefs);
      writeOutput(jsonOutput, output);
      if (!output) {
        // ファイル出力でない場合は件数も stderr に出力
        console.error(`${result.values.length} row(s)`);
      }
      emitEvidence(tableName, `${result.values.length} row(s)`);
      process.exit(0);
    }

    // Print results as table
    const colNames = displayCols.map(c => c.name);
    const colWidths = colNames.map(n => Math.max(n.length, 8));

    // Calculate actual widths from data
    for (const row of result.values) {
      for (let i = 0; i < displayCols.length; i++) {
        const val = Array.isArray(row) ? row[colDefs.indexOf(displayCols[i])] : row[displayCols[i].name];
        const str = val !== undefined && val !== null ? String(val) : '';
        colWidths[i] = Math.max(colWidths[i], str.length);
      }
    }

    // Header
    const header = colNames.map((n, i) => n.padEnd(colWidths[i])).join('  ');
    const separator = colWidths.map(w => '-'.repeat(w)).join('--');
    console.log(header);
    console.log(separator);

    // Rows
    for (const row of result.values) {
      const cells = displayCols.map((col, i) => {
        const val = Array.isArray(row) ? row[colDefs.indexOf(col)] : row[col.name];
        const str = val !== undefined && val !== null ? String(val) : '';
        return str.padEnd(colWidths[i]);
      });
      console.log(cells.join('  '));
    }

    console.log(`\n${result.values.length} row(s)`);

    emitEvidence(tableName, `${result.values.length} row(s)`);

  } catch (err) {
    console.error(`Error: ${err.message || err}`);
    if (err.response) {
      console.error(`HTTP ${err.response.status}: ${err.response.statusText || ''}`);
    }
    process.exit(1);
  }
}

main();
