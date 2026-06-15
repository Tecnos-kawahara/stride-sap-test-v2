/**
 * evidence_writer.js — ツール実行エビデンスファイルの書き出しヘルパー (Node.js)
 *
 * 各 SAP 拡張 Node.js ツールが正常終了時に呼び出し、
 * specs/<feature>/.tool_evidence/ にエビデンスファイルを出力する。
 */

const fs = require('fs');
const path = require('path');

const EVIDENCE_DIR_NAME = '.tool_evidence';

/**
 * ファイル名に使えない文字を置換する
 */
function sanitizeStepId(stepId) {
  return stepId.replace(/[<>:"/\\|?*]/g, '_');
}

/**
 * エビデンスファイル名を生成する
 * 命名規則: {step_id}__{tool_basename}.evidence.yaml
 */
function evidenceFilename(stepId, toolName) {
  const toolBasename = path.basename(toolName, path.extname(toolName));
  const safeStep = sanitizeStepId(stepId);
  return `${safeStep}__${toolBasename}.evidence.yaml`;
}

/**
 * エビデンスファイルを出力する
 *
 * @param {Object} opts
 * @param {string} opts.featureDir - specs/<feature>/ のパス
 * @param {string} opts.stepId - ワークフローステップ ID
 * @param {string} opts.toolName - ツールのスクリプト名
 * @param {string} opts.command - 実行コマンド文字列
 * @param {string[]} [opts.options] - コマンドオプション
 * @param {number} [opts.exitCode=0] - 終了コード
 * @param {string} [opts.resultSummary=''] - 結果要約
 * @param {Array<{path: string, action: string}>} [opts.outputs] - 出力ファイル
 * @param {number} [opts.durationMs] - 実行時間(ms)
 * @param {Object} [opts.extraData] - 追加の構造化データ（例: { checked_tables: ["T001"] }）
 * @returns {string} エビデンスファイルのパス
 */
function writeEvidence(opts) {
  const {
    featureDir,
    stepId,
    toolName,
    command,
    options = [],
    exitCode = 0,
    resultSummary = '',
    outputs = null,
    durationMs = null,
    extraData = null,
  } = opts;

  const evidenceDir = path.join(featureDir, EVIDENCE_DIR_NAME);
  if (!fs.existsSync(evidenceDir)) {
    fs.mkdirSync(evidenceDir, { recursive: true });
  }

  const filename = evidenceFilename(stepId, toolName);
  const filepath = path.join(evidenceDir, filename);

  const data = {
    schema_version: '1.0',
    step_id: stepId,
    tool: toolName,
    command: command,
    options: options,
    timestamp: new Date().toISOString(),
    exit_code: exitCode,
    result_summary: resultSummary,
  };
  if (durationMs !== null) {
    data.duration_ms = durationMs;
  }
  if (outputs) {
    data.outputs = outputs;
  }

  // 簡易 YAML 出力（yaml パッケージ不要）
  const lines = [
    'tool_evidence:',
    `  schema_version: "${data.schema_version}"`,
    `  step_id: "${data.step_id}"`,
    `  tool: "${data.tool}"`,
    `  command: "${data.command.replace(/"/g, '\\"')}"`,
    `  options: [${data.options.map(o => `"${o}"`).join(', ')}]`,
    `  timestamp: "${data.timestamp}"`,
    `  exit_code: ${data.exit_code}`,
    `  result_summary: "${data.result_summary.replace(/"/g, '\\"')}"`,
  ];
  if (data.duration_ms !== undefined) {
    lines.push(`  duration_ms: ${data.duration_ms}`);
  }
  if (data.outputs) {
    lines.push('  outputs:');
    data.outputs.forEach(o => {
      lines.push(`    - path: "${o.path}"`);
      lines.push(`      action: "${o.action}"`);
    });
  }
  if (extraData) {
    for (const [key, val] of Object.entries(extraData)) {
      if (Array.isArray(val)) {
        lines.push(`  ${key}: [${val.map(v => `"${v}"`).join(', ')}]`);
      } else {
        lines.push(`  ${key}: "${val}"`);
      }
    }
  }

  fs.writeFileSync(filepath, lines.join('\n') + '\n', 'utf8');
  return filepath;
}

/**
 * process.argv から --step-id を取得する
 * @returns {string|null} step-id の値、未指定時は null
 */
function getStepIdFromArgs() {
  const idx = process.argv.indexOf('--step-id');
  if (idx !== -1 && idx + 1 < process.argv.length) {
    return process.argv[idx + 1];
  }
  return null;
}

/**
 * --step-id が指定されている場合のみエビデンスを出力する
 */
function writeEvidenceIfStepId(opts) {
  const stepId = getStepIdFromArgs();
  if (!stepId) return null;
  return writeEvidence({ ...opts, stepId });
}

module.exports = {
  writeEvidence,
  writeEvidenceIfStepId,
  getStepIdFromArgs,
  evidenceFilename,
  EVIDENCE_DIR_NAME,
};
