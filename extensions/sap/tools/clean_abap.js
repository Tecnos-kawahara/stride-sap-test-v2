#!/usr/bin/env node
/**
 * clean_abap.js — "S1-C1: ソース自動クリーンアップ"
 *
 * Claude Codeが生成したABAPソースに対して、フォーマット・旧構文の自動修正を行う。
 * ABAP Cleaner CLI相当の処理をNode.jsで実装（Java不要）。
 *
 * SDD自動化サイクル Step S1-C1 に該当。
 * activate.jsの前に実行し、ソースファイルを直接上書きする。
 *
 * Usage:
 *   node clean_abap.js <file_or_dir> [options]
 *
 * Examples:
 *   node clean_abap.js src/zpackage/zcl_example/zcl_example.clas.abap
 *   node clean_abap.js src/ --recursive
 *   node clean_abap.js src/ --recursive --dry-run
 *   node clean_abap.js src/ --recursive --stats
 *
 * Options:
 *   --recursive    ディレクトリ内の.abapファイルを再帰処理
 *   --dry-run      変更せずにプレビューのみ（差分表示）
 *   --stats        修正統計をサマリー表示
 *   --verbose      各ルール適用のログを出力
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { writeEvidenceIfStepId, getStepIdFromArgs } = require('./lib/evidence_writer');

// =========================================================================
// ABAP Keywords（大文字化対象）
// =========================================================================
const ABAP_KEYWORDS = new Set([
  // Declarations
  'DATA', 'TYPES', 'CONSTANTS', 'FIELD-SYMBOLS', 'CLASS-DATA', 'CLASS-METHODS',
  'METHODS', 'INTERFACES', 'ALIASES', 'STATICS', 'TABLES',
  // Types
  'TYPE', 'LIKE', 'REF', 'TO', 'OF', 'STANDARD', 'SORTED', 'HASHED',
  'TABLE', 'RANGE', 'LINE', 'INITIAL', 'SIZE', 'WITH', 'HEADER',
  'DEFAULT', 'VALUE', 'READ-ONLY', 'LENGTH', 'DECIMALS',
  // Control
  'IF', 'ELSE', 'ELSEIF', 'ENDIF', 'CASE', 'WHEN', 'ENDCASE',
  'DO', 'ENDDO', 'WHILE', 'ENDWHILE',
  'LOOP', 'AT', 'ENDLOOP', 'EXIT', 'CONTINUE', 'CHECK', 'RETURN',
  // OO
  'CLASS', 'ENDCLASS', 'METHOD', 'ENDMETHOD', 'INTERFACE', 'ENDINTERFACE',
  'PUBLIC', 'PROTECTED', 'PRIVATE', 'SECTION', 'DEFINITION', 'IMPLEMENTATION',
  'INHERITING', 'FROM', 'CREATE', 'ABSTRACT', 'FINAL', 'FOR', 'TESTING',
  'REDEFINITION', 'RAISING', 'IMPORTING', 'EXPORTING', 'CHANGING', 'RETURNING',
  // SQL
  'SELECT', 'ENDSELECT', 'INSERT', 'UPDATE', 'DELETE', 'MODIFY',
  'INTO', 'CORRESPONDING', 'FIELDS', 'WHERE',
  'AND', 'OR', 'NOT',  // 論理演算子も大文字化（Rule 8 でも処理）
  'ORDER', 'BY', 'GROUP', 'HAVING', 'UP', 'ROWS', 'SINGLE',
  'INNER', 'LEFT', 'RIGHT', 'OUTER', 'JOIN', 'ON', 'AS',
  'APPENDING', 'PACKAGE', 'ALL', 'ENTRIES', 'IN', 'BETWEEN',
  'UNION', 'EXCEPT', 'INTERSECT', 'DISTINCT',
  // Internal table ops
  'APPEND', 'COLLECT', 'READ', 'SORT', 'CLEAR', 'FREE', 'REFRESH',
  'DESCRIBE', 'LINES', 'ASSIGNING', 'REFERENCE', 'TRANSPORTING',
  'BINARY', 'SEARCH', 'INDEX', 'KEY', 'COMPONENTS',
  // Exception handling
  'TRY', 'CATCH', 'CLEANUP', 'ENDTRY', 'RAISE', 'EXCEPTION', 'RESUMABLE',
  'INTO', 'MESSAGE',
  // Transaction
  'COMMIT', 'WORK', 'ROLLBACK', 'WAIT',
  // Form (legacy)
  'FORM', 'ENDFORM', 'PERFORM', 'USING', 'TABLES',
  // Function
  'CALL', 'FUNCTION', 'EXCEPTIONS',
  // Misc
  'WRITE', 'FORMAT', 'NEW-LINE', 'SKIP', 'ULINE',
  'REPORT', 'PROGRAM', 'INCLUDE', 'BEGIN', 'END',
  'MOVE-CORRESPONDING', 'CORRESPONDING',
  'IS', 'BOUND', 'ASSIGNED', 'REQUESTED', 'SUPPLIED',
  // Note: ABAP_TRUE, ABAP_FALSE, SPACE are constants, not keywords.
  // Clean ABAP guidelines recommend lowercase (abap_true, abap_false, space).
  // Excluded to avoid conflict with abaplint keyword_case rule.
  'NEW', 'CAST', 'CONV', 'COND', 'SWITCH', 'FILTER', 'REDUCE',
  'ASSERT', 'AUTHORITY-CHECK', 'OBJECT',
  'CONCATENATE', 'SPLIT', 'REPLACE', 'TRANSLATE', 'CONDENSE', 'SHIFT',
  'FIND', 'REGEX', 'MATCH', 'COUNT', 'OFFSET', 'RESULTS',
  'ASSIGN', 'UNASSIGN', 'GET', 'SET',
  'ENQUEUE', 'DEQUEUE',
  'SELECTION-SCREEN', 'PARAMETERS', 'SELECT-OPTIONS',
  'INITIALIZATION', 'START-OF-SELECTION', 'END-OF-SELECTION',
  'AT', 'SELECTION-SCREEN', 'TOP-OF-PAGE', 'END-OF-PAGE',
  'NO', 'CHANGING',
]);

// =========================================================================
// Cleanup Rules
// =========================================================================

const rules = {
  /**
   * Rule 1: キーワード大文字化
   * data lv_test → DATA lv_test
   */
  keywordUpperCase(line, stats) {
    // 文字列リテラル・コメントの中は変換しない
    if (line.trimStart().startsWith('*') || line.trimStart().startsWith('"')) return line;

    let result = '';
    let inString = false;
    let stringDelim = '';
    let i = 0;

    while (i < line.length) {
      // 文字列リテラル検出
      if (!inString && (line[i] === "'" || line[i] === '`')) {
        inString = true;
        stringDelim = line[i];
        result += line[i];
        i++;
        continue;
      }
      if (inString && line[i] === stringDelim) {
        // エスケープチェック（'' → 1つの'）
        if (line[i] === "'" && line[i + 1] === "'") {
          result += "''";
          i += 2;
          continue;
        }
        inString = false;
        result += line[i];
        i++;
        continue;
      }
      if (inString) {
        result += line[i];
        i++;
        continue;
      }

      // 行コメント（"以降）
      if (line[i] === '"') {
        result += line.substring(i);
        break;
      }

      // ワード境界でキーワード判定
      if (/[a-zA-Z_-]/.test(line[i])) {
        let word = '';
        const start = i;
        while (i < line.length && /[a-zA-Z0-9_-]/.test(line[i])) {
          word += line[i];
          i++;
        }
        if (ABAP_KEYWORDS.has(word.toUpperCase()) && word !== word.toUpperCase()) {
          result += word.toUpperCase();
          if (stats) stats.keywordUpperCase = (stats.keywordUpperCase || 0) + 1;
        } else {
          result += word;
        }
        continue;
      }

      result += line[i];
      i++;
    }

    return result;
  },

  /**
   * Rule 2: MOVE x TO y → y = x
   */
  moveToEquals(line, stats) {
    const trimmed = line.trimStart();
    if (trimmed.startsWith('*') || trimmed.startsWith('"')) return line;

    const match = trimmed.match(/^MOVE\s+(.+?)\s+TO\s+(\S+)\s*\.$/i);
    if (match) {
      const indent = line.substring(0, line.length - trimmed.length);
      if (stats) stats.moveToEquals = (stats.moveToEquals || 0) + 1;
      return `${indent}${match[2]} = ${match[1]}.`;
    }
    return line;
  },

  /**
   * Rule 3: ADD x TO y → y += x (同様にSUBTRACT, MULTIPLY, DIVIDE)
   */
  arithmeticOperator(line, stats) {
    const trimmed = line.trimStart();
    if (trimmed.startsWith('*') || trimmed.startsWith('"')) return line;
    const indent = line.substring(0, line.length - trimmed.length);

    const patterns = [
      { re: /^ADD\s+(.+?)\s+TO\s+(\S+)\s*\.$/i,         op: '+=' },
      { re: /^SUBTRACT\s+(.+?)\s+FROM\s+(\S+)\s*\.$/i,   op: '-=' },
      { re: /^MULTIPLY\s+(\S+)\s+BY\s+(.+?)\s*\.$/i,     op: '*=', swap: true },
      { re: /^DIVIDE\s+(\S+)\s+BY\s+(.+?)\s*\.$/i,       op: '/=', swap: true },
    ];

    for (const p of patterns) {
      const m = trimmed.match(p.re);
      if (m) {
        if (stats) stats.arithmeticOperator = (stats.arithmeticOperator || 0) + 1;
        if (p.swap) {
          return `${indent}${m[1]} ${p.op} ${m[2]}.`;
        }
        return `${indent}${m[2]} ${p.op} ${m[1]}.`;
      }
    }
    return line;
  },

  /**
   * Rule 4: COMPUTE y = expr → y = expr
   */
  removeCompute(line, stats) {
    const trimmed = line.trimStart();
    if (trimmed.startsWith('*') || trimmed.startsWith('"')) return line;

    const match = trimmed.match(/^COMPUTE\s+(.+)$/i);
    if (match) {
      const indent = line.substring(0, line.length - trimmed.length);
      if (stats) stats.removeCompute = (stats.removeCompute || 0) + 1;
      return `${indent}${match[1]}`;
    }
    return line;
  },

  /**
   * Rule 5: 末尾空白除去
   */
  trailingWhitespace(line, stats) {
    const trimmed = line.replace(/\s+$/, '');
    if (trimmed !== line) {
      if (stats) stats.trailingWhitespace = (stats.trailingWhitespace || 0) + 1;
    }
    return trimmed;
  },

  /**
   * Rule 6: 連続空行の正規化（3行以上 → 2行）
   * ※行単位ではなくファイル単位で処理
   */
  normalizeEmptyLines(lines, stats) {
    const result = [];
    let consecutiveEmpty = 0;
    for (const line of lines) {
      if (line.trim() === '') {
        consecutiveEmpty++;
        if (consecutiveEmpty <= 2) {
          result.push(line);
        } else {
          if (stats) stats.normalizeEmptyLines = (stats.normalizeEmptyLines || 0) + 1;
        }
      } else {
        consecutiveEmpty = 0;
        result.push(line);
      }
    }
    return result;
  },

  /**
   * Rule 7: 旧比較演算子 → 新演算子
   * EQ → =, NE → <>, GT → >, LT → <, GE → >=, LE → <=
   */
  comparisonOperator(line, stats) {
    const trimmed = line.trimStart();
    if (trimmed.startsWith('*') || trimmed.startsWith('"')) return line;

    // 文字列リテラルの外側部分のみを置換する
    // 行を「コード部分」と「文字列部分」に分割して処理
    const replacements = [
      { old: /\bEQ\b/gi,  rep: '=' },
      { old: /\bNE\b/gi,  rep: '<>' },
      { old: /\bGT\b/gi,  rep: '>' },
      { old: /\bLT\b/gi,  rep: '<' },
      { old: /\bGE\b/gi,  rep: '>=' },
      { old: /\bLE\b/gi,  rep: '<=' },
    ];

    // 文字列リテラルとコード部分を分離
    const segments = [];
    let inString = false;
    let stringDelim = '';
    let current = '';
    for (let i = 0; i < line.length; i++) {
      if (!inString && (line[i] === "'" || line[i] === '`')) {
        segments.push({ text: current, isCode: true });
        current = line[i];
        inString = true;
        stringDelim = line[i];
        continue;
      }
      if (inString && line[i] === stringDelim) {
        if (line[i] === "'" && line[i + 1] === "'") {
          current += "''";
          i++;
          continue;
        }
        current += line[i];
        segments.push({ text: current, isCode: false });
        current = '';
        inString = false;
        continue;
      }
      // 行中コメント（" 以降）— 文字列外の場合
      if (!inString && line[i] === '"') {
        segments.push({ text: current, isCode: true });
        segments.push({ text: line.substring(i), isCode: false });
        current = '';
        break;
      }
      current += line[i];
    }
    if (current) segments.push({ text: current, isCode: !inString });

    // コード部分のみ置換
    let changed = false;
    for (const seg of segments) {
      if (!seg.isCode) continue;
      for (const r of replacements) {
        const before = seg.text;
        seg.text = seg.text.replace(r.old, r.rep);
        if (before !== seg.text) changed = true;
      }
    }

    if (changed && stats) {
      stats.comparisonOperator = (stats.comparisonOperator || 0) + 1;
    }

    return segments.map(s => s.text).join('');
  },

  /**
   * Rule 8: 論理演算子大文字化
   * and → AND, or → OR, not → NOT
   * ※文字列・コメント内は変換しない
   * ※abaplint keyword_case ルールとの整合性を維持
   */
  logicalOperatorLowerCase(line, stats) {
    const trimmed = line.trimStart();
    if (trimmed.startsWith('*') || trimmed.startsWith('"')) return line;

    // 文字列リテラルとコード部分を分離（Rule 7と同じロジック）
    const segments = [];
    let inString = false;
    let stringDelim = '';
    let current = '';
    for (let i = 0; i < line.length; i++) {
      if (!inString && (line[i] === "'" || line[i] === '`')) {
        segments.push({ text: current, isCode: true });
        current = line[i];
        inString = true;
        stringDelim = line[i];
        continue;
      }
      if (inString && line[i] === stringDelim) {
        if (line[i] === "'" && line[i + 1] === "'") {
          current += "''";
          i++;
          continue;
        }
        current += line[i];
        segments.push({ text: current, isCode: false });
        current = '';
        inString = false;
        continue;
      }
      if (!inString && line[i] === '"') {
        segments.push({ text: current, isCode: true });
        segments.push({ text: line.substring(i), isCode: false });
        current = '';
        break;
      }
      current += line[i];
    }
    if (current) segments.push({ text: current, isCode: !inString });

    let changed = false;
    const replacements = [
      { old: /\band\b/g,  rep: 'AND' },
      { old: /\bor\b/g,   rep: 'OR' },
      { old: /\bnot\b/g,  rep: 'NOT' },
    ];
    for (const seg of segments) {
      if (!seg.isCode) continue;
      for (const r of replacements) {
        const before = seg.text;
        seg.text = seg.text.replace(r.old, r.rep);
        if (before !== seg.text) changed = true;
      }
    }

    if (changed && stats) {
      stats.logicalOperatorLowerCase = (stats.logicalOperatorLowerCase || 0) + 1;
    }
    return segments.map(s => s.text).join('');
  },

  /**
   * Rule 9: CALL METHOD → 機能的呼出し [B1]
   * CALL METHOD obj->method.           → obj->method( ).
   * CALL METHOD cl_class=>method.      → cl_class=>method( ).
   * ※パラメータ付き(EXPORTING等)は複数行にまたがるため対象外
   */
  callMethodFunctional(line, stats) {
    const trimmed = line.trimStart();
    if (trimmed.startsWith('*') || trimmed.startsWith('"')) return line;

    // パターン: CALL METHOD <target>. （引数なし、1行完結）
    const match = trimmed.match(/^CALL\s+METHOD\s+([\w~\->=:]+(?:\(.*?\))?)\s*\.$/i);
    if (match) {
      const indent = line.substring(0, line.length - trimmed.length);
      if (stats) stats.callMethodFunctional = (stats.callMethodFunctional || 0) + 1;
      return `${indent}${match[1]}( ).`;
    }
    return line;
  },

  /**
   * Rule 10: CREATE OBJECT → NEW [B1]
   * CREATE OBJECT lo_obj TYPE zcl_class.  → lo_obj = NEW zcl_class( ).
   * CREATE OBJECT lo_obj.                 → lo_obj = NEW #( ).
   * ※EXPORTING付きは複数行にまたがるため対象外
   */
  createObjectNew(line, stats) {
    const trimmed = line.trimStart();
    if (trimmed.startsWith('*') || trimmed.startsWith('"')) return line;
    const indent = line.substring(0, line.length - trimmed.length);

    // パターン1: CREATE OBJECT lo TYPE zcl_class.
    const matchTyped = trimmed.match(/^CREATE\s+OBJECT\s+(\S+)\s+TYPE\s+(\S+)\s*\.$/i);
    if (matchTyped) {
      if (stats) stats.createObjectNew = (stats.createObjectNew || 0) + 1;
      return `${indent}${matchTyped[1]} = NEW ${matchTyped[2]}( ).`;
    }

    // パターン2: CREATE OBJECT lo. （型推論）
    const matchUntyped = trimmed.match(/^CREATE\s+OBJECT\s+(\S+)\s*\.$/i);
    if (matchUntyped) {
      if (stats) stats.createObjectNew = (stats.createObjectNew || 0) + 1;
      return `${indent}${matchUntyped[1]} = NEW #( ).`;
    }

    return line;
  },

  /**
   * Rule 11: TRANSLATE → to_upper/to_lower 組込み関数 [B1 7.40+]
   * TRANSLATE lv_str TO UPPER CASE. → lv_str = to_upper( lv_str ).
   * TRANSLATE lv_str TO LOWER CASE. → lv_str = to_lower( lv_str ).
   */
  translateToBuiltin(line, stats) {
    const trimmed = line.trimStart();
    if (trimmed.startsWith('*') || trimmed.startsWith('"')) return line;
    const indent = line.substring(0, line.length - trimmed.length);

    const match = trimmed.match(/^TRANSLATE\s+(\S+)\s+TO\s+(UPPER|LOWER)\s+CASE\s*\.$/i);
    if (match) {
      const varName = match[1];
      const func = match[2].toUpperCase() === 'UPPER' ? 'to_upper' : 'to_lower';
      if (stats) stats.translateToBuiltin = (stats.translateToBuiltin || 0) + 1;
      return `${indent}${varName} = ${func}( ${varName} ).`;
    }
    return line;
  },

  /**
   * Rule 12: REFRESH → CLEAR（ヘッダ付き内部テーブル禁止に伴う廃止命令）
   * REFRESH itab. → CLEAR itab.
   * ヘッダ付き内部テーブルが使用禁止のため、REFRESH は不要。
   * CLEAR で内部テーブルの内容がクリアされる。
   */
  refreshToClear(line, stats) {
    const trimmed = line.trimStart();
    if (trimmed.startsWith('*') || trimmed.startsWith('"')) return line;
    const indent = line.substring(0, line.length - trimmed.length);

    const match = trimmed.match(/^REFRESH\s+(\S+)\s*\.$/i);
    if (match) {
      if (stats) stats.refreshToClear = (stats.refreshToClear || 0) + 1;
      return `${indent}CLEAR ${match[1]}.`;
    }
    return line;
  },
};

