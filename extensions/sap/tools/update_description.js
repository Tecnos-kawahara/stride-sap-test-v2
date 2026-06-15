#!/usr/bin/env node
/**
 * update_description.js — SAP オブジェクトの内容説明テキストを GUI スクリプティングで更新
 *
 * ADT REST API ではオブジェクトの description（内容説明テキスト）を作成後に
 * 変更する手段がないため、SAP GUI スクリプティング（COM API）経由で更新する。
 *
 * 仕組み:
 *   1. オブジェクト種別に応じた WSF スクリプトを動的生成
 *   2. gui_launch.js で SAP GUI セッションを確保
 *   3. cscript で WSF を実行し、対象トランザクションで description を更新
 *
 * Usage:
 *   node extensions/sap/tools/update_description.js --type <type> --name <name> --description <text>
 *
 * Types:
 *   function_module  → SE37 で内容説明を更新
 *   function_group   → SE80 で内容説明を更新
 *   program          → SE38 で内容説明を更新（タイトル）
 *   class            → SE24 で内容説明を更新
 *
 * Examples:
 *   node extensions/sap/tools/update_description.js --type function_module --name Z_MY_FM --description "新しい説明"
 *   node extensions/sap/tools/update_description.js --type program --name ZREPORT --description "新しいタイトル"
 *
 * Prerequisites:
 *   - SAP GUI がインストールされ、スクリプティングが有効であること
 *   - SAP GUI セッションが起動済みであること（gui_launch.js で起動）
 */

