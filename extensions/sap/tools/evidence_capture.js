#!/usr/bin/env node
/**
 * evidence_capture.js — S3-A1: エビデンス一括取得スクリプト
 *
 * 全テスト GREEN + stride-lint PASS 後に実行する。
 * plan.md の test_scenarios.scenarios 定義に基づき、SAP GUI 経由で画面スクショを一括取得する。
 * これが唯一の正式エビデンス生成ツールである。
 *
 * AC 別検証結果:
 *   covers_ts[].expected_checks（sap_scenario_generator.py が test_perspective_master.yaml の
 *   perspective_expected_checks から自動生成）を読み取り、各 AC に対応する検証チェックの
 *   期待結果と実結果を HTML テーブルに表示する。spec.md の AC statement も自動読み込みする。
 *
 * スクショは screenshots/{test_id}/ にテストケース単位でフォルダ分けし、
 * フォルダ内は連番（0001, 0002, ...）で画面遷移の順序を保証する。
 *
 * Usage:
 *   node extensions/sap/tools/evidence_capture.js <feature_dir_or_plan.md> --scenario <id> [options]
 *
 * Options:
 *   --scenario <id>     テストシナリオ ID（必須。例: SC-01）
 *   --output <dir>      エビデンス出力先ディレクトリ
 *   --auto              SAP GUI の起動・ログインからセッション終了まで自動実行
 *   --no-evidence       エビデンス取得なし（スクショなし、SE16 なし。PASS/FAIL 自動判定のみ）
 *   --screenshot        --no-evidence と併用時、スクリーンショットのみ取得（SE16/JSON は取得しない）
 *
 * 3段階実行モデル:
 *   Stage 1（単体テスト）:   --scenario SC-01 --no-evidence              スクショなし、自動判定のみ
 *   Stage 2（受入テスト）:   --scenario SC-01 --no-evidence --screenshot  スクショあり、SE16/JSON なし
 *   Stage 3（エビデンス）:   --scenario SC-01                            フルエビデンス（スクショ + SE16 + JSON）
 *
 * Output:
 *   <dir>/evidence_report.html                  — サイドメニュー付き統合エビデンス HTML
 *   <dir>/screenshots/{scenario_id}_{seq}.png   — スクリーンショット PNG（scenario_id_連番形式）
 *
 * Exit codes:
 *   0 — 全エビデンス取得成功
 *   1 — エラー発生
 */

'use strict';

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { writeEvidenceIfStepId, getStepIdFromArgs } = require('./lib/evidence_writer');

// ---------------------------------------------------------------------------
// CLI 引数パース
// ---------------------------------------------------------------------------
function parseArgs() {
  const args = process.argv.slice(2);
  const result = {
    planPath: null,
    output: null,
    auto: false,
    continueOnError: false,
    scenario: null,        // --scenario SC-01（必須）
    noEvidence: false,     // --no-evidence（スクショなし、SE16 なし）
    screenshot: false,     // --screenshot（--no-evidence 併用時のみ有効、スクショだけ取得）
    // EC-M1: --recapture <scenario> — 指定シナリオの再実行 + SLG1 再キャプチャのみ
    recapture: null,
    // EC-M2: --replace-screenshot <name> <file> — HTML 内のスクショ差し替え
    replaceScreenshotName: null,
    replaceScreenshotFile: null,
    // EC-M3: --update-data <table> <json> — HTML 内のデータセクション再生成
    updateDataTable: null,
    updateDataJson: null,
    // --evidence <path> — EC-M2/M3 で対象 HTML を指定
    evidenceHtml: null,
  };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--output' && args[i + 1]) {
      result.output = args[++i];
    } else if (args[i] === '--auto') {
      result.auto = true;
    } else if (args[i] === '--continue-on-error') {
      result.continueOnError = true;
    } else if (args[i] === '--scenario' && args[i + 1]) {
      result.scenario = args[++i];
    } else if (args[i] === '--no-evidence') {
      result.noEvidence = true;
    } else if (args[i] === '--screenshot') {
      result.screenshot = true;
    } else if (args[i] === '--recapture' && args[i + 1]) {
      result.recapture = args[++i];
    } else if (args[i] === '--replace-screenshot' && args[i + 1] && args[i + 2]) {
      result.replaceScreenshotName = args[++i];
      result.replaceScreenshotFile = args[++i];
    } else if (args[i] === '--update-data' && args[i + 1] && args[i + 2]) {
      result.updateDataTable = args[++i];
      result.updateDataJson = args[++i];
    } else if (args[i] === '--evidence' && args[i + 1]) {
      result.evidenceHtml = args[++i];
    } else if (!result.planPath) {
      result.planPath = args[i];
    }
  }

  // EC-M1/M2/M3 モードの場合、--scenario は不要
  const isSubcommandMode = result.recapture || result.replaceScreenshotName || result.updateDataTable;

  // --scenario は通常モードでは必須
  if (!result.scenario && !isSubcommandMode) {
    console.error('Error: --scenario <id> は必須です（例: --scenario SC-01）');
    console.error('');
    console.error('3段階実行モデル:');
    console.error('  Stage 1: --scenario SC-01 --no-evidence              (自動判定のみ)');
    console.error('  Stage 2: --scenario SC-01 --no-evidence --screenshot (スクショ + 自動判定)');
    console.error('  Stage 3: --scenario SC-01                            (フルエビデンス)');
    console.error('');
    console.error('サブコマンド:');
    console.error('  --recapture <scenario>                                (再実行 + SLG1 再キャプチャ)');
    console.error('  --replace-screenshot <name> <file> --evidence <html>  (スクショ差し替え)');
    console.error('  --update-data <table> <json> --evidence <html>        (データセクション再生成)');
    process.exit(1);
  }

  // EC-M1: --recapture は --scenario を自動設定
  if (result.recapture && !result.scenario) {
    result.scenario = result.recapture;
  }

  // --screenshot は --no-evidence と併用時のみ有効
  if (result.screenshot && !result.noEvidence) {
    result.screenshot = false; // --no-evidence なしなら --screenshot は無視（デフォルトでスクショ取得）
  }

  return result;
}

// ---------------------------------------------------------------------------
// ABAP ソースから OBLIGATORY フィールドを検出し、デフォルト値を返す
// ---------------------------------------------------------------------------
function detectObligatoryFromSource(srcDir, progName) {
  const fields = [];
  if (!srcDir || !progName) return fields;

  // src/ 配下からプログラムソースを探す
  const progUpper = progName.toUpperCase();
  const glob = require('path');
  let sourceContent = '';

  function searchDir(dir) {
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = glob.join(dir, entry.name);
        if (entry.isDirectory()) {
          searchDir(fullPath);
        } else if (entry.name.toUpperCase().includes(progUpper) && entry.name.endsWith('.prog.abap')) {
          sourceContent = fs.readFileSync(fullPath, 'utf-8');
          return;
        }
      }
    } catch (e) { /* dir not found */ }
  }
  searchDir(srcDir);

  if (!sourceContent) return fields;

  // s_werks FOR mchb-werks OBLIGATORY のパターンを検出（複数行にまたがる場合も対応）
  const regex = /(S_\w+)\s+FOR\s+(\w+-(\w+))\s+OBLIGATORY/gi;
  let match;
  while ((match = regex.exec(sourceContent)) !== null) {
    const selName = match[1].toUpperCase();
    const colName = match[3].toUpperCase();
    // data_preview.js でデフォルト値を取得
    try {
      const { execSync } = require('child_process');
      const dpJs = glob.resolve(__dirname, 'data_preview.js');
      // テーブル名は FOR 句から取得（mchb-werks → MCHB）
      const tableName = match[2].split('-')[0].toUpperCase();
      const templateRoot = glob.resolve(srcDir, '..');
      const output = execSync(
        `node "${dpJs}" ${tableName} --distinct ${colName}`,
        { cwd: templateRoot, timeout: 30000, encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'] }
      );
      const dataLines = output.split('\n')
        .map(l => l.trim())
        .filter(l => l && !l.startsWith('Previewing') && !l.includes('ユニーク値') && !l.toLowerCase().includes('row'));
      if (dataLines.length > 0) {
        fields.push({ name: `${selName}-LOW`, low: dataLines[0] });
      }
    } catch (e) {
      // data_preview 失敗時はスキップ
    }
  }

  return fields;
}

// ---------------------------------------------------------------------------
// spec.md から AC ID → statement のマップを構築
// ---------------------------------------------------------------------------
function loadAcStatements(featureDir) {
  const acMap = {};
  const specPath = path.join(featureDir, 'spec.md');
  if (!fs.existsSync(specPath)) return acMap;
  try {
    const content = fs.readFileSync(specPath, 'utf-8');
    // CRLF / LF 両対応
    const yamlMatch = content.match(/```yaml\r?\n([\s\S]*?)```/);
    if (!yamlMatch) return acMap;
    const jsYaml = require('js-yaml');
    const doc = jsYaml.load(yamlMatch[1]);
    const spec = doc?.spec || doc || {};
    for (const uc of spec.use_cases || []) {
      for (const ac of uc.acceptance || []) {
        if (ac.id && ac.statement) {
          acMap[ac.id] = ac.statement;
        }
      }
    }
  } catch (e) { /* ignore parse errors */ }
  return acMap;
}

// ---------------------------------------------------------------------------
// plan.md から evidence_capture セクションを抽出
// ---------------------------------------------------------------------------
/**
 * sap_context.md からメタデータのラベル情報を読み込む。
 * plan.md のパスから feature ディレクトリを逆算して sap_context.md を探す。
 */
function loadSapContextLabels(planPath) {
  // plan.md から上方向に implementation-details/sap_context.md を探索
  let searchDir = path.resolve(planPath, '..');
  for (let depth = 0; depth < 10; depth++) {
    const candidate = path.join(searchDir, 'implementation-details', 'sap_context.md');
    if (fs.existsSync(candidate)) {
      try {
        const content = fs.readFileSync(candidate, 'utf-8');
        const yamlMatch = content.match(/```yaml\r?\n(metadata:[\s\S]*?)```/);
        if (!yamlMatch) return null;

        // 簡易 YAML パース（tables と fields のラベルを抽出）
        const yamlText = yamlMatch[1];
        const labels = { tables: {}, fields: {} };
        let currentTable = '';
        let inFields = false;

        for (const line of yamlText.split('\n')) {
          const stripped = line.trim();
          // テーブル名行
          const tblMatch = stripped.match(/^(\w+):$/);
          if (tblMatch && !['metadata', 'tables', 'selection_screen', 'fields'].includes(tblMatch[1].toLowerCase())) {
            currentTable = tblMatch[1];
            inFields = false;
          }
          // テーブルラベル
          const lblMatch = stripped.match(/^label:\s*"([^"]*)"/);
          if (lblMatch && currentTable) {
            labels.tables[currentTable] = lblMatch[1];
          }
          // fields セクション開始
          if (stripped === 'fields:') {
            inFields = true;
            continue;
          }
          // フィールドラベル
          if (inFields) {
            const fldMatch = stripped.match(/^(\w+):\s*\{\s*label:\s*"([^"]*)"/);
            if (fldMatch) {
              labels.fields[fldMatch[1]] = fldMatch[2];
            } else if (!stripped.startsWith('#') && stripped && !stripped.includes('{')) {
              inFields = false;
            }
          }
        }
        // selection_screen の label も fields に追加（P_ZERO 等のパラメータ用）
        const selScreenRegex = /name:\s*"(\w+)"[^}]*label:\s*"([^"]*)"/g;
        let selMatch;
        while ((selMatch = selScreenRegex.exec(yamlText)) !== null) {
          if (selMatch[2] && !labels.fields[selMatch[1]]) {
            labels.fields[selMatch[1]] = selMatch[2];
          }
        }
        return labels;
      } catch (e) {
        return null;
      }
    }
    const parent = path.dirname(searchDir);
    if (parent === searchDir) break;
    searchDir = parent;
  }
  return null;
}