// =========================================================================
// File Processing
// =========================================================================

function cleanSource(source, stats) {
  let lines = source.split(/\r?\n/);

  // 行単位ルール適用
  // 順序重要: 構文変換 → キーワード大文字化 → 演算子変換 → フォーマット
  lines = lines.map(line => {
    // Phase 1: 旧構文 → 新構文（構文レベルの変換）
    line = rules.moveToEquals(line, stats);          // Rule 2: MOVE → =
    line = rules.arithmeticOperator(line, stats);    // Rule 3: ADD/SUB → +=/-=
    line = rules.removeCompute(line, stats);         // Rule 4: COMPUTE除去
    line = rules.callMethodFunctional(line, stats);  // Rule 9: CALL METHOD → func()
    line = rules.createObjectNew(line, stats);       // Rule 10: CREATE OBJECT → NEW
    line = rules.translateToBuiltin(line, stats);    // Rule 11: TRANSLATE → to_upper/lower
    line = rules.refreshToClear(line, stats);        // Rule 12: REFRESH → CLEAR
    // Phase 2: キーワード正規化
    line = rules.keywordUpperCase(line, stats);      // Rule 1: キーワード大文字化
    // Phase 3: 演算子・論理演算子（大文字化の後に実行）
    line = rules.comparisonOperator(line, stats);    // Rule 7: EQ/NE/GT → =/</>/
    line = rules.logicalOperatorLowerCase(line, stats); // Rule 8: and/or/not → AND/OR/NOT
    // Phase 4: フォーマット
    line = rules.trailingWhitespace(line, stats);    // Rule 5: 末尾空白除去
    return line;
  });

  // ファイル単位ルール適用
  lines = rules.normalizeEmptyLines(lines, stats);

  return lines.join('\n');
}