'use strict';

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// --- Load .env ---
const envPath = path.resolve(__dirname, '../../../.env');
if (fs.existsSync(envPath)) {
  const lines = fs.readFileSync(envPath, 'utf-8').split(/\r?\n/);
  for (const line of lines) {
    const m = line.match(/^\s*([^#=][^=]*?)\s*=\s*(.*?)\s*$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2];
  }
}

// --- Helpers ---

function decodeShiftJIS(buf) {
  try { return new TextDecoder('shift_jis').decode(buf); }
  catch (_) { return buf.toString('utf-8'); }
}

function runWSF(wsfContent, timeoutMs) {
  const tmpFile = path.join(os.tmpdir(), `sap_updesc_${process.pid}_${Date.now()}.wsf`);
  try {
    fs.writeFileSync(tmpFile, wsfContent, 'utf-8');
    const buf = execSync(`cscript //NoLogo "${tmpFile}"`, { timeout: timeoutMs || 30000, shell: true });
    const output = decodeShiftJIS(buf);
    const kv = {};
    for (const line of output.split(/\r?\n/)) {
      const idx = line.indexOf('=');
      if (idx > 0) kv[line.substring(0, idx).trim()] = line.substring(idx + 1).trim();
    }
    return kv;
  } catch (e) {
    if (e.stdout) {
      const output = decodeShiftJIS(e.stdout);
      const kv = {};
      for (const line of output.split(/\r?\n/)) {
        const idx = line.indexOf('=');
        if (idx > 0) kv[line.substring(0, idx).trim()] = line.substring(idx + 1).trim();
      }
      if (Object.keys(kv).length > 0) return kv;
    }
    return { STATUS: 'ERROR', ERROR: e.message };
  } finally {
    try { fs.unlinkSync(tmpFile); } catch (_) {}
  }
}

function escapeJSString(s) {
  return s.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
}

// --- WSF generators per object type ---

function generateSE37WSF(fmName, description) {
  const name = escapeJSString(fmName);
  const desc = escapeJSString(description);
  return `<?xml version="1.0" encoding="UTF-8"?>
<job><script language="JScript"><![CDATA[
function out(k,v){WScript.Echo(k+"="+v)}
function sleep(ms){WScript.Sleep(ms)}

try {
  var app = GetObject("SAPGUI").GetScriptingEngine;
  var ses = app.Children(0).Children(0);

  // セッション状態診断
  out("DIAG_SYSTEM", "" + ses.Info.SystemName);
  out("DIAG_SCREEN", "" + ses.Info.ScreenNumber);

  // SE37 を開く
  ses.findById("wnd[0]/tbar[0]/okcd").text = "/nSE37";
  ses.findById("wnd[0]").sendVKey(0);
  sleep(500);

  // 汎用モジュール名を入力
  ses.findById("wnd[0]/usr/ctxtRS38L-NAME").text = "${name}";
  // 変更ボタン
  ses.findById("wnd[0]/tbar[1]/btn[7]").press();
  sleep(500);

  // 内容説明テキスト（Kurztext）フィールドを更新
  // S/4HANA: モーダルダイアログ（wnd[1]）の可能性を先に試行
  var useModal = false;
  try {
    var dlg = ses.findById("wnd[1]");
    if (dlg) {
      // S/4HANA モーダルパターン
      try { ses.findById("wnd[1]/usr/txtRS38L-FTITLE").text = "${desc}"; useModal = true; } catch(m1) {
        try { ses.findById("wnd[1]/usr/txtRSFBPARA-STEXT").text = "${desc}"; useModal = true; } catch(m2) {}
      }
    }
  } catch(dlgErr) {}

  if (!useModal) {
    // ECC: メインウィンドウで直接編集
    try {
      ses.findById("wnd[0]/usr/txtRS38L-FTITLE").text = "${desc}";
    } catch(e1) {
      try {
        ses.findById("wnd[0]/usr/txtRSFBPARA-STEXT").text = "${desc}";
      } catch(e2) {
        out("STATUS", "FIELD_NOT_FOUND");
        out("ERROR", "Could not find description field: " + e1.message + " / " + e2.message);
        WScript.Quit(1);
      }
    }
  }

  if (useModal) {
    // S/4HANA: モーダルダイアログの OK ボタン
    ses.findById("wnd[1]/tbar[0]/btn[0]").press();
    sleep(300);
  }

  // 保存
  ses.findById("wnd[0]/tbar[0]/btn[11]").press();
  sleep(500);

  // 戻る
  ses.findById("wnd[0]/tbar[0]/btn[3]").press();
  sleep(300);

  out("STATUS", "OK");
  out("OBJECT", "${name}");
  out("DESCRIPTION", "${desc}");
  out("MODE", useModal ? "S4HANA_MODAL" : "ECC_DIRECT");

} catch(e) {
  out("STATUS", "ERROR");
  out("ERROR", e.message || String(e));
  try {
    var tmpDir = new ActiveXObject("Scripting.FileSystemObject").GetSpecialFolder(2).Path;
    ses.findById("wnd[0]").HardCopy(tmpDir + "\\\\update_desc_fail_${name}.png", "PNG");
    out("FAIL_SS", tmpDir + "\\\\update_desc_fail_${name}.png");
  } catch(ss) {}
  WScript.Quit(1);
}
]]></script></job>`;
}

function generateSE38WSF(progName, description) {
  const name = escapeJSString(progName);
  const desc = escapeJSString(description);
  return `<?xml version="1.0" encoding="UTF-8"?>
<job><script language="JScript"><![CDATA[
function out(k,v){WScript.Echo(k+"="+v)}
function sleep(ms){WScript.Sleep(ms)}

try {
  var app = GetObject("SAPGUI").GetScriptingEngine;
  var ses = app.Children(0).Children(0);

  // セッション状態診断
  out("DIAG_SYSTEM", "" + ses.Info.SystemName);
  out("DIAG_SCREEN", "" + ses.Info.ScreenNumber);

  // SE38 を開く
  ses.findById("wnd[0]/tbar[0]/okcd").text = "/nSE38";
  ses.findById("wnd[0]").sendVKey(0);
  sleep(500);

  // プログラム名を入力
  ses.findById("wnd[0]/usr/ctxtRS38M-PROGRAMM").text = "${name}";

  // S/4HANA 確定パッチ: 属性ラジオボタン → FUNC_HEAD（31プログラム検証済み）
  // 旧: radRS38M-ATTR（S/4HANA で存在しない）→ 新: radRS38M-FUNC_HEAD
  try {
    ses.findById("wnd[0]/usr/radRS38M-FUNC_HEAD").select();
  } catch(rf) {
    // ECC フォールバック: radRS38M-ATTR
    try { ses.findById("wnd[0]/usr/radRS38M-ATTR").select(); } catch(ra) {}
  }

  // S/4HANA 確定パッチ: 変更ボタン → btnCHAP
  // 旧: tbar[1]/btn[7]（実行ボタン誤用）→ 新: btnCHAP
  try {
    ses.findById("wnd[0]/usr/btnCHAP").press();
  } catch(bc) {
    // ECC フォールバック
    ses.findById("wnd[0]/tbar[1]/btn[7]").press();
  }
  sleep(500);

  // S/4HANA: 属性編集がモーダルダイアログ（wnd[1]）で開く
  var useModal = false;
  try {
    ses.findById("wnd[1]/usr/txtRS38M-REPTI").text = "${desc}";
    useModal = true;
  } catch(m) {
    // ECC フォールバック: メインウィンドウ（wnd[0]）
    ses.findById("wnd[0]/usr/txtRS38M-REPTI").text = "${desc}";
  }

  if (useModal) {
    // S/4HANA: モーダルダイアログの OK ボタン
    ses.findById("wnd[1]/tbar[0]/btn[0]").press();
    sleep(300);
  }

  // 保存
  ses.findById("wnd[0]/tbar[0]/btn[11]").press();
  sleep(500);

  // 戻る
  ses.findById("wnd[0]/tbar[0]/btn[3]").press();
  sleep(300);

  out("STATUS", "OK");
  out("OBJECT", "${name}");
  out("DESCRIPTION", "${desc}");
  out("MODE", useModal ? "S4HANA_MODAL" : "ECC_DIRECT");

} catch(e) {
  out("STATUS", "ERROR");
  out("ERROR", e.message || String(e));
  // 失敗時スクリーンショット取得（リモートデバッグ用）
  try {
    var tmpDir = new ActiveXObject("Scripting.FileSystemObject").GetSpecialFolder(2).Path;
    ses.findById("wnd[0]").HardCopy(tmpDir + "\\\\update_desc_fail_${name}.png", "PNG");
    out("FAIL_SS", tmpDir + "\\\\update_desc_fail_${name}.png");
  } catch(ss) {}
  WScript.Quit(1);
}
]]></script></job>`;
}

function generateSE24WSF(className, description) {
  const name = escapeJSString(className);
  const desc = escapeJSString(description);
  return `<?xml version="1.0" encoding="UTF-8"?>
<job><script language="JScript"><![CDATA[
function out(k,v){WScript.Echo(k+"="+v)}
function sleep(ms){WScript.Sleep(ms)}

try {
  var app = GetObject("SAPGUI").GetScriptingEngine;
  var ses = app.Children(0).Children(0);

  // セッション状態診断
  out("DIAG_SYSTEM", "" + ses.Info.SystemName);
  out("DIAG_SCREEN", "" + ses.Info.ScreenNumber);

  // SE24 を開く
  ses.findById("wnd[0]/tbar[0]/okcd").text = "/nSE24";
  ses.findById("wnd[0]").sendVKey(0);
  sleep(500);

  // クラス名を入力
  ses.findById("wnd[0]/usr/ctxtSEOC-CLSNAME").text = "${name}";
  // 変更ボタン
  ses.findById("wnd[0]/tbar[1]/btn[7]").press();
  sleep(500);

  // 内容説明フィールド — S/4HANA モーダル対応
  var useModal = false;
  try {
    var dlg = ses.findById("wnd[1]");
    if (dlg) {
      try { ses.findById("wnd[1]/usr/txtSEOC-DESCRIPT").text = "${desc}"; useModal = true; } catch(m) {}
    }
  } catch(dlgErr) {}

  if (!useModal) {
    // ECC: メインウィンドウで直接編集
    ses.findById("wnd[0]/usr/txtSEOC-DESCRIPT").text = "${desc}";
  }

  if (useModal) {
    ses.findById("wnd[1]/tbar[0]/btn[0]").press();
    sleep(300);
  }

  // 保存
  ses.findById("wnd[0]/tbar[0]/btn[11]").press();
  sleep(500);

  // 戻る
  ses.findById("wnd[0]/tbar[0]/btn[3]").press();
  sleep(300);

  out("STATUS", "OK");
  out("OBJECT", "${name}");
  out("DESCRIPTION", "${desc}");
  out("MODE", useModal ? "S4HANA_MODAL" : "ECC_DIRECT");

} catch(e) {
  out("STATUS", "ERROR");
  out("ERROR", e.message || String(e));
  try {
    var tmpDir = new ActiveXObject("Scripting.FileSystemObject").GetSpecialFolder(2).Path;
    ses.findById("wnd[0]").HardCopy(tmpDir + "\\\\update_desc_fail_${name}.png", "PNG");
    out("FAIL_SS", tmpDir + "\\\\update_desc_fail_${name}.png");
  } catch(ss) {}
  WScript.Quit(1);
}
]]></script></job>`;
}

// --- Supported types ---
const TYPE_MAP = {
  function_module: { label: '汎用モジュール', transaction: 'SE37', generate: generateSE37WSF },
  program:         { label: 'プログラム',     transaction: 'SE38', generate: generateSE38WSF },
  class:           { label: 'クラス',         transaction: 'SE24', generate: generateSE24WSF },
};

// --- Args ---
function parseArgs() {
  const args = process.argv.slice(2);
  let type = null, name = null, description = null;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--type' && args[i + 1]) { type = args[++i]; }
    else if (args[i] === '--name' && args[i + 1]) { name = args[++i].toUpperCase(); }
    else if (args[i] === '--description' && args[i + 1]) { description = args[++i]; }
  }

  if (!type || !name || !description) {
    console.log(`Usage:
  node extensions/sap/tools/update_description.js --type <type> --name <name> --description <text>

Types: ${Object.keys(TYPE_MAP).join(', ')}

Examples:
  node extensions/sap/tools/update_description.js --type function_module --name Z_MY_FM --description "新しい説明"
  node extensions/sap/tools/update_description.js --type program --name ZREPORT --description "新しいタイトル"
  node extensions/sap/tools/update_description.js --type class --name ZCL_MY_CLASS --description "新しい説明"`);
    process.exit(1);
  }

  if (!TYPE_MAP[type]) {
    console.error(`Error: Unsupported type "${type}". Use: ${Object.keys(TYPE_MAP).join(', ')}`);
    process.exit(1);
  }

  return { type, name, description };
}

// --- Main ---
function main() {
  const { type, name, description } = parseArgs();
  const config = TYPE_MAP[type];

  console.log(`Updating description via ${config.transaction} (GUI Scripting)`);
  console.log(`  Type:        ${config.label} (${type})`);
  console.log(`  Object:      ${name}`);
  console.log(`  Description: ${description}`);
  console.log('');

  // SAP GUI セッション確認
  console.log('Checking SAP GUI session...');
  try {
    execSync(`node "${path.join(__dirname, 'gui_launch.js')}"`, { stdio: 'inherit', timeout: 60000 });
  } catch (e) {
    console.error('Error: SAP GUI session could not be established.');
    console.error('Run gui_launch.js first or check SAP GUI installation.');
    process.exit(1);
  }

  // WSF 生成 + 実行
  console.log(`\nExecuting ${config.transaction} script...`);
  const wsf = config.generate(name, description);
  const result = runWSF(wsf, 30000);

  if (result.STATUS === 'OK') {
    console.log(`\nDone. Description updated successfully.`);
    console.log(`  Object:      ${result.OBJECT}`);
    console.log(`  Description: ${result.DESCRIPTION}`);
  } else {
    console.error(`\nError: Failed to update description.`);
    console.error(`  Status: ${result.STATUS}`);
    if (result.ERROR) console.error(`  Detail: ${result.ERROR}`);
    console.error('\nNote: SAP GUI Scripting must be enabled (RZ11: sapgui/user_scripting = TRUE)');
    process.exit(1);
  }
}

main();