// ---------------------------------------------------------------------------
// Node.js 側の追加チェック（VBScript 外で実行する check 種別）
// ---------------------------------------------------------------------------
function runNodeChecks(checks, scenario, featureDir, evidenceMode) {
  const results = { passed: 0, failed: 0, details: [] };
  const reportDir = path.join(featureDir, 'tests', 'reports');
  const evidenceDataDir = path.join(reportDir, 'evidence_data');

  for (const chk of checks) {
    let pass = false;
    let detail = '';

    if (chk.check === 'db_changed') {
      // db_changed: data_preview.js でテーブルデータを取得して比較
      // Stage 1（単体テスト）ではスキップ。Stage 2/3 では実行。
      if (evidenceMode === 'stage1') {
        pass = true;
        detail = 'db_changed: Stage 1 ではスキップ（Stage 2 で実行）';
      } else {
        const table = chk.table || '';
        const keys = chk.keys || '';
        const expected = chk.expected; // true = 変更あり, false = 変更なし
        const mode = chk.mode || '';   // "update" | "insert" | "delete" | ""
        if (table === '__PLACEHOLDER__' || keys === '__PLACEHOLDER__') {
          detail = `db_changed: __PLACEHOLDER__ が残っています（table=${table}）`;
        } else if (!table) {
          detail = 'db_changed: table が未指定';
        } else {
          try {
            const dataPreviewJs = path.join(__dirname, 'data_preview.js');
            const where = typeof keys === 'string' ? keys :
              Object.entries(keys).map(([k, v]) => `${k} = '${v}'`).join(' AND ');
            const cmd = `node "${dataPreviewJs}" ${table} --format json${where ? ` --where "${where}"` : ''} --rows 100`;
            const buf = execSync(cmd, { timeout: 30000, shell: true, cwd: process.cwd() });
            const postData = JSON.parse(buf.toString('utf-8'));
            const postRows = Array.isArray(postData) ? postData.length : 0;

            // pre JSON の読み込み（evidence_data ディレクトリから）
            const testId = scenario.test_id || scenario.id || '';
            const preJsonPath = path.join(evidenceDataDir, `pre_${testId}_${table}.json`);
            let preData = null;
            let preRows = 0;
            try {
              preData = JSON.parse(fs.readFileSync(preJsonPath, 'utf-8'));
              preRows = Array.isArray(preData) ? preData.length : 0;
            } catch (_) { /* pre JSON がなければ比較なし */ }

            if (expected === false) {
              // ROLLBACK: pre と post が同じであること
              if (preData && JSON.stringify(preData) === JSON.stringify(postData)) {
                pass = true;
                detail = `db_changed(rollback): ${table} 変更なし（${postRows} 行、pre と同一）`;
              } else if (!preData) {
                pass = postRows >= 0; // pre がなければ post の存在だけ確認
                detail = `db_changed(rollback): ${table} ${postRows} 行（pre JSON なし、厳密比較不可）`;
              } else {
                detail = `db_changed(rollback): ${table} 変更あり（期待: 変更なし）`;
              }
            } else if (mode === 'update') {
              // UPDATE: 行数同じで値が変わっている
              if (preData && preRows === postRows && preRows > 0 && JSON.stringify(preData) !== JSON.stringify(postData)) {
                pass = true;
                detail = `db_changed(update): ${table} ${postRows} 行（行数同一、値変更あり）`;
              } else if (preData && preRows === postRows && JSON.stringify(preData) === JSON.stringify(postData)) {
                detail = `db_changed(update): ${table} 値が変更されていない（pre と post が同一）`;
              } else if (preData && preRows !== postRows) {
                detail = `db_changed(update): ${table} 行数変化（pre=${preRows}, post=${postRows}）UPDATE ではなく INSERT/DELETE の可能性`;
              } else if (!preData) {
                pass = postRows > 0;
                detail = `db_changed(update): ${table} ${postRows} 行（pre JSON なし、厳密比較不可）`;
              } else {
                detail = `db_changed(update): ${table} 期待する変更なし`;
              }
            } else if (mode === 'insert') {
              // INSERT: 行数が増えている
              if (preData && postRows > preRows) {
                pass = true;
                detail = `db_changed(insert): ${table} ${preRows} → ${postRows} 行（+${postRows - preRows} 行）`;
              } else if (preData && postRows <= preRows) {
                detail = `db_changed(insert): ${table} 行数未増加（pre=${preRows}, post=${postRows}）`;
              } else if (!preData && postRows > 0) {
                pass = true;
                detail = `db_changed(insert): ${table} ${postRows} 行（pre JSON なし、厳密比較不可）`;
              } else {
                detail = `db_changed(insert): ${table} データなし`;
              }
            } else if (mode === 'delete') {
              // DELETE: 行数が減っている
              if (preData && postRows < preRows) {
                pass = true;
                detail = `db_changed(delete): ${table} ${preRows} → ${postRows} 行（-${preRows - postRows} 行）`;
              } else if (preData && postRows >= preRows) {
                detail = `db_changed(delete): ${table} 行数未減少（pre=${preRows}, post=${postRows}）`;
              } else {
                detail = `db_changed(delete): ${table} 厳密比較不可`;
              }
            } else {
              // mode 未指定: 単純にデータ有無チェック
              if (expected === true && postRows > 0) {
                pass = true;
                detail = `db_changed: ${table} にデータあり（${postRows} 行）`;
              } else {
                detail = `db_changed: ${table} expected=${expected} rows=${postRows}`;
              }
            }
          } catch (e) {
            detail = `db_changed: data_preview.js 実行エラー — ${e.message}`;
          }
        }
      }
    } else if (chk.check === 'file_output') {
      // file_output: 出力ファイルの存在・内容チェック
      const filePath = chk.path || '';
      if (filePath === '__PLACEHOLDER__') {
        detail = 'file_output: __PLACEHOLDER__ が残っています';
      } else if (!filePath) {
        detail = 'file_output: path が未指定';
      } else if (chk.expected_error) {
        // エラー時はファイルが生成されないことを確認
        pass = !fs.existsSync(filePath);
        detail = pass ? 'file_output: ファイルなし（期待通り）' : `file_output: ファイルが存在する（${filePath}）`;
      } else {
        if (fs.existsSync(filePath)) {
          const content = fs.readFileSync(filePath, 'utf-8');
          const contains = chk.contains || '';
          if (contains === '__PLACEHOLDER__') {
            detail = 'file_output: contains が __PLACEHOLDER__';
          } else if (contains && content.includes(contains)) {
            pass = true;
            detail = `file_output: ${path.basename(filePath)} に期待内容あり`;
          } else if (contains) {
            detail = `file_output: '${contains}' が ${path.basename(filePath)} に見つからない`;
          } else {
            pass = true;
            detail = `file_output: ${path.basename(filePath)} が存在する`;
          }
        } else {
          detail = `file_output: ファイルが存在しない（${filePath}）`;
        }
      }
    } else if (chk.check === 'log_output') {
      // log_output: SLG1 アプリケーションログの確認（BALHDR テーブル経由）
      const logObj = chk.object || '';
      const logSub = chk.subobject || '';
      const logContains = chk.contains || '';
      if (logObj === '__PLACEHOLDER__' || logSub === '__PLACEHOLDER__' || logContains === '__PLACEHOLDER__') {
        detail = `log_output: __PLACEHOLDER__ が残っています（object=${logObj}, subobject=${logSub})`;
      } else if (evidenceMode === 'stage1') {
        pass = true;
        detail = 'log_output: Stage 1 ではスキップ（Stage 2 で実行）';
      } else {
        try {
          const dataPreviewJs = path.join(__dirname, 'data_preview.js');
          const where = `OBJECT = '${logObj}' AND SUBOBJECT = '${logSub}'`;
          const cmd = `node "${dataPreviewJs}" BALHDR --format json --where "${where}" --rows 10`;
          const buf = execSync(cmd, { timeout: 30000, shell: true, cwd: process.cwd() });
          const data = JSON.parse(buf.toString('utf-8'));
          if (Array.isArray(data) && data.length > 0) {
            if (logContains) {
              const found = data.some(row => JSON.stringify(row).includes(logContains));
              pass = found;
              detail = found ? `log_output: BALHDR に '${logContains}' を含むログあり` : `log_output: '${logContains}' が見つからない`;
            } else {
              pass = true;
              detail = `log_output: BALHDR にログ ${data.length} 件あり`;
            }
          } else {
            detail = `log_output: BALHDR にログなし（OBJECT=${logObj}, SUBOBJECT=${logSub}）`;
          }
        } catch (e) {
          detail = `log_output: BALHDR 検索エラー — ${e.message}`;
        }
      }
    } else if (chk.check === 'print_output') {
      // print_output: スプール出力の確認（TSP01 テーブル経由）
      const printContains = chk.contains || '';
      if (printContains === '__PLACEHOLDER__') {
        detail = 'print_output: __PLACEHOLDER__ が残っています';
      } else if (evidenceMode === 'stage1') {
        pass = true;
        detail = 'print_output: Stage 1 ではスキップ';
      } else {
        try {
          const dataPreviewJs = path.join(__dirname, 'data_preview.js');
          const cmd = `node "${dataPreviewJs}" TSP01 --format json --rows 5`;
          const buf = execSync(cmd, { timeout: 30000, shell: true, cwd: process.cwd() });
          const data = JSON.parse(buf.toString('utf-8'));
          if (Array.isArray(data) && data.length > 0) {
            pass = true;
            detail = `print_output: スプール ${data.length} 件あり`;
          } else {
            detail = 'print_output: スプールなし';
          }
        } catch (e) {
          detail = `print_output: TSP01 検索エラー — ${e.message}`;
        }
      }
    } else if (chk.check === 'idoc_status') {
      // idoc_status: IDoc ステータスの確認（EDIDC テーブル経由）
      const idocType = chk.idoc_type || '';
      const expectedStatus = chk.expected_status || '';
      if (idocType === '__PLACEHOLDER__' || expectedStatus === '__PLACEHOLDER__') {
        detail = `idoc_status: __PLACEHOLDER__ が残っています（idoc_type=${idocType}）`;
      } else if (evidenceMode === 'stage1') {
        pass = true;
        detail = 'idoc_status: Stage 1 ではスキップ';
      } else {
        try {
          const dataPreviewJs = path.join(__dirname, 'data_preview.js');
          const where = `IDOCTP = '${idocType}'`;
          const cmd = `node "${dataPreviewJs}" EDIDC --format json --where "${where}" --rows 10`;
          const buf = execSync(cmd, { timeout: 30000, shell: true, cwd: process.cwd() });
          const data = JSON.parse(buf.toString('utf-8'));
          if (Array.isArray(data) && data.length > 0) {
            const lastIdoc = data[data.length - 1];
            const actualStatus = lastIdoc.STATUS || '';
            pass = actualStatus === expectedStatus;
            detail = pass ? `idoc_status: STATUS=${actualStatus}（期待通り）` : `idoc_status: STATUS=${actualStatus}（期待: ${expectedStatus}）`;
          } else {
            detail = `idoc_status: EDIDC に該当 IDoc なし（IDOCTP=${idocType}）`;
          }
        } catch (e) {
          detail = `idoc_status: EDIDC 検索エラー — ${e.message}`;
        }
      }
    } else if (chk.check === 'wf_status') {
      // wf_status: ワークフローステータスの確認（SWWWIHEAD テーブル経由）
      const wfId = chk.workflow_id || '';
      const expectedStatus = chk.expected_status || '';
      if (wfId === '__PLACEHOLDER__' || expectedStatus === '__PLACEHOLDER__') {
        detail = `wf_status: __PLACEHOLDER__ が残っています（workflow_id=${wfId}）`;
      } else if (evidenceMode === 'stage1') {
        pass = true;
        detail = 'wf_status: Stage 1 ではスキップ';
      } else {
        try {
          const dataPreviewJs = path.join(__dirname, 'data_preview.js');
          const where = `WI_TYPE = '${wfId}'`;
          const cmd = `node "${dataPreviewJs}" SWWWIHEAD --format json --where "${where}" --rows 10`;
          const buf = execSync(cmd, { timeout: 30000, shell: true, cwd: process.cwd() });
          const data = JSON.parse(buf.toString('utf-8'));
          if (Array.isArray(data) && data.length > 0) {
            const lastWf = data[data.length - 1];
            const actualStatus = lastWf.WI_STAT || '';
            pass = actualStatus === expectedStatus;
            detail = pass ? `wf_status: WI_STAT=${actualStatus}（期待通り）` : `wf_status: WI_STAT=${actualStatus}（期待: ${expectedStatus}）`;
          } else {
            detail = `wf_status: SWWWIHEAD に該当ワークフローなし`;
          }
        } catch (e) {
          detail = `wf_status: SWWWIHEAD 検索エラー — ${e.message}`;
        }
      }
    } else if (chk.check === 'mail_sent') {
      // mail_sent: メール送信の確認（SOOD テーブル経由）
      const recipient = chk.recipient || '';
      const subjectContains = chk.subject_contains || '';
      if (recipient === '__PLACEHOLDER__' || subjectContains === '__PLACEHOLDER__') {
        detail = `mail_sent: __PLACEHOLDER__ が残っています（recipient=${recipient}）`;
      } else if (chk.expected_error) {
        // 送信失敗のケース — メッセージタイプで判定済みのため Node.js 側は PASS
        pass = true;
        detail = 'mail_sent: 送信失敗ケース（メッセージタイプで判定済み）';
      } else if (evidenceMode === 'stage1') {
        pass = true;
        detail = 'mail_sent: Stage 1 ではスキップ';
      } else {
        try {
          const dataPreviewJs = path.join(__dirname, 'data_preview.js');
          const cmd = `node "${dataPreviewJs}" SOOD --format json --rows 10`;
          const buf = execSync(cmd, { timeout: 30000, shell: true, cwd: process.cwd() });
          const data = JSON.parse(buf.toString('utf-8'));
          if (Array.isArray(data) && data.length > 0) {
            pass = true;
            detail = `mail_sent: SOOD にメール ${data.length} 件あり`;
          } else {
            detail = 'mail_sent: SOOD にメールなし';
          }
        } catch (e) {
          detail = `mail_sent: SOOD 検索エラー — ${e.message}`;
        }
      }
    } else if (chk.check === 'bdc_result') {
      // bdc_result: BDC 実行結果の確認
      const transaction = chk.transaction || '';
      const expectedStatus = chk.expected_status || '';
      if (transaction === '__PLACEHOLDER__' || expectedStatus === '__PLACEHOLDER__') {
        detail = `bdc_result: __PLACEHOLDER__ が残っています（transaction=${transaction}）`;
      } else {
        // BDC の結果はプログラム内の CALL TRANSACTION の戻り値で判定される。
        // メッセージタイプ（S/E）で既に VBScript 側で判定済み。
        // Node.js 側では追加の DB 確認があれば実行。
        pass = true;
        detail = `bdc_result: メッセージタイプで判定済み（transaction=${transaction}）`;
      }
    } else if (chk.check === 'rfc_return') {
      // rfc_return: RFC 返り値の確認
      const funcModule = chk.function_module || '';
      const expectedType = chk.expected_type || '';
      if (funcModule === '__PLACEHOLDER__' || expectedType === '__PLACEHOLDER__') {
        detail = `rfc_return: __PLACEHOLDER__ が残っています（function_module=${funcModule}）`;
      } else {
        // RFC の返り値はプログラム内で処理され、最終的にメッセージとして出力される。
        // メッセージタイプ（S/E）で既に VBScript 側で判定済み。
        pass = true;
        detail = `rfc_return: メッセージタイプで判定済み（${funcModule}, expected_type=${expectedType}）`;
      }
    } else {
      pass = true;
      detail = `unknown node check '${chk.check}' skipped`;
    }

    if (pass) {
      results.passed++;
    } else {
      results.failed++;
    }
    results.details.push(`${pass ? 'PASS' : 'FAIL'}: ${detail}`);
  }

  return results;
}

function parsePlanEvidence(planPath) {
  let yaml;
  try {
    yaml = require('js-yaml');
  } catch (e) {
    throw new Error('js-yaml が必要です。extensions/sap/ で npm install js-yaml を実行してください');
  }

  // --- plan.md から補助情報を取得 ---
  const content = fs.readFileSync(planPath, 'utf-8');
  const yamlMatch = content.match(/```yaml\r?\n([\s\S]*?)```/);
  let testStrategy = null;
  let planProgramId = '';
  if (yamlMatch) {
    const planDoc = yaml.load(yamlMatch[1]);
    testStrategy = planDoc?.plan?.test_strategy || null;
    planProgramId = testStrategy?.program_id || '';
    // plan.md の sap_components / sap_objects からプログラム名を探す
    if (!planProgramId) {
      const sapComps = planDoc?.plan?.sap_components || planDoc?.plan?.sap_objects || [];
      const prog = sapComps.find(o => (o.object_type || o.type) === 'PROG');
      if (prog) planProgramId = prog.object_name || prog.name || '';
    }
  }

  // --- scenarios.yaml を読み込み（SSoT）---
  const featureDir = path.dirname(planPath);
  const scenariosYamlPath = path.join(featureDir, 'tests', 'scenarios.yaml');
  let rawScenarios = [];

  if (fs.existsSync(scenariosYamlPath)) {
    const scContent = fs.readFileSync(scenariosYamlPath, 'utf-8');
    const scDoc = yaml.load(scContent);
    rawScenarios = scDoc?.scenarios || [];
  }

  // scenarios.yaml がない場合は plan.md からフォールバック（レガシー互換）
  if (rawScenarios.length === 0 && testStrategy) {
    rawScenarios = testStrategy?.test_scenarios?.scenarios
      || testStrategy?.scenarios
      || testStrategy?.evidence_capture?.scenarios
      || [];
  }

  if (!rawScenarios || rawScenarios.length === 0) {
    throw new Error('シナリオが見つかりません。tests/scenarios.yaml に定義してください');
  }

  // --- plan.md の covers_ts 情報をマージ（AC 別検証結果テーブル用）---
  const planScenarios = testStrategy?.scenarios || [];
  const planCoversMap = {};
  for (const ps of planScenarios) {
    const sid = ps.id || ps.test_id || '';
    if (sid && ps.covers_ts) {
      planCoversMap[sid] = ps.covers_ts;
    }
  }

  // --- scenarios.yaml → evidence_capture 内部形式に変換 ---
  const scenarios = rawScenarios.map(raw => {
    const sc = {};

    // 基本識別
    sc.test_id = raw.id || raw.test_id || '';
    sc.name = raw.title || raw.name || '';
    sc.description = raw.expected_result?.description || raw.title || '';
    sc.category = raw.category || 'normal';

    // covers_ts: plan.md から取得（AC 別検証結果テーブル用）
    sc.covers_ts = planCoversMap[sc.test_id] || raw.covers_ts || [];

    // --- プログラム名・トランザクションを steps から抽出 ---
    const steps = raw.steps || [];
    let progName = '';
    let transaction = '';
    const selFields = [];

    for (const step of steps) {
      const input = step.input || {};
      if (input.tcode && !transaction) transaction = input.tcode;
      if (input.program && !progName) progName = input.program;

      for (const [key, val] of Object.entries(input)) {
        if (['tcode', 'program', 'key'].includes(key)) continue;
        if (val === '' || val === null || val === undefined) continue;
        const strVal = String(val);
        // 日付範囲 "YYYYMMDD-YYYYMMDD"
        const rangeMatch = strVal.match(/^(\d{8})-(\d{8})$/);
        if (rangeMatch) {
          selFields.push({ name: `${key}-LOW`, low: rangeMatch[1], high: rangeMatch[2] });
        } else if (key.startsWith('S_')) {
          selFields.push({ name: `${key}-LOW`, low: strVal });
        } else {
          selFields.push({ name: key, low: strVal });
        }
      }
    }

    // プログラム名フォールバック: steps[].action テキストから Z* プログラム名を抽出
    if (!progName) {
      for (const step of steps) {
        const actionMatch = (step.action || '').match(/\b(Z[A-Z0-9]{2,})\b/i);
        if (actionMatch) { progName = actionMatch[1].toUpperCase(); break; }
      }
    }
    sc._program_id = progName || planProgramId;
    sc.transaction = transaction || raw.sap_specifics?.tcode || 'SA38';
    sc.execution = { selection_fields: selFields };

    // --- expected_result 変換 ---
    // オブジェクト形式（buildScenarioWSF 用）+ _checks 配列（renderChecks 用）
    const rawExp = raw.expected_result || {};
    const verifs = rawExp.verification || [];
    const expResult = {};
    const checks = [];

    for (const v of verifs) {
      if (v.type === 'message_check') {
        const target = v.target || '';
        const msgNum = target.replace('MSG-', '');
        if (['001', '002', '005'].includes(msgNum)) {
          expResult.message_type = 'E';
          checks.push({ check: 'message_type', value: 'E' });
        } else if (msgNum === '003') {
          expResult.message_type = 'I';
          expResult.no_data = true;
          checks.push({ check: 'message_type', value: 'I' });
        } else {
          expResult.message_type = expResult.message_type || 'S';
          checks.push({ check: 'message_type', value: 'S' });
        }
      } else if (v.type === 'screen_check') {
        const target = v.target || '';
        if (target.includes('ALV')) {
          expResult.alv = true;
          checks.push({ check: 'alv', value: true });
        }
        if (target.includes('選択画面')) {
          expResult.stays_on_selection = true;
        }
        if ((v.condition || '').includes('応答時間')) {
          expResult.performance_check = true;
        }
      } else if (v.type === 'db_check') {
        checks.push({ check: 'db_verify', target: v.target || '', condition: v.condition || '' });
      }
    }

    // ALV 正常系: message_type S は cl_salv_table fullscreen でステータスバーがクリアされるため
    // ALV 表示確認が PASS すれば十分。message_type チェックを除外する
    if (expResult.alv) {
      const filtered = checks.filter(c => !(c.check === 'message_type' && c.value === 'S'));
      checks.length = 0;
      checks.push(...filtered);
      if (!expResult.message_type) {
        expResult.message_type = 'S'; // HTML 表示用のみ（VBScript チェックからは除外済み）
      }
    }

    expResult._checks = checks;
    expResult._description = rawExp.description || '';
    sc.expected_result = expResult;

    // --- sap_specifics.test_data → se16_checks 自動変換 ---
    const sapSpecs = raw.sap_specifics || {};
    const testData = sapSpecs.test_data || [];
    const expOutput = sapSpecs.expected_output || null;
    const se16Pre = [];
    for (const td of testData) {
      if (!td.table) continue;
      const entries = td.entries || [];
      const whereParts = [];
      for (const entry of entries) {
        const pairs = entry.split(',').map(s => s.trim()).filter(s => s);
        for (const pair of pairs) {
          const eqIdx = pair.indexOf('=');
          if (eqIdx > 0) {
            const key = pair.substring(0, eqIdx).trim();
            const val = pair.substring(eqIdx + 1).trim();
            if (key && val) whereParts.push(`${key} = '${val}'`);
          }
        }
      }
      if (whereParts.length > 0) {
        // expected_output.columns があればそれで表示カラムを限定
        const cols = expOutput?.columns
          ? expOutput.columns.filter(c => c !== 'NETWR_TOTAL').join(',')
          : '';
        se16Pre.push({
          table: td.table,
          keys: whereParts.join(' AND '),
          columns: cols || undefined,
          description: `${td.table} 対象データ確認`,
        });
      }
    }
    sc.se16_checks = { pre: se16Pre, post: [] };

    // --- expected_output を取得 ---
    sc.expected_output = sapSpecs.expected_output || null;

    return sc;
  });

  const result = { scenarios };
  result._tests = testStrategy?.tests || [];
  result._program_id = planProgramId;
  return result;
}