function collectFiles(target, recursive) {
  const files = [];
  const stat = fs.statSync(target);

  if (stat.isFile()) {
    if (target.endsWith('.abap')) {
      files.push(target);
    }
  } else if (stat.isDirectory()) {
    const entries = fs.readdirSync(target, { withFileTypes: true });
    for (const entry of entries) {
      const full = path.join(target, entry.name);
      if (entry.isFile() && entry.name.endsWith('.abap')) {
        files.push(full);
      } else if (entry.isDirectory() && recursive) {
        files.push(...collectFiles(full, true));
      }
    }
  }

  return files;
}

// =========================================================================
// CLI
// =========================================================================

function parseArgs(argv) {
  const args = argv.slice(2);
  if (args.length < 1 || args.includes('--help')) {
    console.log(`clean_abap.js — S1-C1: ABAP ソース自動クリーンアップ

Usage:
  node clean_abap.js <file_or_dir> [options]

Options:
  --recursive    ディレクトリ再帰処理
  --dry-run      変更せずプレビューのみ
  --stats        修正統計サマリー
  --verbose      詳細ログ

Examples:
  node clean_abap.js src/zcl_example.clas.abap
  node clean_abap.js src/ --recursive --stats`);
    process.exit(args.includes('--help') ? 0 : 1);
  }

  return {
    target: args[0],
    recursive: args.includes('--recursive'),
    dryRun: args.includes('--dry-run'),
    showStats: args.includes('--stats'),
    verbose: args.includes('--verbose'),
  };
}