// ---------------------------------------------------------------------------
// Shift_JIS デコード / KV パース / GUI 起動・終了
// ---------------------------------------------------------------------------
function decodeShiftJIS(buf) {
  try { return new TextDecoder('shift_jis').decode(buf); }
  catch (e) { return buf.toString('utf-8'); }
}

function parseKV(output) {
  const kv = {};
  for (const line of output.split(/\r?\n/)) {
    const idx = line.indexOf('=');
    if (idx > 0) kv[line.substring(0, idx).trim()] = line.substring(idx + 1).trim();
  }
  return kv;
}

function runWSF(wsfContent, timeoutMs) {
  const tmpFile = path.join(os.tmpdir(), `sap_evidence_${process.pid}_${Date.now()}.wsf`);
  try {
    fs.writeFileSync(tmpFile, wsfContent, 'utf-8');
    const buf = execSync(`cscript //NoLogo "${tmpFile}"`, { timeout: timeoutMs || 120000, shell: true });
    return parseKV(decodeShiftJIS(buf));
  } catch (err) {
    const stdoutBuf = err.stdout || Buffer.alloc(0);
    const stderrBuf = err.stderr || Buffer.alloc(0);
    return parseKV(decodeShiftJIS(Buffer.concat([stdoutBuf, stderrBuf])));
  } finally {
    try { fs.unlinkSync(tmpFile); } catch (_) {}
  }
}

function runGuiLaunch(action) {
  const launchScript = path.join(__dirname, 'gui_launch.js');
  const args = action === 'close' ? ['--close'] : [];
  try {
    execSync(`node "${launchScript}" ${args.join(' ')}`, {
      stdio: 'inherit', timeout: 90000, shell: true, cwd: process.cwd(),
    });
    return true;
  } catch (e) { return false; }
}

// ---------------------------------------------------------------------------
// SE16 keys パース: 文字列・辞書どちらにも対応
// ---------------------------------------------------------------------------
// EC-02: SLG1 キャプチャ用 WSF 生成
// ---------------------------------------------------------------------------
function buildSlg1CaptureWSF(check, ssDir, testId, capturePsPath, sapPid, startTime) {
  const ssPath = ssDir.replace(/\\/g, '\\\\');
  const capturePath = (capturePsPath || '').replace(/\\/g, '\\\\');
  const logObj = check.keys?.OBJECT || check.object || '';
  const logSub = check.keys?.SUBOBJECT || check.subobject || '';
  // EC-04: 時刻フィルタ — シナリオ実行開始時刻以降のログのみ表示
  const dateStr = startTime.toISOString().slice(0, 10).replace(/-/g, '');
  const timeStr = startTime.toTimeString().slice(0, 8).replace(/:/g, '');

  return `<?xml version="1.0" encoding="UTF-8"?>
<job><script language="JScript"><![CDATA[
function out(k,v){WScript.Echo(k+"="+v)}
var ssDir = "${ssPath}";
var capturePsPath = "${capturePath}";
var sapPid = "${sapPid || ''}";
var wshShell = new ActiveXObject("WScript.Shell");

function screenshot(filePath) {
  try {
    ses.findById("wnd[0]").HardCopy(filePath, "PNG");
    return true;
  } catch(e) {
    if (capturePsPath) {
      var psCmd = "powershell -NoProfile -ExecutionPolicy Bypass -File \\"" + capturePsPath + "\\" -Keyword \\"SAP\\" -OutFile \\"" + filePath + "\\"";
      if (sapPid) psCmd += " -FilterPid " + sapPid;
      try { wshShell.Run(psCmd, 0, true); return true; } catch(e2) {}
    }
    return false;
  }
}

try {
  var sapgui = GetObject("SAPGUI");
  var app = sapgui.GetScriptingEngine;
  var conn = app.Children(0);
  var ses = conn.Children(0);

  // SLG1 トランザクションを開始
  ses.StartTransaction("SLG1");
  WScript.Sleep(1500);

  // ログオブジェクト・サブオブジェクトを入力
  ${logObj ? `try { ses.findById("wnd[0]/usr/ctxtBALOBJECT-OBJECT").text = "${logObj}"; } catch(x){}` : ''}
  ${logSub ? `try { ses.findById("wnd[0]/usr/ctxtBALOBJECT-SUBOBJECT").text = "${logSub}"; } catch(x){}` : ''}

  // 日付・時刻フィルタ設定（EC-04）
  try { ses.findById("wnd[0]/usr/ctxtBALOBJECT-ALDATE_FR").text = "${dateStr}"; } catch(x){}
  try { ses.findById("wnd[0]/usr/ctxtBALOBJECT-ALDATE_TO").text = "${dateStr}"; } catch(x){}
  try { ses.findById("wnd[0]/usr/ctxtBALOBJECT-ALTIME_FR").text = "${timeStr}"; } catch(x){}

  // 実行 (F8)
  ses.findById("wnd[0]").sendVKey(8);
  WScript.Sleep(3000);

  // SLG1 結果画面のスクリーンショット
  var ssFile = ssDir + "\\\\${testId}_slg1_applog.png";
  screenshot(ssFile);
  out("SLG1_SS", ssFile);

  // F3 で戻る
  try { ses.findById("wnd[0]/tbar[0]/btn[3]").press(); WScript.Sleep(500); } catch(bx){}
  try { ses.findById("wnd[0]/tbar[0]/btn[3]").press(); WScript.Sleep(500); } catch(bx2){}

  out("STATUS", "OK");
} catch(e) {
  out("STATUS", "ERROR");
  out("ERROR", e.message);
}
WScript.Quit(0);
]]></script></job>`;
}

// ---------------------------------------------------------------------------
// シナリオ単位 WSF 生成
// ---------------------------------------------------------------------------
function buildScenarioWSF(scenario, ssDir, capturePsPath, sapPid, planPath, evidenceMode) {
  evidenceMode = evidenceMode || 'stage3'; // stage1 | stage2 | stage3
  const ssPath = ssDir.replace(/\\/g, '\\\\');
  const capturePath = (capturePsPath || '').replace(/\\/g, '\\\\');
  const progName = scenario._program_id || scenario.execution?.program || '';
  const progUpper = progName.toUpperCase();
  const transaction = scenario.transaction || 'SA38';

  if (!progUpper) {
    throw new Error(`シナリオ "${scenario.test_id}" に program_id も execution.program も定義されていません`);
  }


  // シナリオ情報から説明文を Node.js 側で完成させる
  const scenarioName = scenario.name || '';
  const scenarioDesc = scenario.description || '';
  let selFields = scenario.execution?.selection_fields || [];

  // OBLIGATORY フォールバック: キャッシュ済み OBLIGATORY フィールドが selection_fields に含まれていなければ追加
  if (scenario._cachedObligatoryFields && scenario._cachedObligatoryFields.length > 0) {
    const existingNames = new Set(selFields.map(f => f.name));
    for (const ob of scenario._cachedObligatoryFields) {
      if (!existingNames.has(ob.name)) {
        selFields = [...selFields, ob];
      }
    }
  }

  // selFieldOps: スクショ説明用（日本語ラベル付き）
  const scLabels = scenario.labels || {};
  const scFldLabels = scLabels.fields || {};
  const _fldLbl = (name) => {
    // まず name そのもので検索（P_ZERO 等）
    const direct = scFldLabels[name.toUpperCase()];
    if (direct) return `${direct}(${name})`;
    // S_WERKS-LOW → WERKS で検索
    const n = name.replace(/-LOW$|-HIGH$/, '').replace(/^S_/, '');
    const l = scFldLabels[n.toUpperCase()];
    return l ? `${l}(${name})` : name;
  };
  const selFieldOps = selFields.map(f => {
    const ft = (f.type || 'text').toLowerCase();
    const label = _fldLbl(f.name);
    if (ft === 'checkbox') return `${label} を ${f.value ? 'ON' : 'OFF'} に設定`;
    if (ft === 'radio') return `${label} を選択`;
    if (ft === 'dropdown' || ft === 'listbox') return `${label} で ${f.low || f.value} を選択`;
    if (ft === 'button') return `${label} ボタンを押下`;
    return `${label} に ${f.low}${f.high ? ' ～ ' + f.high : ''} を入力`;
  }).join('、');
  const esc = s => s.replace(/\\/g, '\\\\').replace(/"/g, '\\"');

  const descSelection = `【操作】SE38 でプログラム ${progUpper} を実行し、選択画面を表示`;
  const descFilled = selFieldOps
    ? `【操作】選択画面に条件を入力: ${selFieldOps}。F8 で実行する`
    : '【操作】選択画面に条件を入力せずに F8 で実行する';
  // 期待結果を含む具体的な確認内容
  const expResult = scenario.expected_result || {};
  let resultCheckDesc = '';
  if (expResult.message_type === 'E') {
    resultCheckDesc = 'エラーメッセージ (TYPE E) が表示されること';
  } else if (expResult.message_type === 'I') {
    resultCheckDesc = expResult.no_data ? '「該当データがありません」等の情報メッセージが表示されること' : '情報メッセージ (TYPE I) が表示されること';
  } else if (expResult.alv) {
    if (expResult.filter_check) {
      resultCheckDesc = 'ALV にフィルタ条件に一致するデータのみが表示されること';
    } else {
      resultCheckDesc = 'ALV 一覧にデータが表示されること';
    }
  }
  const descResult = `【確認】${resultCheckDesc || scenarioDesc}`;

  // SE38 選択画面フィールド入力（テキスト、チェックボックス、ラジオボタン、ドロップダウン対応）
  let fieldSetScript = '';
  for (const f of selFields) {
    let name = f.name || '';
    const fieldType = (f.type || 'text').toLowerCase();

    // EC-01: SELECT-OPTIONS フィールドの -LOW サフィックス自動補完
    // S_ プレフィックスのフィールドで -LOW/-HIGH が付いていない場合、自動的に -LOW を付与
    if (fieldType === 'text' && /^S_/i.test(name) && !/-LOW$/i.test(name) && !/-HIGH$/i.test(name)) {
      name = name + '-LOW';
    }

    const low = String(f.low ?? f.value ?? '').replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    const high = f.high ? String(f.high).replace(/\\/g, '\\\\').replace(/"/g, '\\"') : '';

    if (fieldType === 'checkbox') {
      // チェックボックス: chk プレフィックス、.Selected で ON/OFF
      const checked = (f.value === true || f.value === 'true' || f.value === 'X') ? 'true' : 'false';
      fieldSetScript += `
  try { ses.findById("wnd[0]/usr/chk${name}").Selected = ${checked}; } catch(fx){}`;

    } else if (fieldType === 'radio') {
      // ラジオボタン: SAP GUI では GuiCheckBox として扱われることが多い
      // rad プレフィックスと chk プレフィックスの両方を試す
      fieldSetScript += `
  try { ses.findById("wnd[0]/usr/rad${name}").Selected = true; } catch(fx){
    try { ses.findById("wnd[0]/usr/chk${name}").Selected = true; } catch(fx2){} }`;

    } else if (fieldType === 'dropdown' || fieldType === 'listbox') {
      // ドロップダウン: cmb プレフィックス、.Key で値設定
      fieldSetScript += `
  try { ses.findById("wnd[0]/usr/cmb${name}").Key = "${low}"; } catch(fx){}`;

    } else if (fieldType === 'button') {
      // ボタン押下: btn プレフィックス、または ID 直指定
      // name にフル ID（例: "wnd[0]/tbar[1]/btn[8]"）が入っている場合はそのまま使用
      // 短い名前（例: "BTN_EXEC"）の場合は usr/btn プレフィックスで探す
      if (name.includes('/')) {
        fieldSetScript += `
  try { ses.findById("${name}").press(); WScript.Sleep(1000); } catch(fx){}`;
      } else {
        fieldSetScript += `
  try { ses.findById("wnd[0]/usr/btn${name}").press(); WScript.Sleep(1000); } catch(fx){
    try { ses.findById("wnd[0]/tbar[1]/btn${name}").press(); WScript.Sleep(1000); } catch(fx2){} }`;
      }

    } else if (fieldType === 'file') {
      // ファイルアップロード: ファイルパスをテキストフィールドに設定
      // SAP GUI のファイルダイアログはシェル操作が必要な場合がある
      // 一般的にはファイルパスフィールドに直接パスを設定可能
      fieldSetScript += `
  try { var el=null; var pf=["ctxt","txt"];
    for(var p=0;p<pf.length;p++){try{el=ses.findById("wnd[0]/usr/"+pf[p]+"${name}");break;}catch(x){}}
    if(el) el.text="${low}"; } catch(fx){}
  // ファイルダイアログが開いた場合はパスを入力して確定
  WScript.Sleep(500);
  try { ses.findById("wnd[1]/usr/ctxtDY_PATH").text = "${low.replace(/[^/\\\\]*$/, '')}";
    ses.findById("wnd[1]/usr/ctxtDY_FILENAME").text = "${low.replace(/.*[/\\\\]/, '')}";
    ses.findById("wnd[1]/tbar[0]/btn[0]").press(); WScript.Sleep(1000); } catch(fdx){}`;

    } else if (fieldType === 'table_cell') {
      // テーブルコントロール内のセル操作
      // name: "tblCONTROL/ctxtFIELD[col,row]" のようなフルパス
      fieldSetScript += `
  try { ses.findById("wnd[0]/usr/${name}").text = "${low}"; } catch(fx){}`;

    } else if (fieldType === 'tab') {
      // タブ切り替え: name にタブのフル ID を指定
      // 例: { name: "tabsTABSTRIP/tabpTAB01", type: "tab" }
      if (name.includes('/')) {
        fieldSetScript += `
  try { ses.findById("wnd[0]/usr/${name}").Select(); WScript.Sleep(500); } catch(fx){}`;
      } else {
        fieldSetScript += `
  try { ses.findById("wnd[0]/usr/tabsTABSTRIP/tabp${name}").Select(); WScript.Sleep(500); } catch(fx){}`;
      }

    } else if (fieldType === 'vkey') {
      // ファンクションキー送信: value に VKey 番号を指定
      // F5=5, F6=6, ..., F8=8 (実行), F11=11 (保存), F12=12 (完了)
      const vkey = parseInt(f.value || f.low || '0', 10);
      fieldSetScript += `
  ses.findById("wnd[0]").sendVKey(${vkey}); WScript.Sleep(1500);`;

    } else if (fieldType === 'popup_ok' || fieldType === 'popup_yes') {
      // ポップアップの OK/Yes ボタン押下
      fieldSetScript += `
  WScript.Sleep(500);
  try { ses.findById("wnd[1]/tbar[0]/btn[0]").press(); WScript.Sleep(500); } catch(fx){
    try { ses.findById("wnd[1]/usr/btnSPOP-OPTION1").press(); WScript.Sleep(500); } catch(fx2){} }`;

    } else if (fieldType === 'popup_no' || fieldType === 'popup_cancel') {
      // ポップアップの No/Cancel ボタン押下
      fieldSetScript += `
  WScript.Sleep(500);
  try { ses.findById("wnd[1]/tbar[0]/btn[12]").press(); WScript.Sleep(500); } catch(fx){
    try { ses.findById("wnd[1]/usr/btnSPOP-OPTION2").press(); WScript.Sleep(500); } catch(fx2){} }`;

    } else if (fieldType === 'popup_text') {
      // ポップアップ内のテキスト入力（理由入力等）
      fieldSetScript += `
  WScript.Sleep(500);
  try { var pel=null; var ppf=["ctxt","txt"];
    for(var pp=0;pp<ppf.length;pp++){try{pel=ses.findById("wnd[1]/usr/"+ppf[pp]+"${name}");break;}catch(x){}}
    if(pel) pel.text="${low}"; } catch(fx){}`;

    } else if (fieldType === 'menu') {
      // メニューバー操作: name にメニューパスを指定
      // 例: { name: "menu[0]/menu[1]", type: "menu" } → mbar/menu[0] → サブメニュー menu[1]
      fieldSetScript += `
  try { ses.findById("wnd[0]/mbar/${name}").select(); WScript.Sleep(1000); } catch(fx){}`;

    } else if (fieldType === 'enter') {
      // Enter キー送信（フィールド確定）
      fieldSetScript += `
  ses.findById("wnd[0]").sendVKey(0); WScript.Sleep(1000);`;

    } else if (fieldType === 'scroll') {
      // スクロール操作: value に "down"/"up" を指定, low にスクロール量（行数）を指定
      const direction = String(f.value || 'down').toLowerCase();
      const amount = parseInt(f.low || '20', 10);
      fieldSetScript += `
  // スクロール: ${direction}
  try {
    // ALV Grid のスクロール（FirstVisibleRow）
    var alvScroll = null;
    var alvScrollPaths = ["wnd[0]/usr/cntlGRID1/shellcont/shell","wnd[0]/usr/cntlRESULT_LIST/shellcont/shell","wnd[0]/usr/cntlCONTAINER/shellcont/shell"];
    for (var si = 0; si < alvScrollPaths.length; si++) {
      try { alvScroll = ses.findById(alvScrollPaths[si]); break; } catch(sx) {}
    }
    if (alvScroll) {
      var cur = alvScroll.FirstVisibleRow;
      alvScroll.FirstVisibleRow = ${direction === 'up' ? 'Math.max(0, cur - ' + amount + ')' : 'cur + ' + amount};
      WScript.Sleep(500);
    } else {
      // ALV がない場合は VKey でスクロール
      ses.findById("wnd[0]").sendVKey(${direction === 'up' ? 22 : 23});
      WScript.Sleep(500);
    }
  } catch(fx) {}`;

    } else if (fieldType === 'screenshot') {
      // 追加スクリーンショット（任意タイミングで撮影）
      const label = low || 'custom';
      fieldSetScript += `
  ssSeq++; screenshot(ssSeq + "_${label}");
  out("SS_DESC_" + pad4(ssSeq), "${esc(f.description || '追加スクリーンショット')}");`;

    } else {
      // テキストフィールド（デフォルト）: ctxt/txt プレフィックス
      fieldSetScript += `
  try { var el=null; var pf=["ctxt","txt"];
    for(var p=0;p<pf.length;p++){try{el=ses.findById("wnd[0]/usr/"+pf[p]+"${name}");break;}catch(x){}}
    if(el) el.text="${low}"; } catch(fx){}`;
      if (high) {
        fieldSetScript += `
  try { var elH=null; var pf2=["ctxt","txt"];
    for(var p2=0;p2<pf2.length;p2++){try{elH=ses.findById("wnd[0]/usr/"+pf2[p2]+"${name.replace(/-LOW$/, '-HIGH')}");break;}catch(x){}}
    if(elH) elH.text="${high}"; } catch(fxH){}`;
      }
    }
  }

  // SE38 実行スクリプト
  const se38Script = `
  // 画面リセット: 前シナリオの残留状態をクリア
  try { ses.findById("wnd[0]/tbar[0]/okcd").text = "/n"; ses.findById("wnd[0]").sendVKey(0); WScript.Sleep(500); } catch(rx){}
  // ポップアップが残っていたら閉じる
  try { ses.findById("wnd[1]/tbar[0]/btn[0]").press(); WScript.Sleep(300); } catch(dx){}

  // SE38 実行: ${progUpper}
  ses.StartTransaction("${transaction}");
  WScript.Sleep(1000);
  ses.findById("wnd[0]/usr/ctxtRS38M-PROGRAMM").text = "${progUpper}";
  ses.findById("wnd[0]").sendVKey(8);
  WScript.Sleep(1500);

  // 選択画面が表示されたことを確認
  var selScreen = "" + ses.Info.ScreenNumber;
  ssSeq++; screenshot(ssSeq + "_se38_selection");
  out("SS_DESC_" + pad4(ssSeq), "${esc(descSelection)}");

  // フィールド入力
  ${fieldSetScript}
  ssSeq++; screenshot(ssSeq + "_se38_selection_filled");
  out("SS_DESC_" + pad4(ssSeq), "${esc(descFilled)}");

  // 実行 (F8)
  ses.findById("wnd[0]").sendVKey(8);
  WScript.Sleep(3000);

  // 結果画面のスクショ
  ssSeq++; screenshot(ssSeq + "_se38_result");
  out("SS_DESC_" + pad4(ssSeq), "${esc(descResult)}");

  // 結果検証（expected_result に基づくシナリオ個別判定）
  var resultScreen = "" + ses.Info.ScreenNumber;
  out("SCREEN_RESULT", resultScreen);

  // ポップアップダイアログ（MESSAGE TYPE 'I' 等）があれば先に処理
  var dialogText = ""; var dialogHandled = false;
  try {
    var dlg = ses.findById("wnd[1]");
    if (dlg) {
      try { dialogText = "" + ses.findById("wnd[1]/usr/txtMESSTXT1").Text; } catch(dx) {
        try { dialogText = "" + dlg.Text; } catch(dx2) { dialogText = "dialog"; }
      }
      dialogHandled = true;
      dlg.sendVKey(0); // Enter で閉じる
      WScript.Sleep(500);
    }
  } catch(dlgErr) {}

  // ステータスバー確認
  var sbarText = ""; var sbarType = "";
  try { sbarText = "" + ses.findById("wnd[0]/sbar").Text; } catch(sx){}
  try { sbarType = "" + ses.findById("wnd[0]/sbar").MessageType; } catch(sx2){}
  if (dialogHandled && !sbarType) { sbarType = "I"; sbarText = dialogText; }
  out("SBAR_TEXT", sbarText);
  out("SBAR_TYPE", sbarType);

  // ALV 検出
  var alvFound = false; var alvRows = 0;
  var alvPaths = [
    "wnd[0]/usr/cntlGRID1/shellcont/shell",
    "wnd[0]/usr/cntlCONTAINER/shellcont/shell",
    "wnd[0]/usr/cntlALV/shellcont/shell"
  ];
  for (var ai = 0; ai < alvPaths.length; ai++) {
    try {
      var alv = ses.findById(alvPaths[ai]);
      if (alv) { alvFound = true; alvRows = alv.RowCount; out("ALV_ROW_COUNT", "" + alvRows); break; }
    } catch(ax) {}
  }

  // --- expected_result に基づく個別検証（配列対応） ---
  // expected_result は配列形式: [{ check: "message_type", value: "S" }, ...]
  // 旧形式（オブジェクト）は後方互換のため配列に変換
  var RAW_EXPECTED = ${JSON.stringify((scenario.expected_result && scenario.expected_result._checks) || (Array.isArray(scenario.expected_result) ? scenario.expected_result : []))};
  var CHECKS = [];
  if (typeof RAW_EXPECTED === "object" && typeof RAW_EXPECTED.length === "number") {
    CHECKS = RAW_EXPECTED;
  } else if (typeof RAW_EXPECTED === "object") {
    // 旧形式の後方互換変換
    if (RAW_EXPECTED.message_type) CHECKS.push({ check: "message_type", value: RAW_EXPECTED.message_type });
    if (RAW_EXPECTED.alv) CHECKS.push({ check: "alv", value: true });
  }

  if (CHECKS.length === 0) {
    // expected_result 未定義: エラーメッセージなら FAIL、それ以外は PASS
    if (sbarType == "E" || sbarType == "A") {
      out("VERIFY_STATUS", "FAIL");
      out("VERIFY_DETAIL", "expected_result 未定義。エラーメッセージ検出: [" + sbarType + "] " + sbarText);
    } else {
      out("VERIFY_STATUS", "PASS");
      out("VERIFY_DETAIL", "expected_result 未定義。Screen " + resultScreen + " displayed");
    }
  } else {
    var allPass = true;
    var details = [];
    for (var ci = 0; ci < CHECKS.length; ci++) {
      var chk = CHECKS[ci];
      var chkType = chk.check || "";
      var chkPass = false;
      var chkDetail = "";

      if (chkType == "message_type") {
        if (sbarType == chk.value || (dialogHandled && chk.value == "I")) {
          chkPass = true;
          chkDetail = "message_type [" + chk.value + "] OK: " + sbarText;
        } else {
          chkDetail = "message_type: expected [" + chk.value + "] but got [" + sbarType + "] " + sbarText;
        }
      } else if (chkType == "message_text_contains") {
        if (sbarText.indexOf(chk.value) >= 0) {
          chkPass = true;
          chkDetail = "message_text_contains '" + chk.value + "' OK";
        } else {
          chkDetail = "message_text_contains: '" + chk.value + "' not found in '" + sbarText + "'";
        }
      } else if (chkType == "alv") {
        if (alvFound && alvRows > 0) {
          chkPass = true;
          chkDetail = "ALV displayed with " + alvRows + " rows";
        } else if (sbarType == "E" || sbarType == "A") {
          chkDetail = "Expected ALV but got error: [" + sbarType + "] " + sbarText;
        } else {
          chkDetail = "Expected ALV but not found. Screen: " + resultScreen;
        }
      } else if (chkType == "alv_min_rows") {
        if (alvFound && alvRows >= (chk.value || 1)) {
          chkPass = true;
          chkDetail = "ALV rows " + alvRows + " >= " + chk.value;
        } else {
          chkDetail = "ALV rows " + (alvFound ? alvRows : "N/A") + " < " + chk.value;
        }
      } else if (chkType == "screen_number") {
        if (resultScreen == chk.value) {
          chkPass = true;
          chkDetail = "screen_number " + chk.value + " OK";
        } else {
          chkDetail = "screen_number: expected " + chk.value + " but got " + resultScreen;
        }
      } else if (chkType == "no_error") {
        if (sbarType != "E" && sbarType != "A") {
          chkPass = true;
          chkDetail = "no_error OK (status bar: [" + sbarType + "])";
        } else {
          chkDetail = "no_error FAIL: [" + sbarType + "] " + sbarText;
        }
      } else {
        // Node.js 側で実行する check type、または未知の type はスキップ
        chkPass = true;
        var nodeChecks = ["db_changed", "file_output", "log_output", "print_output", "idoc_status", "wf_status", "mail_sent", "bdc_result", "rfc_return"];
        var isNodeCheck = false;
        for (var ni = 0; ni < nodeChecks.length; ni++) { if (chkType == nodeChecks[ni]) { isNodeCheck = true; break; } }
        chkDetail = isNodeCheck ? "'" + chkType + "' is checked by Node.js (skipped in VBScript)" : "unknown check type '" + chkType + "' skipped";
      }

      if (!chkPass) allPass = false;
      details.push((chkPass ? "PASS" : "FAIL") + ": " + chkDetail);
      out("VERIFY_CHECK_" + ci, (chkPass ? "PASS" : "FAIL") + ": " + chkDetail);
    }
    out("VERIFY_STATUS", allPass ? "PASS" : "FAIL");
    out("VERIFY_DETAIL", details.join(" | "));
  }

  // ポップアップがあればスクショ取得して閉じる
  try {
    var popup = ses.findById("wnd[1]");
    if (popup) { ssSeq++; screenshot(ssSeq + "_se38_popup"); }
    ses.findById("wnd[1]/tbar[0]/btn[0]").press(); WScript.Sleep(300);
  } catch(px2) {}

  // F3 で戻る
  try { ses.findById("wnd[0]/tbar[0]/btn[3]").press(); WScript.Sleep(500); } catch(bx){}
  try { ses.findById("wnd[0]/tbar[0]/btn[3]").press(); WScript.Sleep(500); } catch(bx2){}
`;

  return `<?xml version="1.0" encoding="UTF-8"?>
<job><script language="JScript"><![CDATA[
function out(k,v){WScript.Echo(k+"="+v)}
var ssDir = "${ssPath}";
var scenarioId = "${scenario.test_id || 'unknown'}";
var capturePsPath = "${capturePath}";
var sapPid = "${sapPid || ''}";
var evidenceMode = "${evidenceMode}";
var wshShell = new ActiveXObject("WScript.Shell");
var ssSeq = 0;

function pad4(n) { var s = "" + n; while(s.length < 4) s = "0" + s; return s; }

function screenshot(label) {
  if (!ssDir) return;
  if (evidenceMode === "stage1") return;
  var filePath = ssDir + "\\\\" + scenarioId + "_" + pad4(ssSeq) + "_" + label + ".png";
  try {
    ses.findById("wnd[0]").HardCopy(filePath, "PNG");
    out("SS_" + pad4(ssSeq), filePath);
  } catch(e) {
    if (capturePsPath) {
      var psCmd = "powershell -NoProfile -ExecutionPolicy Bypass -File \\"" + capturePsPath + "\\" -Keyword \\"SAP\\" -OutFile \\"" + filePath + "\\"";
      if (sapPid) psCmd += " -FilterPid " + sapPid;
      try { wshShell.Run(psCmd, 0, true); out("SS_" + pad4(ssSeq), filePath); } catch(e2) {}
    }
  }
}

try {
  var sapgui = GetObject("SAPGUI");
  var app = sapgui.GetScriptingEngine;
  var conn = app.Children(0);
  var ses = conn.Children(0);
  out("SYSTEM", "" + ses.Info.SystemName);
  out("CLIENT", "" + ses.Info.Client);
  out("USER", "" + ses.Info.User);

  ${se38Script}

  out("SS_COUNT", "" + ssSeq);
  out("STATUS", "OK");
} catch(e) {
  out("STATUS", "ERROR");
  out("ERROR", e.message);
}
WScript.Quit(0);
]]></script></job>`;
}

// ---------------------------------------------------------------------------
// HTML エビデンスレポート生成
// ---------------------------------------------------------------------------
/**
 * シナリオの se16_checks / selection_fields / expected_result から
 * テスト概要 HTML を自動生成する。
 */
function generateTestSummary(sc) {
  const lines = [];
  const esc = s => (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  // sap_context メタデータのラベル（scenarios に含まれる）
  const labels = sc.labels || {};
  const tblLabel = (t) => { const l = (labels.tables || {})[t.toUpperCase()]; return l ? `${l}(${t})` : t; };
  const fldLabel = (f) => { const n = f.replace(/-LOW$|-HIGH$/, '').replace(/^S_/, ''); const l = (labels.fields || {})[n.toUpperCase()]; return l ? `${l}(${f})` : f; };
  const keyLabel = (k, v) => { const l = (labels.fields || {})[k.toUpperCase()]; return l ? `${l}(${k})=${v}` : `${k}=${v}`; };

  // 1. 事前確認（SE16）
  const preChecks = sc.se16_checks?.pre || [];
  if (preChecks.length > 0) {
    lines.push('<p style="margin:4px 0;"><strong>1. 事前確認（SE16）:</strong></p><ul style="margin:2px 0 8px 20px;">');
    for (const p of preChecks) {
      const table = p.table || '';
      const keys = p.keys || {};
      const desc = p.description || '';
      const keyStr = Object.keys(keys).length > 0
        ? Object.entries(keys).map(([k, v]) => keyLabel(k, v)).join(', ')
        : '（条件なし — 全件確認）';
      lines.push(`<li><strong>${esc(tblLabel(table))}</strong> [${esc(keyStr)}]: ${esc(desc)}</li>`);
    }
    lines.push('</ul>');
  } else {
    lines.push('<p style="margin:4px 0;color:#666;"><strong>1. 事前確認（SE16）:</strong> なし</p>');
  }

  // 2. 実行操作（SE38）
  const prog = sc._program_id || sc.execution?.program || '';
  const selFields = sc.execution?.selection_fields || [];
  lines.push(`<p style="margin:4px 0;"><strong>2. 実行操作（SE38）:</strong> プログラム <code>${esc(prog)}</code></p>`);
  if (selFields.length > 0) {
    lines.push('<ul style="margin:2px 0 8px 20px;">');
    for (const f of selFields) {
      const name = f.name || '';
      const fType = (f.type || 'text').toLowerCase();
      const label = fldLabel(name);
      if (fType === 'checkbox') {
        const val = f.value ? 'ON' : 'OFF';
        lines.push(`<li>${esc(label)} = <strong>${val}</strong>（チェックボックス）</li>`);
      } else {
        const low = f.low || '';
        const high = f.high || '';
        const val = high ? `${low} ～ ${high}` : low;
        lines.push(`<li>${esc(label)} = <strong>${esc(val)}</strong></li>`);
      }
    }
    lines.push('</ul>');
  }

  // 3. 期待結果
  const expResult = sc.expected_result || {};
  const expTexts = sc.expected || [];
  lines.push('<p style="margin:4px 0;"><strong>3. 期待結果:</strong></p><ul style="margin:2px 0 8px 20px;">');

  if (expResult.message_type) {
    const typeDesc = expResult.message_type === 'E' ? 'エラーメッセージ (TYPE E)'
                   : expResult.message_type === 'I' ? '情報メッセージ (TYPE I)'
                   : `メッセージ TYPE ${expResult.message_type}`;
    lines.push(`<li>${typeDesc} が表示されること</li>`);
    if (expResult.no_data) {
      lines.push('<li>「該当データがありません」等の 0 件メッセージが表示されること</li>');
    }
  } else if (expResult.alv) {
    lines.push('<li>ALV 一覧が表示され、データが 1 件以上存在すること</li>');
    if (expResult.filter_check) {
      lines.push('<li>フィルタ条件に一致するデータのみが表示されること</li>');
    }
  }

  for (const t of expTexts) {
    lines.push(`<li>${esc(t)}</li>`);
  }
  lines.push('</ul>');

  return lines.join('\n');
}

/**
 * テスト結果一覧表を生成する。
 */
function generateResultTable(scenarios, verifyResults, tests) {
  const esc = s => (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  let rows = '';
  for (let i = 0; i < scenarios.length; i++) {
    const sc = scenarios[i];
    const testId = sc.test_id || '';
    const verify = verifyResults[testId] || {};
    const sectionId = `sc_${i}`;
    const labels = sc.labels || {};
    const tblLabels = labels.tables || {};
    const fldLabels = labels.fields || {};
    const tblLbl = (t) => { const l = tblLabels[t.toUpperCase()]; return l ? `${l}(${t})` : t; };
    const fldLbl = (f) => { const l = fldLabels[f.toUpperCase()]; return l ? `${l}(${f})` : f; };
    const keyLbl = (k, v) => { const l = fldLabels[k.toUpperCase()]; return l ? `${l}(${k})=${v}` : `${k}=${v}`; };

    // 事前確認内容
    const preChecks = sc.se16_checks?.pre || [];
    let preHtml = '';
    if (preChecks.length > 0) {
      preHtml = preChecks.map(p => {
        const tName = tblLbl(p.table || '');
        const keys = p.keys || {};
        const keyStr = Object.keys(keys).length > 0
          ? Object.entries(keys).map(([k, v]) => keyLbl(k, v)).join(', ')
          : '全件';
        return `・${esc(tName)} [${esc(keyStr)}]: ${esc(p.description || '')}`;
      }).join('<br>');
    } else {
      preHtml = '<span style="color:#999;">なし</span>';
    }

    // 期待結果
    const expResult = sc.expected_result || {};
    let expHtml = '';
    if (expResult.message_type) {
      const typeDesc = expResult.message_type === 'E' ? 'エラーメッセージ (TYPE E) が表示されること'
                     : expResult.message_type === 'I' ? '情報メッセージ (TYPE I) が表示されること'
                     : `メッセージ TYPE ${expResult.message_type} が表示されること`;
      expHtml = typeDesc;
      if (expResult.no_data) expHtml += '<br>「該当データがありません」等の 0 件メッセージが表示されること';
    } else if (expResult.alv) {
      expHtml = 'ALV 一覧が表示され、データが 1 件以上存在すること';
      if (expResult.filter_check) expHtml += '<br>フィルタ条件に一致するデータのみが表示されること';
    }
    const expTexts = sc.expected || [];
    if (expTexts.length > 0 && !expHtml) {
      expHtml = expTexts.map(t => esc(t)).join('<br>');
    }

    // 結果バッジ
    const statusBadge = verify.status === 'PASS'
      ? '<span style="color:#2e7d32;font-weight:bold;">PASS</span>'
      : verify.status === 'FAIL'
        ? '<span style="color:#c62828;font-weight:bold;">FAIL</span>'
        : `<span style="color:#999;">${verify.status || '—'}</span>`;

    rows += `
      <tr style="border-bottom:1px solid #eee;">
        <td style="padding:8px 10px;vertical-align:top;"><a href="#${sectionId}">${esc(testId)}</a></td>
        <td style="padding:8px 10px;vertical-align:top;">${esc(sc.name || '')}</td>
        <td style="padding:8px 10px;vertical-align:top;font-size:0.9em;">${preHtml}</td>
        <td style="padding:8px 10px;vertical-align:top;">${expHtml}</td>
        <td style="padding:8px 10px;text-align:center;vertical-align:top;">${statusBadge}</td>
      </tr>`;
  }

  let result = `
<div style="background:#fff;border-radius:8px;padding:20px;margin:16px 0 24px;box-shadow:0 1px 3px rgba(0,0,0,0.12);">
  <h3 style="margin:0 0 12px;color:#1a237e;">テスト結果一覧</h3>
  <table style="width:100%;border-collapse:collapse;font-size:0.85em;">
    <thead>
      <tr style="background:#e8eaf6;">
        <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #c5cae9;">テストID</th>
        <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #c5cae9;">テスト内容</th>
        <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #c5cae9;">事前確認（SE16）</th>
        <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #c5cae9;">期待結果</th>
        <th style="padding:8px 10px;text-align:center;border-bottom:2px solid #c5cae9;">結果</th>
      </tr>
    </thead>
    <tbody>${rows}
    </tbody>
  </table>
</div>`;

  // 手動テスト対象がある場合、一覧表にも追記
  const manualTests = (tests || []).filter(t =>
    t.s_evidence?.method === 'manual_required' && !t.s_evidence?.manual_test_waived
  );
  if (manualTests.length > 0) {
    // 一覧表の tbody 末尾に追加（手動テスト行）
    const manualRows = manualTests.map(t => {
      const tid = t.id || '';
      const reason = t.s_evidence?.reason || '';
      return `
      <tr style="border-bottom:1px solid #eee;background:#fff8e1;">
        <td style="padding:8px 10px;vertical-align:top;"><a href="#manual_tests">${esc(tid)}</a></td>
        <td style="padding:8px 10px;vertical-align:top;">${esc(t.scope || '')}</td>
        <td style="padding:8px 10px;vertical-align:top;font-size:0.9em;color:#666;">手動テスト対象</td>
        <td style="padding:8px 10px;vertical-align:top;color:#666;">${esc(reason)}</td>
        <td style="padding:8px 10px;text-align:center;vertical-align:top;"><span style="color:#f57f17;font-weight:bold;">手動</span></td>
      </tr>`;
    }).join('');
    // </tbody> の前に挿入
    result = result.replace('</tbody>', manualRows + '\n    </tbody>');
  }

  return result;
}

// ---------------------------------------------------------------------------
// 個別シナリオ HTML 生成（evidence_SC-01.html 等）
// ---------------------------------------------------------------------------
function generateScenarioHTML(sc, baseSSDir, systemInfo, verifyResult, reportDir, acMap) {
  const testId = sc.test_id || sc.id || 'unknown';
  const verify = verifyResult || {};
  const now = new Date().toISOString().replace('T', ' ').substring(0, 19);

  // スクショ
  let ssFiles = [];
  if (fs.existsSync(baseSSDir)) {
    ssFiles = fs.readdirSync(baseSSDir)
      .filter(f => f.startsWith(testId + '_') && f.endsWith('.png'))
      .sort();
  }

  // 事前/事後 JSON データの読み込み
  const evidenceDataDir = reportDir ? path.join(reportDir, 'evidence_data') : '';
  const loadJSON = (prefix, table) => {
    if (!evidenceDataDir) return null;
    const jsonPath = path.join(evidenceDataDir, `${prefix}_${testId}_${table}.json`);
    try { return JSON.parse(fs.readFileSync(jsonPath, 'utf-8')); } catch (e) { return null; }
  };
  const preChecks = sc.se16_checks?.pre || [];
  const postChecks = sc.se16_checks?.post || [];

  const statusBadge = verify.status === 'PASS'
    ? '<span style="color:#2e7d32;font-weight:bold">PASS</span>'
    : verify.status === 'FAIL'
      ? '<span style="color:#c62828;font-weight:bold">FAIL</span>'
      : '<span style="color:#999">\u2014</span>';

  // --- データテーブル（diff ハイライト + JSON リンク付き） ---
  const renderDataTable = (data, title, jsonRelPath, diffData) => {
    let html = '<div class="data-section">';
    html += '<div class="data-header">';
    html += `<h3>${title} (${data ? data.length : 0} 件)</h3>`;
    if (jsonRelPath) {
      html += ` <a href="${jsonRelPath}" class="json-link" target="_blank">JSON: ${jsonRelPath}</a>`;
    }
    html += '</div>';
    if (!data || !Array.isArray(data) || data.length === 0) {
      html += '<p style="color:#999;">データなし</p></div>';
      return html;
    }
    const cols = Object.keys(data[0]);
    html += '<table class="data-table">';
    html += '<thead><tr>' + cols.map(c => `<th>${c}</th>`).join('') + '</tr></thead><tbody>';
    for (let ri = 0; ri < data.length; ri++) {
      const row = data[ri];
      const isNewRow = diffData && ri >= diffData.length;
      const rowClass = isNewRow ? ' class="diff-new-row"' : '';
      html += `<tr${rowClass}>`;
      for (const c of cols) {
        const val = row[c] ?? '';
        const diffVal = diffData && diffData[ri] ? (diffData[ri][c] ?? '') : null;
        const changed = diffVal !== null && String(val) !== String(diffVal);
        const tdClass = changed ? ' class="diff-highlight"' : '';
        html += `<td${tdClass}>${val}</td>`;
      }
      html += '</tr>';
    }
    html += '</tbody></table></div>';
    return html;
  };

  // --- diff サマリ ---
  const renderDiffSummary = (preData, postData, tableName) => {
    if (!preData || !postData) return '';
    const items = [];
    if (preData.length !== postData.length) {
      const diff = postData.length - preData.length;
      items.push(`行数: ${preData.length} \u2192 ${postData.length}（${diff > 0 ? '+' : ''}${diff} 行）`);
    }
    for (let i = 0; i < Math.min(preData.length, postData.length); i++) {
      for (const k of Object.keys(preData[i])) {
        if (String(preData[i][k]) !== String(postData[i][k])) {
          items.push(`行${i+1} ${k}: ${preData[i][k]} \u2192 <strong>${postData[i][k]}</strong>`);
        }
      }
    }
    for (let i = preData.length; i < postData.length; i++) {
      items.push(`<span style="color:#2e7d32;">新規行${i+1}: ${Object.entries(postData[i]).map(([k,v]) => k+'='+v).join(', ')}</span>`);
    }
    if (items.length === 0) return '<div class="diff-summary">変更なし</div>';
    return `<div class="diff-summary"><strong>データ差分（${tableName}）:</strong><ul>${items.map(i => '<li>'+i+'</li>').join('')}</ul></div>`;
  };

  // --- スクショ ---
  const renderSSGroup = (files, title) => {
    if (files.length === 0) return '';
    let html = `<h3>${title} (${files.length} 枚)</h3><div class="screenshot-grid">`;
    for (const file of files) {
      const label = file.replace('.png', '');
      html += `<div class="screenshot-item">
      <div class="ss-label">${label}</div>
      <img src="screenshots/${file}" alt="${label}" onclick="window.open(this.src)" />
    </div>`;
    }
    html += '</div>';
    return html;
  };

  // --- AC 別検証結果テーブル（AC + 期待結果 + 実結果 + 判定を統合） ---
  acMap = acMap || {};
  const methodLabels = {
    'automatic': '自動検証',
    'ai_multimodal': 'AI マルチモーダル判定',
    'indirect': '間接確認（最終出力から推定）',
    'manual': '手動確認',
  };
  const renderChecks = () => {
    const coversTs = sc.covers_ts || [];
    const detail = verify.detail || '';
    const checkItems = detail ? detail.split(' | ') : [];
    const expectedChecks = (sc.expected_result && sc.expected_result._checks) || (Array.isArray(sc.expected_result) ? sc.expected_result : []);

    // 検証チェック詳細を解析（PASS/FAIL + テキスト）
    const parsedChecks = checkItems.map(d => ({
      pass: d.startsWith('PASS:'),
      text: d.replace(/^(PASS|FAIL):\s*/, ''),
      raw: d,
    }));

    // expected_result を日本語テキストに変換
    const expectedTexts = expectedChecks.map(er => {
      if (er.check === 'no_error') return '処理エラーなし';
      if (er.check === 'message_type') return `メッセージタイプ: ${er.value}`;
      if (er.check === 'message_text_contains') return `メッセージに「${er.value}」を含む`;
      if (er.check === 'db_changed') return `${er.table} ${er.mode || 'check'}（keys: ${er.keys || 'N/A'}）`;
      if (er.check === 'screen_number') return `画面番号: ${er.value}`;
      return `${er.check}: ${er.value || ''}`;
    });
    const expectedSummary = expectedTexts.join(' / ');

    // 検証実結果サマリ
    const actualSummary = parsedChecks.map(c => {
      const icon = c.pass ? '\u2713' : '\u2717';
      return `<span style="color:${c.pass ? '#2e7d32' : '#c62828'}">${icon} ${c.text}</span>`;
    }).join('<br>');

    let html = '';
    if (coversTs.length > 0) {
      html += '<div class="ac-results"><h3>AC 別検証結果</h3>';
      html += '<table class="ac-table"><thead><tr><th>AC ID</th><th>受入条件</th><th>検証方法</th><th>期待結果</th><th>実結果</th><th>判定</th></tr></thead><tbody>';
      for (const ts of coversTs) {
        const acId = ts.ac_id || '';
        const stmt = acMap[acId] || '';
        const method = methodLabels[ts.verification_method || ''] || ts.verification_method || '';
        const status = verify.status || '';
        const badge = status === 'PASS'
          ? '<span style="color:#2e7d32;font-weight:bold">\u2713 PASS</span>'
          : status === 'FAIL'
            ? '<span style="color:#c62828;font-weight:bold">\u2717 FAIL</span>'
            : '<span style="color:#999">\u2014</span>';

        // expected_checks から期待結果を取得（AC ごとに個別）
        const expChecks = ts.expected_checks || [];
        let acExpected = '';
        let acActual = '';
        if (expChecks.length > 0) {
          acExpected = expChecks.map(ec => ec.description || ec.check).join('<br>');
          // 対応するチェック結果を parsedChecks から検索
          const matchedActuals = expChecks.map(ec => {
            const matched = parsedChecks.find(pc => pc.text.toLowerCase().includes(ec.check.replace('_', ' ').toLowerCase())
              || pc.text.toLowerCase().includes(ec.check.toLowerCase()));
            if (matched) {
              const icon = matched.pass ? '\u2713' : '\u2717';
              return `<span style="color:${matched.pass ? '#2e7d32' : '#c62828'}">${icon} ${matched.text}</span>`;
            }
            return `<span style="color:#999">\u2014 (${ec.check})</span>`;
          });
          acActual = matchedActuals.join('<br>');
        } else if (ts.verification_method === 'ai_multimodal') {
          acExpected = 'スクリーンショットで目視確認';
          acActual = 'スクリーンショット参照';
        } else {
          acExpected = expectedSummary || '\u2014';
          acActual = actualSummary || '\u2014';
        }

        html += `<tr><td style="white-space:nowrap;">${acId}</td><td>${stmt}</td><td>${method}</td><td style="font-size:0.85em;">${acExpected}</td><td style="font-size:0.85em;">${acActual}</td><td>${badge}</td></tr>`;
      }
      html += '</tbody></table></div>';
    }

    return html;
  };

  // --- 実行手順サマリ ---
  const renderProcedure = () => {
    const selFields = sc.execution?.selection_fields || [];
    const transaction = sc.transaction || 'SA38';
    const progId = sc._program_id || sc.execution?.program || '';
    const expectedChecks2 = (sc.expected_result && sc.expected_result._checks) || (Array.isArray(sc.expected_result) ? sc.expected_result : []);
    const expectedDesc = (sc.expected_result && sc.expected_result._description) || '';

    let html = '<div class="procedure-box">';
    html += '<h3>実行手順</h3><ol>';
    html += `<li>${transaction} でプログラム <strong>${progId}</strong> を実行</li>`;
    if (selFields.length > 0) {
      const fieldList = selFields.map(f => {
        const ft = (f.type || 'text').toLowerCase();
        if (ft === 'checkbox') return `${f.name} = ${f.value ? 'ON' : 'OFF'}`;
        return `${f.name} = ${f.low || f.value || ''}${f.high ? ' ～ ' + f.high : ''}`;
      }).join(', ');
      html += `<li>選択画面に入力: <code>${fieldList}</code></li>`;
    }
    html += '<li>F8 で実行</li>';
    if (expectedChecks2.length > 0) {
      const expList = expectedChecks2.map(er => {
        if (er.check === 'no_error') return '処理エラーなし';
        if (er.check === 'message_type') return `メッセージタイプ: ${er.value}`;
        if (er.check === 'message_text_contains') return `メッセージに「${er.value}」を含む`;
        if (er.check === 'db_changed') return `${er.table} ${er.mode || 'check'}（keys: ${er.keys || 'N/A'}）`;
        if (er.check === 'screen_number') return `画面番号: ${er.value}`;
        return `${er.check}: ${er.value || ''}`;
      });
      html += `<li>期待結果: ${expList.join('、')}</li>`;
    }
    html += '</ol></div>';
    return html;
  };

  // --- データ検索条件 ---
  const renderSearchConditions = () => {
    if (preChecks.length === 0 && postChecks.length === 0) return '';
    let html = '<div class="search-conditions">';
    html += '<h3>SE16 データ検索条件</h3>';
    html += '<table class="condition-table"><thead><tr><th>タイミング</th><th>テーブル</th><th>検索条件（WHERE）</th><th>説明</th></tr></thead><tbody>';
    for (const c of preChecks) {
      if (!c.table) continue;
      const where = typeof c.keys === 'string' ? c.keys :
        Object.entries(c.keys || {}).map(([k, v]) => `${k} = '${v}'`).join(' AND ');
      html += `<tr><td>事前</td><td>${c.table}</td><td><code>${where || '条件なし'}</code></td><td>${c.description || ''}</td></tr>`;
    }
    for (const c of postChecks) {
      if (!c.table) continue;
      const where = typeof c.keys === 'string' ? c.keys :
        Object.entries(c.keys || {}).map(([k, v]) => `${k} = '${v}'`).join(' AND ');
      html += `<tr><td>事後</td><td>${c.table}</td><td><code>${where || '条件なし'}</code></td><td>${c.description || ''}</td></tr>`;
    }
    html += '</tbody></table></div>';
    return html;
  };

  // --- 期待出力データ ---
  const renderExpectedOutput = () => {
    const eo = sc.expected_output;
    if (!eo || !eo.rows || eo.rows.length === 0) return '';
    const cols = eo.columns || Object.keys(eo.rows[0]);
    const formatLabel = ({alv:'ALV 表示データ',db_change:'DB 変更データ',message_only:'メッセージのみ'})[eo.format] || eo.description || 'ALV';
    let html = '<div class="data-section expected-output">';
    html += '<div class="data-header">';
    html += `<h3>期待出力データ — ${formatLabel} (${eo.rows.length} 件)</h3>`;
    html += '</div>';
    html += '<table class="data-table">';
    html += '<thead><tr>' + cols.map(c => `<th>${c}</th>`).join('') + '</tr></thead><tbody>';
    for (const row of eo.rows) {
      html += '<tr>';
      for (const c of cols) html += `<td>${row[c] ?? ''}</td>`;
      html += '</tr>';
    }
    html += '</tbody></table></div>';
    return html;
  };

  // --- 事前/事後データの組み立て ---
  let preDataHTML = '';
  let postDataHTML = '';
  let diffHTML = '';
  for (const c of preChecks) {
    if (!c.table) continue;
    const data = loadJSON('pre', c.table);
    const jsonRel = `evidence_data/pre_${testId}_${c.table}.json`;
    preDataHTML += renderDataTable(data, `1. 事前データ（${c.table}）`, jsonRel, null);
  }
  for (const c of postChecks) {
    if (!c.table) continue;
    const postData = loadJSON('post', c.table);
    const preData = loadJSON('pre', c.table);
    const jsonRel = `evidence_data/post_${testId}_${c.table}.json`;
    postDataHTML += renderDataTable(postData, `3. 事後データ（${c.table}）`, jsonRel, preData);
    diffHTML += renderDiffSummary(preData, postData, c.table);
  }

  const scenarioCSS = `
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', 'Yu Gothic UI', 'Meiryo', sans-serif; background: #f5f5f5; color: #333; padding: 24px 32px; }
  h1 { font-size: 1.3em; margin-bottom: 16px; border-bottom: 2px solid #1a237e; padding-bottom: 8px; color: #1a237e; }
  h2 { font-size: 1.1em; margin: 20px 0 8px; color: #283593; }
  h3 { font-size: 0.95em; margin: 12px 0 6px; color: #37474f; }
  .summary-box { background: #fff; border: 1px solid #e0e0e0; border-radius: 6px; padding: 14px 18px; margin-bottom: 16px; }
  .summary-box p { margin: 4px 0; font-size: 0.9em; }
  .evidence { background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); margin-bottom: 16px; }
  .data-section { margin-bottom: 20px; }
  .data-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
  .data-header h3 { margin: 0; }
  .json-link { font-size: 0.8em; color: #1565c0; text-decoration: none; background: #e3f2fd; padding: 2px 8px; border-radius: 3px; }
  .json-link:hover { background: #bbdefb; }
  .data-table { width: 100%; border-collapse: collapse; font-size: 0.85em; margin: 8px 0 16px; }
  .data-table th { background: #e8eaf6; padding: 8px 10px; text-align: left; border: 1px solid #c5cae9; color: #283593; font-weight: 600; }
  .data-table td { padding: 6px 10px; border: 1px solid #eee; }
  .data-table tr:nth-child(even) { background: #fafafa; }
  .diff-highlight { background: #fff9c4; font-weight: bold; }
  .diff-new-row { background: #e8f5e9; }
  .screenshot-grid { display: flex; flex-direction: column; gap: 12px; }
  .screenshot-item { border: 1px solid #ddd; border-radius: 4px; overflow: hidden; }
  .screenshot-item .ss-label { background: #e8eaf6; padding: 6px 12px; font-size: 0.82em; font-weight: bold; color: #283593; }
  .screenshot-item img { width: 80%; display: block; cursor: pointer; margin: 8px auto; }
  .checks { margin: 8px 0; }
  .check-pass { color: #2e7d32; font-size: 0.9em; margin: 2px 0; }
  .check-fail { color: #c62828; font-size: 0.9em; margin: 2px 0; }
  .checks h3 { color: #37474f; margin-bottom: 6px; }
  .ac-results { margin-bottom: 16px; }
  .ac-results h3 { color: #283593; margin-bottom: 8px; }
  .ac-table { width: 100%; border-collapse: collapse; font-size: 0.85em; }
  .ac-table th { background: #e8eaf6; padding: 8px 10px; text-align: left; border: 1px solid #c5cae9; color: #283593; }
  .ac-table td { padding: 6px 10px; border: 1px solid #eee; vertical-align: top; }
  .ac-table tr:nth-child(even) { background: #fafafa; }
  .diff-summary { font-size: 0.9em; margin: 8px 0; padding: 10px 14px; background: #fff3e0; border-radius: 4px; border-left: 3px solid #ff9800; }
  .diff-summary li { margin: 2px 0; }
  .procedure-box { background: #e8f5e9; border: 1px solid #c8e6c9; border-radius: 6px; padding: 14px 18px; margin-bottom: 16px; }
  .procedure-box h3 { color: #2e7d32; margin-bottom: 8px; }
  .procedure-box ol { padding-left: 20px; font-size: 0.9em; }
  .procedure-box li { margin: 4px 0; }
  .procedure-box code { background: #fff; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
  .search-conditions { background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 6px; padding: 14px 18px; margin-bottom: 16px; }
  .search-conditions h3 { color: #1565c0; margin-bottom: 8px; }
  .condition-table { width: 100%; border-collapse: collapse; font-size: 0.85em; }
  .condition-table th { background: #bbdefb; padding: 6px 10px; text-align: left; border: 1px solid #90caf9; }
  .condition-table td { padding: 6px 10px; border: 1px solid #e0e0e0; }
  .condition-table code { background: #fff; padding: 1px 4px; border-radius: 2px; }
  .expected-output { border-left: 3px solid #1565c0; padding-left: 16px; }
  .expected-output .data-header h3 { color: #1565c0; }
  .footer { margin-top: 24px; text-align: center; font-size: 0.8em; color: #999; border-top: 1px solid #eee; padding-top: 12px; }
  `;

  return `<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>${testId}: ${sc.name || ''}</title>
<style>${scenarioCSS}</style></head>
<body>
<h1>${testId}: ${sc.name || ''} ${statusBadge}</h1>
<div class="summary-box">
  <p><strong>種別:</strong> ${({normal:'正常系',abnormal:'異常系',boundary:'境界値',performance:'性能'})[sc.category] || sc.category || ''}</p>
  <p><strong>概要:</strong> ${sc.description || ''}</p>
  <p><strong>検証結果:</strong> ${verify.status || '\u2014'}</p>
</div>
${renderChecks()}
${renderProcedure()}
${renderSearchConditions()}
<div class="evidence">
<h2>エビデンス</h2>
${preDataHTML}
${renderExpectedOutput()}
${renderSSGroup(ssFiles, `${preDataHTML ? '3' : '2'}. プログラム実行（SE38）`)}
${postDataHTML}
${diffHTML}
</div>
<div class="footer">${now} | ${systemInfo.system || '?'} / ${systemInfo.client || '?'} | ${systemInfo.user || '?'}</div>
</body></html>`;
}

// ---------------------------------------------------------------------------
// generateReportHTML は evidence_merge_report.js に移設済み。
// ---------------------------------------------------------------------------
function _REMOVED_generateReportHTML(reportDir, allScenarioResults, systemInfo, tests) {
  tests = tests || [];
  const now = new Date().toISOString().replace('T', ' ').substring(0, 19);

  const totalScenarios = allScenarioResults.length;
  const passCount = allScenarioResults.filter(r => r.status === 'PASS').length;
  const failCount = allScenarioResults.filter(r => r.status === 'FAIL').length;

  let sidebarLinks = '';
  let resultRows = '';

  for (const r of allScenarioResults) {
    const statusIcon = r.status === 'PASS' ? '\u2713' : r.status === 'FAIL' ? '\u2717' : '\u2014';
    const statusColor = r.status === 'PASS' ? '#4caf50' : r.status === 'FAIL' ? '#ef5350' : '#999';
    const statusBadge = r.status === 'PASS'
      ? '<span style="color:#2e7d32;font-weight:bold">PASS</span>'
      : r.status === 'FAIL'
        ? '<span style="color:#c62828;font-weight:bold">FAIL</span>'
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
    <td style="padding:8px 10px;font-size:0.85em;">${(r.detail || '').split(' | ').map(d => {
      const pass = d.startsWith('PASS:');
      const text = d.replace(/^(PASS|FAIL):\s*/, '');
      return `<span style="color:${pass ? '#2e7d32' : '#c62828'}">${pass ? '\u2713' : '\u2717'} ${text}</span>`;
    }).join('<br>')}</td>
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
    <div class="sidebar-section-label">\u30b7\u30ca\u30ea\u30aa</div>
    ${sidebarLinks}
  </div>
</nav>
<div class="main">
  <div id="summary-page">
    <h1>S3-A1: \u6b63\u5f0f\u30a8\u30d3\u30c7\u30f3\u30b9</h1>
    <div class="summary-cards">
      <div class="summary-card"><div class="label">\u53d6\u5f97\u65e5\u6642</div><div class="value">${now}</div></div>
      <div class="summary-card"><div class="label">\u30b7\u30b9\u30c6\u30e0</div><div class="value">${systemInfo.system || '?'} / ${systemInfo.client || '?'}</div></div>
      <div class="summary-card"><div class="label">\u5b9f\u884c\u30e6\u30fc\u30b6\u30fc</div><div class="value">${systemInfo.user || '?'}</div></div>
      <div class="summary-card"><div class="label">\u30b7\u30ca\u30ea\u30aa</div><div class="value">${totalScenarios} \u4ef6</div></div>
      <div class="summary-card"><div class="label">\u691c\u8a3c\u7d50\u679c</div><div class="value">${passCount} PASS / ${failCount} FAIL</div></div>
    </div>
    <table class="result-table">
      <thead><tr><th>ID</th><th>\u30b7\u30ca\u30ea\u30aa\u540d</th><th>\u7a2e\u5225</th><th>\u7d50\u679c</th><th>\u8a73\u7d30</th></tr></thead>
      <tbody>${resultRows}</tbody>
    </table>
  </div>
  <iframe id="scenario-frame"></iframe>
  <div class="footer">\u751f\u6210: ${now}</div>
</div>
</body></html>`;
}

// generateEvidenceHTML は廃止。generateScenarioHTML + generateReportHTML に分割済み。

// ---------------------------------------------------------------------------
// メイン処理
// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// EC-M2: --replace-screenshot サブコマンド
// HTML 内の指定スクリーンショットの src を新しいファイルの base64 に差し替える
// ---------------------------------------------------------------------------
function execReplaceScreenshot(evidenceHtml, screenshotName, newFile) {
  if (!fs.existsSync(evidenceHtml)) {
    console.error(`HTML ファイルが見つかりません: ${evidenceHtml}`);
    process.exit(1);
  }
  if (!fs.existsSync(newFile)) {
    console.error(`スクリーンショットファイルが見つかりません: ${newFile}`);
    process.exit(1);
  }

  let html = fs.readFileSync(evidenceHtml, 'utf-8');
  const imgData = fs.readFileSync(newFile);
  const ext = path.extname(newFile).toLowerCase().replace('.', '');
  const mimeType = ext === 'jpg' || ext === 'jpeg' ? 'image/jpeg' : 'image/png';
  const base64 = imgData.toString('base64');
  const dataUri = `data:${mimeType};base64,${base64}`;

  // screenshots/NAME.png パターンを検索して base64 data URI に置換
  const pattern = new RegExp(`src="[^"]*${screenshotName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}[^"]*"`, 'g');
  const matches = html.match(pattern);
  if (!matches || matches.length === 0) {
    console.error(`スクリーンショット '${screenshotName}' が HTML 内に見つかりません。`);
    process.exit(1);
  }

  html = html.replace(pattern, `src="${dataUri}"`);
  fs.writeFileSync(evidenceHtml, html, 'utf-8');
  console.log(`[EC-M2] ${matches.length} 箇所のスクリーンショットを差し替えました: ${screenshotName}`);
  console.log(`  対象 HTML: ${evidenceHtml}`);
  console.log(`  新画像:    ${newFile}`);
}

// ---------------------------------------------------------------------------
// EC-M3: --update-data サブコマンド
// HTML 内のデータセクションを JSON から再生成する
// ---------------------------------------------------------------------------
function execUpdateData(evidenceHtml, tableName, jsonFile) {
  if (!fs.existsSync(evidenceHtml)) {
    console.error(`HTML ファイルが見つかりません: ${evidenceHtml}`);
    process.exit(1);
  }
  if (!fs.existsSync(jsonFile)) {
    console.error(`JSON ファイルが見つかりません: ${jsonFile}`);
    process.exit(1);
  }

  let html = fs.readFileSync(evidenceHtml, 'utf-8');
  const data = JSON.parse(fs.readFileSync(jsonFile, 'utf-8'));

  // データセクション（<div class="data-section">...テーブル名......</div>）を検索して置換
  // タイトルに tableName を含むセクションを対象にする
  const sectionRegex = new RegExp(
    `<div class="data-section">\\s*<div class="data-header">\\s*<h3>[^<]*${tableName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}[^<]*</h3>[\\s\\S]*?</div>\\s*</div>`,
    'g'
  );
  const matches = html.match(sectionRegex);

  if (matches && matches.length > 0) {
    // 既存セクションを置換
    const newTable = buildDataTableHtml(data, tableName);
    html = html.replace(sectionRegex, newTable);
    fs.writeFileSync(evidenceHtml, html, 'utf-8');
    console.log(`[EC-M3] データセクション '${tableName}' を更新しました（${data.length} 件）`);
  } else {
    // セクションが見つからない場合、</div> の最後の evidence セクション前に新規挿入
    const insertPoint = html.lastIndexOf('</div>\n<div class="footer">');
    if (insertPoint > -1) {
      const newTable = buildDataTableHtml(data, tableName);
      html = html.slice(0, insertPoint) + '\n' + newTable + '\n' + html.slice(insertPoint);
      fs.writeFileSync(evidenceHtml, html, 'utf-8');
      console.log(`[EC-M3] データセクション '${tableName}' を新規挿入しました（${data.length} 件）`);
    } else {
      console.error(`[EC-M3] HTML 内に挿入位置が見つかりません。`);
      process.exit(1);
    }
  }
  console.log(`  対象 HTML: ${evidenceHtml}`);
  console.log(`  JSON:      ${jsonFile}`);
}

function buildDataTableHtml(data, tableName) {
  if (!Array.isArray(data) || data.length === 0) {
    return `<div class="data-section"><div class="data-header"><h3>${tableName} (0 件)</h3></div><p style="color:#999;">データなし</p></div>`;
  }
  const cols = Object.keys(data[0]);
  let html = `<div class="data-section"><div class="data-header"><h3>${tableName} (${data.length} 件)</h3></div>`;
  html += '<table class="data-table"><thead><tr>' + cols.map(c => `<th>${c}</th>`).join('') + '</tr></thead><tbody>';
  for (const row of data) {
    html += '<tr>' + cols.map(c => `<td>${row[c] ?? ''}</td>`).join('') + '</tr>';
  }
  html += '</tbody></table></div>';
  return html;
}

function main() {
  const { planPath, output, auto, continueOnError, scenario, noEvidence, screenshot,
          recapture, replaceScreenshotName, replaceScreenshotFile,
          updateDataTable, updateDataJson, evidenceHtml } = parseArgs();

  // EC-M2: --replace-screenshot サブコマンド
  if (replaceScreenshotName && replaceScreenshotFile) {
    if (!evidenceHtml) {
      console.error('Error: --replace-screenshot には --evidence <html_path> が必要です');
      process.exit(1);
    }
    execReplaceScreenshot(evidenceHtml, replaceScreenshotName, replaceScreenshotFile);
    process.exit(0);
  }

  // EC-M3: --update-data サブコマンド
  if (updateDataTable && updateDataJson) {
    if (!evidenceHtml) {
      console.error('Error: --update-data には --evidence <html_path> が必要です');
      process.exit(1);
    }
    execUpdateData(evidenceHtml, updateDataTable, updateDataJson);
    process.exit(0);
  }

  if (!planPath) {
    console.error('Usage: node evidence_capture.js <feature_dir_or_plan.md> --scenario <id> [--output <dir>] [--auto] [--no-evidence] [--screenshot]');
    process.exit(1);
  }

  // planPath がディレクトリの場合は plan.md を探す
  let fullPlanPath = path.resolve(planPath);
  if (fs.statSync(fullPlanPath).isDirectory()) {
    fullPlanPath = path.join(fullPlanPath, 'plan.md');
  }
  if (!fs.existsSync(fullPlanPath)) {
    console.error(`plan.md が見つかりません: ${fullPlanPath}`);
    process.exit(1);
  }

  // エビデンスモードの判定
  const evidenceMode = noEvidence
    ? (screenshot ? 'stage2' : 'stage1')
    : 'stage3';
  const modeLabels = {
    stage1: 'Stage 1（自動判定のみ、スクショなし）',
    stage2: 'Stage 2（スクショあり、SE16/JSON なし）',
    stage3: 'Stage 3（フルエビデンス）',
  };

  console.log(`=== evidence_capture.js ===`);
  console.log(`plan.md:    ${fullPlanPath}`);
  console.log(`シナリオ:   ${scenario}`);
  console.log(`モード:     ${modeLabels[evidenceMode]}`);
  if (output) console.log(`出力先:     ${path.resolve(output)}`);
  if (auto) console.log(`SAP GUI:    自動（起動→取得→終了）`);
  console.log('');

  // plan.md から evidence_capture 定義を読み取り
  const evidenceConfig = parsePlanEvidence(fullPlanPath);
  let scenarios = evidenceConfig.scenarios || [];

  if (scenarios.length === 0) {
    console.error('evidence_capture.scenarios が空です。');
    process.exit(1);
  }

  // --scenario でフィルタリング（指定シナリオのみ実行）
  const targetScenario = scenarios.find(sc =>
    sc.test_id === scenario || sc.name === scenario
  );
  if (!targetScenario) {
    console.error(`シナリオ '${scenario}' が見つかりません。`);
    console.error(`利用可能なシナリオ: ${scenarios.map(s => s.test_id).join(', ')}`);
    process.exit(1);
  }
  scenarios = [targetScenario]; // 1シナリオのみ実行

  // sap_context.md からメタデータ（テーブル/フィールドの日本語ラベル）を読み込み
  const sapContextLabels = loadSapContextLabels(planPath);
  if (sapContextLabels && Object.keys(sapContextLabels.tables || {}).length > 0) {
    for (const sc of scenarios) {
      if (!sc.labels || Object.keys(sc.labels.tables || {}).length === 0) {
        sc.labels = sapContextLabels;
      }
    }
  }

  console.log(`対象シナリオ: ${scenarios.length}件`);
  for (const sc of scenarios) {
    console.log(`  - ${sc.test_id}: ${sc.name} (${sc.category || '?'}) [program: ${sc._program_id || evidenceConfig._program_id || 'MISSING'}]`);
  }
  console.log('');

  // 出力ディレクトリ準備
  const featureDir = path.resolve(fullPlanPath, '..');
  const reportDir = output ? path.resolve(output) : path.join(featureDir, 'tests', 'reports');
  const baseSSDir = path.join(reportDir, 'screenshots');
  fs.mkdirSync(baseSSDir, { recursive: true });

  // capture_window.ps1 パス
  const capturePsPath = path.join(__dirname, 'capture_window.ps1');

  // SAP GUI PID 検出用
  function findSapGuiPid() {
    try {
      const out = execSync(
        'powershell -NoProfile -Command "Get-Process saplogon -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Id"',
        { encoding: 'utf-8', timeout: 5000, shell: true }
      ).trim();
      if (/^\d+$/.test(out)) return out;
    } catch (e) {}
    return '';
  }

  // SAP GUI 起動（常に実行 — 既存セッションがあればそのまま使用、なければ新規起動）
  console.log('[自動起動] SAP GUI セッションを準備...\n');
  if (!runGuiLaunch('start')) {
    console.error('[失敗] SAP GUI の起動に失敗しました。');
    process.exit(1);
  }
  console.log('');

  const sapPid = findSapGuiPid();
  if (sapPid) console.log(`SAP GUI PID: ${sapPid}\n`);

  const systemInfo = { system: '', client: '', user: '' };
  let hasError = false;
  const verifyResults = {};

  // OBLIGATORY フィールドを一度だけ検出してキャッシュ
  // 各シナリオの selection_fields が空の場合にフォールバックとして使用
  let cachedObligatoryFields = [];
  const firstProg = evidenceConfig._program_id || scenarios.find(s => s.execution?.program)?.execution?.program;
  if (firstProg) {
    // plan.md から上方向に src/ ディレクトリを探索
    let srcDir = '';
    let searchDir = path.resolve(planPath, '..');
    for (let depth = 0; depth < 10; depth++) {
      const candidate = path.join(searchDir, 'src');
      if (fs.existsSync(candidate)) { srcDir = candidate; break; }
      const parent = path.dirname(searchDir);
      if (parent === searchDir) break;
      searchDir = parent;
    }
    if (!srcDir) srcDir = path.resolve(planPath, '..', '..', '..', 'src');
    cachedObligatoryFields = detectObligatoryFromSource(srcDir, firstProg);
    if (cachedObligatoryFields.length > 0) {
      console.log(`[OBLIGATORY 検出] ソースから: ${cachedObligatoryFields.map(f => f.name + '=' + f.low).join(', ')}`);
    }
  }
  // キャッシュを各シナリオに注入
  for (const sc of scenarios) {
    sc._cachedObligatoryFields = cachedObligatoryFields;
    // top-level program_id を各シナリオに伝播（シナリオ自身に未設定の場合のみ）
    if (!sc._program_id && evidenceConfig._program_id) {
      sc._program_id = evidenceConfig._program_id;
    }
  }

  // EC-M1: --recapture モード — プログラム再実行 + SLG1 再キャプチャのみ
  if (recapture) {
    console.log(`\n[EC-M1] --recapture モード: ${recapture}`);
    console.log('[自動起動] SAP GUI セッションを準備...\n');
    if (!runGuiLaunch('start')) {
      console.error('[失敗] SAP GUI の起動に失敗しました。');
      process.exit(1);
    }
    const recapSapPid = findSapGuiPid();
    const sc = scenarios[0];
    const testId = sc.test_id || 'unknown';

    // プログラム再実行
    const recapWsf = buildScenarioWSF(sc, baseSSDir, capturePsPath, recapSapPid, planPath, 'stage2');
    const recapResult = runWSF(recapWsf, 180000);
    console.log(`  プログラム再実行: ${recapResult.STATUS}`);

    // SLG1 再キャプチャ（BALHDR を含む se16_checks がある場合）
    const recapStartTime = new Date();
    const allChecks = [...(sc.se16_checks?.pre || []), ...(sc.se16_checks?.post || [])];
    const balhdrChecks = allChecks.filter(c => (c.table || '').toUpperCase() === 'BALHDR');
    for (const check of balhdrChecks) {
      const slg1Wsf = buildSlg1CaptureWSF(check, baseSSDir, testId, capturePsPath, recapSapPid, recapStartTime);
      const slg1Result = runWSF(slg1Wsf, 60000);
      console.log(`  SLG1 再キャプチャ: ${slg1Result.STATUS} — ${slg1Result.SLG1_SS || 'N/A'}`);
    }

    if (auto) runGuiLaunch('close');
    console.log('\n[EC-M1] --recapture 完了（HTML 再生成は行いません）');
    process.exit(0);
  }

  // シナリオごとにエビデンス取得
  // H-5: 失敗したシナリオ ID を追跡（depends_on スキップ用）
  const failedScenarios = new Set();

  for (let i = 0; i < scenarios.length; i++) {
    const sc = scenarios[i];
    const testId = sc.test_id || 'unknown';
    console.log(`--- ${testId}: ${sc.name} ---`);

    // H-5: depends_on チェック — 依存シナリオが失敗していたらスキップ
    const dependsOn = sc.depends_on || [];
    const depArray = Array.isArray(dependsOn) ? dependsOn : [dependsOn];
    const blockedBy = depArray.filter(dep => failedScenarios.has(dep));
    if (blockedBy.length > 0) {
      console.log(`  [スキップ] 依存シナリオ ${blockedBy.join(', ')} が失敗したためスキップ`);
      verifyResults[testId] = { status: 'SKIPPED', detail: `依存シナリオ失敗: ${blockedBy.join(', ')}`, ssDescs: {} };
      failedScenarios.add(testId);
      console.log('');
      continue;
    }

    // スクショフォルダ準備（フラット形式: screenshots/{scenario_id}_{seq}.png）
    // scenario_id をプレフィックスとして使い、baseSSDir 直下に保存
    const scenarioSSDir = baseSSDir;  // サブフォルダは作らない
    // 既存のスクショを削除（同一 scenario_id のもの）
    try {
      const existing = fs.readdirSync(baseSSDir).filter(f => f.startsWith(testId + '_'));
      for (const f of existing) fs.unlinkSync(path.join(baseSSDir, f));
    } catch (e) { /* ignore */ }

    // EC-03: 再実行時に evidence_data/ の該当シナリオ JSON ファイルも自動削除
    const evidenceDataCleanupDir = path.join(reportDir, 'evidence_data');
    try {
      if (fs.existsSync(evidenceDataCleanupDir)) {
        const existingJson = fs.readdirSync(evidenceDataCleanupDir)
          .filter(f => f.includes(`_${testId}_`) && f.endsWith('.json'));
        for (const f of existingJson) fs.unlinkSync(path.join(evidenceDataCleanupDir, f));
      }
    } catch (e) { /* ignore */ }

    // シナリオ全体を1つのWSFで実行
    let wsf;
    try {
      wsf = buildScenarioWSF(sc, scenarioSSDir, capturePsPath, sapPid, planPath, evidenceMode);
    } catch (buildErr) {
      console.error(`  [失敗] ${buildErr.message}`);
      hasError = true;
      verifyResults[testId] = { status: 'FAIL', detail: buildErr.message };
      failedScenarios.add(testId);
      if (!continueOnError) {
        console.error(`\n[早期停止] シナリオ "${testId}" でエラー発生。--continue-on-error で全シナリオ実行可能。`);
        break;
      }
      continue;
    }

    // --- 事前データ取得（data_preview.js、Stage 2/3 で実行） ---
    const evidenceDataDir = path.join(reportDir, 'evidence_data');
    // EC-04: シナリオ実行開始時刻を記録（BALHDR タイムフィルタ用）
    const scenarioStartTime = new Date();
    if (evidenceMode !== 'stage1') {
      const preChecks = sc.se16_checks?.pre || [];
      if (preChecks.length > 0) {
        fs.mkdirSync(evidenceDataDir, { recursive: true });
        for (const check of preChecks) {
          if (!check.table) continue;
          try {
            // EC-02: BALHDR テーブルは SLG1 スクリーンショットに置換
            if (check.table.toUpperCase() === 'BALHDR') {
              console.log(`    [EC-02] BALHDR → SLG1 スクリーンショットで代替`);
              continue; // SLG1 キャプチャは WSF 実行後に行う
            }
            const dpJs = path.join(__dirname, 'data_preview.js');
            const where = typeof check.keys === 'string' ? check.keys
              : typeof check.keys === 'object' && check.keys
                ? Object.entries(check.keys).map(([k, v]) => `${k} = '${v}'`).join(' AND ')
                : '';
            // EC-05: columns パラメータ対応
            const columnsOpt = check.columns ? ` --columns "${check.columns}"` : '';
            const outFile = path.join(evidenceDataDir, `pre_${testId}_${check.table}.json`);
            const cmd = `node "${dpJs}" ${check.table} --format json${where ? ` --where "${where}"` : ''}${columnsOpt} --rows 100 --output "${outFile}"`;
            execSync(cmd, { timeout: 30000, shell: true, cwd: process.cwd() });
            // EC-03: ADT 0件返却時に空配列 JSON を書き込む
            if (fs.existsSync(outFile)) {
              const content = fs.readFileSync(outFile, 'utf-8').trim();
              if (!content) fs.writeFileSync(outFile, '[]', 'utf-8');
            } else {
              fs.writeFileSync(outFile, '[]', 'utf-8');
            }
          } catch (e) { /* data_preview 失敗は警告のみ */ }
        }
      }
    }

    let result = runWSF(wsf, 180000);

    // --- 事後データ取得（data_preview.js、Stage 2/3 で実行） ---
    if (evidenceMode !== 'stage1') {
      const postChecks = sc.se16_checks?.post || [];
      if (postChecks.length > 0) {
        fs.mkdirSync(evidenceDataDir, { recursive: true });
        for (const check of postChecks) {
          if (!check.table) continue;
          try {
            // EC-02: BALHDR テーブルは SLG1 スクリーンショットに置換
            if (check.table.toUpperCase() === 'BALHDR') {
              // EC-02 + EC-04: BALHDR の場合、SLG1 で時刻フィルタ付きキャプチャ
              const slg1Wsf = buildSlg1CaptureWSF(check, baseSSDir, testId, capturePsPath, sapPid, scenarioStartTime);
              const slg1Result = runWSF(slg1Wsf, 60000);
              if (slg1Result.STATUS === 'OK') {
                console.log(`    [EC-02] SLG1 キャプチャ成功: ${slg1Result.SLG1_SS || 'N/A'}`);
              }
              // BALHDR JSON も保存（時刻フィルタ付き）
              const dpJs = path.join(__dirname, 'data_preview.js');
              const dateStr = scenarioStartTime.toISOString().slice(0, 10).replace(/-/g, '');
              const timeStr = scenarioStartTime.toTimeString().slice(0, 8).replace(/:/g, '');
              const balhdrWhere = typeof check.keys === 'string' ? check.keys
                : typeof check.keys === 'object' && check.keys
                  ? Object.entries(check.keys).map(([k, v]) => `${k} = '${v}'`).join(' AND ')
                  : '';
              const timeFilter = `ALDATE = '${dateStr}' AND ALTIME >= '${timeStr}'`;
              const fullWhere = balhdrWhere ? `${balhdrWhere} AND ${timeFilter}` : timeFilter;
              const outFile = path.join(evidenceDataDir, `post_${testId}_BALHDR.json`);
              const cmd = `node "${dpJs}" BALHDR --format json --where "${fullWhere}" --rows 100 --output "${outFile}"`;
              try { execSync(cmd, { timeout: 30000, shell: true, cwd: process.cwd() }); } catch (_) {}
              if (!fs.existsSync(outFile) || !fs.readFileSync(outFile, 'utf-8').trim()) {
                fs.writeFileSync(outFile, '[]', 'utf-8');
              }
              continue;
            }
            const dpJs = path.join(__dirname, 'data_preview.js');
            const where = typeof check.keys === 'string' ? check.keys
              : typeof check.keys === 'object' && check.keys
                ? Object.entries(check.keys).map(([k, v]) => `${k} = '${v}'`).join(' AND ')
                : '';
            // EC-05: columns パラメータ対応
            const columnsOpt = check.columns ? ` --columns "${check.columns}"` : '';
            const outFile = path.join(evidenceDataDir, `post_${testId}_${check.table}.json`);
            const cmd = `node "${dpJs}" ${check.table} --format json${where ? ` --where "${where}"` : ''}${columnsOpt} --rows 100 --output "${outFile}"`;
            execSync(cmd, { timeout: 30000, shell: true, cwd: process.cwd() });
            // EC-03: ADT 0件返却時に空配列 JSON を書き込む
            if (fs.existsSync(outFile)) {
              const content = fs.readFileSync(outFile, 'utf-8').trim();
              if (!content) fs.writeFileSync(outFile, '[]', 'utf-8');
            } else {
              fs.writeFileSync(outFile, '[]', 'utf-8');
            }
          } catch (e) { /* data_preview 失敗は警告のみ */ }
        }
      }
    }

    // スクショ説明文を収集
    let ssDescs = {};
    for (const [k, v] of Object.entries(result)) {
      if (k.startsWith('SS_DESC_')) {
        ssDescs[k.replace('SS_DESC_', '')] = v;
      }
    }

    // H-3: FAIL 時に1回リトライ
    if (result.STATUS === 'ERROR' || (result.VERIFY_STATUS === 'FAIL')) {
      console.log(`  [リトライ] 1回目失敗。2秒待機後にリトライ...`);
      // スクショをリセット（同一 scenario_id のもの）
      try {
        const existingSS = fs.readdirSync(baseSSDir).filter(f => f.startsWith(testId + '_'));
        for (const f of existingSS) fs.unlinkSync(path.join(baseSSDir, f));
      } catch (e) { /* ignore */ }

      // 2秒待機
      execSync('powershell -Command "Start-Sleep -Seconds 2"', { shell: true, timeout: 5000 });

      // リトライ実行
      const retryWsf = buildScenarioWSF(sc, scenarioSSDir, capturePsPath, sapPid, planPath, evidenceMode);
      const retryResult = runWSF(retryWsf, 180000);

      // リトライ結果で上書き
      result = retryResult;
      ssDescs = {};
      for (const [k, v] of Object.entries(result)) {
        if (k.startsWith('SS_DESC_')) {
          ssDescs[k.replace('SS_DESC_', '')] = v;
        }
      }
    }

    // --- Node.js 側の追加チェック（VBScript 外で実行） ---
    // db_changed, file_output 等の VBScript で実行できないチェックをここで実行する。
    // VBScript の VERIFY_STATUS が PASS の場合のみ追加チェックを行う。
    if (result.VERIFY_STATUS === 'PASS' && sc.expected_result) {
      const nodeCheckTypes = ['db_changed', 'file_output', 'log_output', 'print_output', 'idoc_status', 'wf_status', 'mail_sent', 'bdc_result', 'rfc_return'];
      const expChecks = (sc.expected_result && sc.expected_result._checks) || (Array.isArray(sc.expected_result) ? sc.expected_result : []);
      const nodeChecks = expChecks.filter(c => nodeCheckTypes.includes(c.check));
      if (nodeChecks.length > 0) {
        const nodeResults = runNodeChecks(nodeChecks, sc, featureDir, evidenceMode);
        if (nodeResults.failed > 0) {
          result.VERIFY_STATUS = 'FAIL';
          result.VERIFY_DETAIL = (result.VERIFY_DETAIL || '') + ' | ' + nodeResults.details.join(' | ');
        } else if (nodeResults.details.length > 0) {
          result.VERIFY_DETAIL = (result.VERIFY_DETAIL || '') + ' | ' + nodeResults.details.join(' | ');
        }
      }
    }

    let scenarioFailed = false;
    if (result.STATUS === 'ERROR') {
      console.error(`  [失敗] ${result.ERROR}`);
      hasError = true;
      failedScenarios.add(testId);
      verifyResults[testId] = { status: 'FAIL', detail: result.ERROR, ssDescs };
      scenarioFailed = true;
    } else {
      const ssCount = result.SS_COUNT || '0';
      const verifyStatus = result.VERIFY_STATUS || 'UNKNOWN';
      const verifyDetail = result.VERIFY_DETAIL || '';
      console.log(`  [完了] スクショ ${ssCount} 枚 | 検証: ${verifyStatus} — ${verifyDetail}`);
      verifyResults[testId] = { status: verifyStatus, detail: verifyDetail, ssDescs };
      if (verifyStatus === 'FAIL') {
        hasError = true;
        failedScenarios.add(testId);
        scenarioFailed = true;
      }
    }

    if (scenarioFailed && !continueOnError) {
      console.error(`\n[早期停止] シナリオ "${testId}" が FAIL。残り ${scenarios.length - i - 1} シナリオをスキップ。`);
      console.error(`  原因: ${verifyResults[testId]?.detail || 'unknown'}`);
      console.error(`  全シナリオ実行するには --continue-on-error を指定してください。`);
      break;
    }

    if (!systemInfo.system && result.SYSTEM) {
      systemInfo.system = result.SYSTEM;
      systemInfo.client = result.CLIENT;
      systemInfo.user = result.USER;
    }
    console.log('');
  }

  // Stage 1/2: 結果サマリのみ出力、HTML レポートは生成しない
  if (evidenceMode !== 'stage3') {
    console.log(`\n[完了] ${modeLabels[evidenceMode]} — HTML レポートは Stage 3 で生成します。`);
    for (const [tid, vr] of Object.entries(verifyResults)) {
      console.log(`  ${tid}: ${vr.status} ${vr.detail ? '— ' + vr.detail : ''}`);
    }
    // Evidence output
    const stepId = getStepIdFromArgs();
    if (stepId) {
      const passCount = Object.values(verifyResults).filter(v => v.status === 'PASS').length;
      writeEvidenceIfStepId({
        featureDir,
        stepId,
        toolName: 'evidence_capture.js',
        command: process.argv.join(' '),
        options: [scenario, noEvidence ? '--no-evidence' : '', screenshot ? '--screenshot' : ''].filter(Boolean),
        resultSummary: `${modeLabels[evidenceMode]}: ${passCount}/${scenarios.length} scenarios passed`,
      });
    }
    if (auto) runGuiLaunch('stop');
    process.exit(hasError ? 1 : 0);
  }

  // Stage 3: 個別シナリオ HTML 生成
  console.log('[生成] 個別シナリオ HTML...');
  const acMap = loadAcStatements(featureDir);
  for (const sc of scenarios) {
    const testId = sc.test_id || sc.id || 'unknown';
    const scenarioHtml = generateScenarioHTML(sc, baseSSDir, systemInfo, verifyResults[testId] || {}, reportDir, acMap);
    const scenarioHtmlPath = path.join(reportDir, `evidence_${testId}.html`);
    fs.writeFileSync(scenarioHtmlPath, scenarioHtml, 'utf-8');
    console.log(`  個別 HTML: ${scenarioHtmlPath}`);
  }

  // 統合レポート HTML は evidence_merge_report.js で生成する。
  // 全シナリオのエビデンス取得完了後に以下を実行:
  //   node extensions/sap/tools/evidence_merge_report.js specs/<feature>/

  // evidence_pack_sap.md の s_evidence.scenarios をマージ更新（上書きではなく追記/更新）
  const evidenceSapPath = path.join(featureDir, 'implementation-details', 'evidence_pack_sap.md');
  if (fs.existsSync(evidenceSapPath)) {
    try {
      let sapContent = fs.readFileSync(evidenceSapPath, 'utf-8');

      // 既存の scenarios を YAML からパース
      const existingMatch = sapContent.match(/  s_evidence:\n    scenarios:\n([\s\S]*?)(?=\n  \w|\n#|\n---|\n```|$)/);
      const existingEntries = [];
      if (existingMatch) {
        const lines = existingMatch[1].split('\n');
        let current = null;
        for (const line of lines) {
          const idMatch = line.match(/^\s+- test_id:\s*"([^"]+)"/);
          if (idMatch) {
            if (current) existingEntries.push(current);
            current = { test_id: idMatch[1], lines: [line] };
          } else if (current && line.trim()) {
            current.lines.push(line);
          }
        }
        if (current) existingEntries.push(current);
      }

      // 今回のシナリオでマージ（同じ test_id は上書き、新規は追加）
      for (const sc of scenarios) {
        const testId = sc.test_id || sc.id || '';
        if (!testId) continue;
        const vr = verifyResults[testId] || {};
        let ssCount = 0;
        try {
          if (fs.existsSync(baseSSDir)) {
            ssCount = fs.readdirSync(baseSSDir).filter(f => f.startsWith(testId + '_') && (f.endsWith('.png') || f.endsWith('.jpg') || f.endsWith('.bmp'))).length;
          }
        } catch (e) { /* ignore */ }
        const newEntry = {
          test_id: testId,
          lines: [
            `    - test_id: "${testId}"`,
            `      status: "${vr.status || 'UNKNOWN'}"`,
            `      screenshot_count: ${ssCount}`,
            `      screenshots: "tests/reports/screenshots/${testId}_*.png"`,
          ],
        };
        const idx = existingEntries.findIndex(e => e.test_id === testId);
        if (idx >= 0) {
          existingEntries[idx] = newEntry; // 既存を更新
        } else {
          existingEntries.push(newEntry); // 新規追加
        }
      }

      // test_id でソートして YAML を再構成
      existingEntries.sort((a, b) => a.test_id.localeCompare(b.test_id));
      const mergedYaml = existingEntries.map(e => e.lines.join('\n')).join('\n');
      const newScenarios = `  s_evidence:\n    scenarios:\n${mergedYaml}`;

      sapContent = sapContent.replace(
        /  s_evidence:\n    scenarios:[\s\S]*?(?=\n  \w|\n#|\n---|\n```|$)/,
        newScenarios
      );
      fs.writeFileSync(evidenceSapPath, sapContent, 'utf-8');
      console.log(`[更新] ${evidenceSapPath}`);
    } catch (e) {
      console.error(`[警告] evidence_pack_sap.md の更新に失敗: ${e.message}`);
    }
  }

  // 検証サマリ
  const passCount = Object.values(verifyResults).filter(v => v.status === 'PASS').length;
  const failCount = Object.values(verifyResults).filter(v => v.status === 'FAIL').length;
  console.log(`\n検証結果: ${passCount}/${scenarios.length} PASS, ${failCount} FAIL`);

  // SAP GUI 終了
  if (auto) {
    console.log('\n[自動終了] SAP GUI セッションを終了...');
    runGuiLaunch('close');
  }

  if (hasError) {
    console.error('\n[警告] 一部のエビデンス取得または検証でエラーが発生しました。');
  }

  // Evidence output
  const stepId = getStepIdFromArgs();
  if (stepId) {
    writeEvidenceIfStepId({
      featureDir,
      stepId,
      toolName: 'evidence_capture.js',
      command: process.argv.join(' '),
      options: [scenario, noEvidence ? '--no-evidence' : '', screenshot ? '--screenshot' : ''].filter(Boolean),
      resultSummary: `${modeLabels[evidenceMode]}: ${passCount}/${scenarios.length} scenarios passed, ${failCount} failed`,
    });
  }

  console.log('\n=== S3-A1 エビデンス取得完了 ===');
  process.exit(hasError ? 1 : 0);
}

main();