function main() {
  const opts = parseArgs(process.argv);
  const files = collectFiles(opts.target, opts.recursive);

  if (files.length === 0) {
    console.error('No .abap files found.');
    process.exit(1);
  }

  console.log(`clean_abap.js — S1-C1: ABAP Source Cleanup`);
  console.log(`Files: ${files.length}`);
  console.log('');

  const totalStats = {};
  let modifiedCount = 0;

  for (const filePath of files) {
    const original = fs.readFileSync(filePath, 'utf-8');
    const fileStats = {};
    const cleaned = cleanSource(original, fileStats);

    const changed = cleaned !== original;

    if (changed) {
      modifiedCount++;

      if (opts.verbose) {
        console.log(`  MODIFIED: ${filePath}`);
        for (const [rule, count] of Object.entries(fileStats)) {
          console.log(`    ${rule}: ${count} fix(es)`);
        }
      }

      if (!opts.dryRun) {
        fs.writeFileSync(filePath, cleaned, 'utf-8');
      } else {
        console.log(`  [dry-run] Would modify: ${filePath}`);
      }
    }

    // 統計集計
    for (const [rule, count] of Object.entries(fileStats)) {
      totalStats[rule] = (totalStats[rule] || 0) + count;
    }
  }

  // サマリー
  const totalFixes = Object.values(totalStats).reduce((a, b) => a + b, 0);
  console.log('');
  console.log(`Result: ${modifiedCount}/${files.length} files modified, ${totalFixes} fixes applied.`);

  if (opts.showStats && totalFixes > 0) {
    console.log('');
    console.log('Fix Summary:');
    console.log('  Rule                     Fixes');
    console.log('  ─────────────────────────────────');
    for (const [rule, count] of Object.entries(totalStats).sort((a, b) => b[1] - a[1])) {
      console.log(`  ${rule.padEnd(25)} ${count}`);
    }
  }

  if (opts.dryRun) {
    console.log('\n(dry-run mode — no files were modified)');
  }

  // Evidence output
  const stepId = getStepIdFromArgs();
  if (stepId) {
    // Derive feature-dir from --feature-dir arg or try to infer from src/ path
    const fdIdx = process.argv.indexOf('--feature-dir');
    let featureDir = (fdIdx !== -1 && process.argv[fdIdx + 1]) ? process.argv[fdIdx + 1] : null;
    if (!featureDir && files.length > 0) {
      // Try to infer: if target is under specs/<feature>/src/, walk up
      const absTarget = path.resolve(opts.target);
      const specsIdx = absTarget.indexOf(path.sep + 'specs' + path.sep);
      if (specsIdx !== -1) {
        const afterSpecs = absTarget.substring(specsIdx + 6); // after '/specs/'
        const featureName = afterSpecs.split(path.sep)[0];
        if (featureName) {
          featureDir = absTarget.substring(0, specsIdx) + path.sep + 'specs' + path.sep + featureName;
        }
      }
    }
    if (featureDir) {
      writeEvidenceIfStepId({
        featureDir,
        stepId,
        toolName: 'clean_abap.js',
        command: process.argv.join(' '),
        options: [opts.target, opts.recursive ? '--recursive' : '', opts.dryRun ? '--dry-run' : ''].filter(Boolean),
        resultSummary: `${modifiedCount}/${files.length} files modified, ${totalFixes} fixes applied`,
      });
    } else {
      console.error('Warning: --step-id specified but --feature-dir not provided and could not be inferred. Skipping evidence output.');
    }
  }
}

main();
