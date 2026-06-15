#!/usr/bin/env node
/**
 * gui_launch.js — SAP GUI 自動起動・ログイン・セッション待機
 *
 * COM API (GetObject("SAPGUI")) を使って SAP GUI (DIAG) セッションを起動し、
 * ログイン完了を待機する。既に接続済みの場合はスキップ。
 *
 * Usage:
 *   node extensions/sap/tools/gui_launch.js [--close]
 *
 * Options:
 *   --close   既存の SAP GUI セッションを閉じる（テスト後のクリーンアップ用）
 *
 * Environment (.env):
 *   SAP_URL            — SAP system URL (サーバーIPを抽出)
 *   SAP_USERNAME       — SAP user
 *   SAP_PASSWORD       — SAP password
 *   SAP_GUI_INSTANCE   — DIAG instance number (default: 00)
 *   SAP_GUI_CLIENT     — SAP client for GUI (default: SAP_CLIENT)
 *   SAP_GUI_LANGUAGE   — Login language (default: JA)
 *   SAP_GUI_SYSTEM     — SAPlogon entry name (auto-detect if omitted)
 *
 * Exit codes:
 *   0 — session is ready (or closed successfully)
 *   1 — failed to establish session
 */

'use strict';

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// --- Load .env ---
function loadEnv() {
  const envPath = path.resolve(process.cwd(), '.env');
  if (!fs.existsSync(envPath)) return;
  const lines = fs.readFileSync(envPath, 'utf-8').split(/\r?\n/);
  for (const line of lines) {
    const m = line.match(/^\s*([^#=][^=]*?)\s*=\s*(.*?)\s*$/);
    if (m && !process.env[m[1]]) {
      process.env[m[1]] = m[2];
    }
  }
}

// --- Shift_JIS decode ---
function decodeShiftJIS(buf) {
  try {
    return new TextDecoder('shift_jis').decode(buf);
  } catch (e) {
    return buf.toString('utf-8');
  }
}

// --- Run a WSF script and return key=value pairs ---
function runWSF(wsfContent, timeoutMs) {
  const tmpFile = path.join(os.tmpdir(), `sap_gui_${process.pid}_${Date.now()}.wsf`);
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
    // Try to parse stdout even on error
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

// --- Check if SAP GUI session is already active ---
function checkExistingSession() {
  const wsf = `<?xml version="1.0" encoding="UTF-8"?>
<job><script language="JScript"><![CDATA[
function out(k,v){WScript.Echo(k+"="+v)}
try {
  var g=GetObject("SAPGUI");
  var a=g.GetScriptingEngine;
  if(!a){out("STATUS","NO_ENGINE");WScript.Quit(0)}
  if(a.Children.Count==0){out("STATUS","NO_CONN");WScript.Quit(0)}
  var c=a.Children(0);
  if(c.Children.Count==0){out("STATUS","NO_SESSION");WScript.Quit(0)}
  var s=c.Children(0);
  out("STATUS","CONNECTED");
  out("SYSTEM",""+s.Info.SystemName);
  out("CLIENT",""+s.Info.Client);
  out("USER",""+s.Info.User);
  out("SCREEN",""+s.Info.ScreenNumber);
} catch(e) {
  out("STATUS","NOT_RUNNING");
}
WScript.Quit(0);
]]></script></job>`;

  return runWSF(wsf, 10000);
}

// --- Close SAP GUI session ---
function closeSession() {
  const wsf = `<?xml version="1.0" encoding="UTF-8"?>
<job><script language="JScript"><![CDATA[
function out(k,v){WScript.Echo(k+"="+v)}
try {
  var g=GetObject("SAPGUI");
  var a=g.GetScriptingEngine;
  if(!a||a.Children.Count==0){out("CLOSE","NO_SESSION");WScript.Quit(0)}
  var c=a.Children(0);
  if(c.Children.Count>0){
    var s=c.Children(0);
    s.findById("wnd[0]/tbar[0]/okcd").text="/nex";
    s.findById("wnd[0]").sendVKey(0);
    WScript.Sleep(1000);
  }
  out("CLOSE","OK");
} catch(e) {
  out("CLOSE","ERROR");
  out("ERROR",e.message);
}
WScript.Quit(0);
]]></script></job>`;

  const result = runWSF(wsf, 15000);
  return result.CLOSE === 'OK';
}

// --- Extract server IP from SAP_URL ---
function getServerIP() {
  const url = process.env.SAP_URL || '';
  const m = url.match(/\/\/([\d.]+)/);
  return m ? m[1] : null;
}

// --- Find DIAG entry name in SAPlogon config ---
function findSaplogonEntry() {
  if (process.env.SAP_GUI_SYSTEM) return process.env.SAP_GUI_SYSTEM;

  const landscapePath = path.join(
    process.env.APPDATA || '', 'SAP', 'Common', 'SAPUILandscape.xml'
  );

  if (fs.existsSync(landscapePath)) {
    try {
      const xml = fs.readFileSync(landscapePath, 'utf-8');
      const server = getServerIP();
      const instance = process.env.SAP_GUI_INSTANCE || '00';
      const port = `32${instance}`;

      const entries = xml.match(/<Service[^>]*type="SAPGUI"[^>]*\/>/g) || [];
      for (const entry of entries) {
        const nameMatch = entry.match(/name="([^"]*)"/);
        const serverMatch = entry.match(/server="([^"]*)"/);
        if (nameMatch && serverMatch) {
          const srvValue = serverMatch[1];
          if (server && srvValue.includes(server) && srvValue.includes(port)) {
            return nameMatch[1];
          }
        }
      }
    } catch (e) { /* ignore */ }
  }

  return null;
}

// --- Launch SAP GUI via COM API and login ---
function launchAndLogin() {
  const client = process.env.SAP_GUI_CLIENT || process.env.SAP_CLIENT || '200';
  const user = process.env.SAP_USERNAME;
  const password = process.env.SAP_PASSWORD;
  const language = process.env.SAP_GUI_LANGUAGE || 'JA';

  if (!user || !password) {
    console.error('[エラー] SAP_USERNAME / SAP_PASSWORD が .env に設定されていません。');
    return false;
  }

  // SAPlogon に登録済みのエントリ名を検索
  const systemName = findSaplogonEntry();
  const server = getServerIP();
  const instance = process.env.SAP_GUI_INSTANCE || '00';

  // OpenConnection に渡す接続記述子
  const connDesc = systemName || (server ? `/H/${server}/S/32${instance}` : null);

  if (!connDesc) {
    console.error('[エラー] SAP接続先が特定できません。SAP_GUI_SYSTEM を .env に設定してください。');
    return false;
  }

  console.log(`[起動] COM API 経由で接続: "${connDesc}" (クライアント: ${client}, ユーザー: ${user})`);

  // JScript の Unicode エスケープで日本語接続名を安全に渡す
  const connDescEscaped = Array.from(connDesc).map(ch => {
    const code = ch.charCodeAt(0);
    if (code > 127) {
      return '\\u' + code.toString(16).padStart(4, '0');
    }
    return ch;
  }).join('');

  // パスワード内の特殊文字をJScript文字列用にエスケープ
  const passwordEscaped = password.replace(/\\/g, '\\\\').replace(/"/g, '\\"');

  const wsf = `<?xml version="1.0" encoding="UTF-8"?>
<job><script language="JScript"><![CDATA[
function out(k,v){WScript.Echo(k+"="+v)}

var connDesc = "${connDescEscaped}";
var client = "${client}";
var user = "${user}";
var password = "${passwordEscaped}";
var language = "${language}";

try {
  var app;
  try {
    var sapgui = GetObject("SAPGUI");
    app = sapgui.GetScriptingEngine;
  } catch(e) {
    // SAP GUI が起動していない場合、saplogon.exe を起動
    out("STEP", "LAUNCHING_SAPLOGON");
    var wsh = new ActiveXObject("WScript.Shell");
    wsh.Run('"C:\\\\Program Files\\\\SAP\\\\FrontEnd\\\\SAPgui\\\\saplogon.exe"', 1, false);
    WScript.Sleep(5000);

    try {
      var sapgui2 = GetObject("SAPGUI");
      app = sapgui2.GetScriptingEngine;
    } catch(e2) {
      out("STATUS", "SAPLOGON_LAUNCH_FAILED");
      out("ERROR", e2.message);
      WScript.Quit(1);
    }
  }

  if (!app) {
    out("STATUS", "NO_ENGINE");
    WScript.Quit(1);
  }

  out("STEP", "ENGINE_OK");

  // 既存接続があればそのまま使う
  if (app.Children.Count > 0) {
    var existConn = app.Children(0);
    if (existConn.Children.Count > 0) {
      var existSes = existConn.Children(0);
      var existUser = "" + existSes.Info.User;
      if (existUser && existUser.length > 0) {
        out("STATUS", "ALREADY_CONNECTED");
        out("SYSTEM", "" + existSes.Info.SystemName);
        out("CLIENT", "" + existSes.Info.Client);
        out("USER", existUser);
        WScript.Quit(0);
      }
    }
  }

  // 新規接続を開く
  out("STEP", "OPENING_CONNECTION");
  out("CONN_DESC", connDesc);
  var conn = app.OpenConnection(connDesc, true);
  WScript.Sleep(3000);

  if (!conn || conn.Children.Count == 0) {
    out("STATUS", "CONNECTION_FAILED");
    WScript.Quit(1);
  }

  var ses = conn.Children(0);
  var screenNum = "" + ses.Info.ScreenNumber;
  out("STEP", "CONNECTED_SCREEN_" + screenNum);

  // ログイン画面（Screen 20 or 100）でクレデンシャルを入力
  if (screenNum == "20" || screenNum == "100") {
    out("STEP", "LOGGING_IN");
    try { ses.findById("wnd[0]/usr/txtRSYST-MANDT").text = client; } catch(x){}
    try { ses.findById("wnd[0]/usr/txtRSYST-BNAME").text = user; } catch(x){}
    try { ses.findById("wnd[0]/usr/pwdRSYST-BCODE").text = password; } catch(x){}
    try { ses.findById("wnd[0]/usr/txtRSYST-LANGU").text = language; } catch(x){}
    ses.findById("wnd[0]").sendVKey(0);
    WScript.Sleep(3000);

    // 多重ログオンポップアップの処理
    try {
      var popup = ses.findById("wnd[1]");
      if (popup) {
        try { popup.findById("usr/radMULTI_LOGON_OPT1").select(); } catch(x){}
        try { popup.findById("usr/radMULTI_LOGON_OPT2").select(); } catch(x){}
        popup.sendVKey(0);
        WScript.Sleep(2000);
      }
    } catch(x) { /* no popup */ }
  }

  // ログイン結果を出力
  var finalUser = "";
  try { finalUser = "" + ses.Info.User; } catch(x){}
  var finalSystem = "";
  try { finalSystem = "" + ses.Info.SystemName; } catch(x){}
  var finalClient = "";
  try { finalClient = "" + ses.Info.Client; } catch(x){}
  var finalScreen = "";
  try { finalScreen = "" + ses.Info.ScreenNumber; } catch(x){}

  if (finalUser && finalUser.length > 0) {
    out("STATUS", "CONNECTED");
  } else {
    out("STATUS", "LOGIN_FAILED");
  }
  out("SYSTEM", finalSystem);
  out("CLIENT", finalClient);
  out("USER", finalUser);
  out("FINAL_SCREEN", finalScreen);

} catch(e) {
  out("STATUS", "ERROR");
  out("ERROR", e.message);
  WScript.Quit(1);
}

WScript.Quit(0);
]]></script></job>`;

  const result = runWSF(wsf, 60000);

  if (result.STATUS === 'CONNECTED' || result.STATUS === 'ALREADY_CONNECTED') {
    return result;
  }

  console.error(`[エラー] 接続失敗: ${result.STATUS} — ${result.ERROR || ''}`);
  return null;
}

// --- Main ---
function main() {
  loadEnv();

  const args = process.argv.slice(2);
  const doClose = args.includes('--close');

  if (doClose) {
    console.log('=== SAP GUI セッション終了 ===\n');
    const existing = checkExistingSession();
    if (existing.STATUS === 'CONNECTED') {
      console.log(`[接続中] ${existing.SYSTEM} / ${existing.CLIENT} / ${existing.USER}`);
      const closed = closeSession();
      if (closed) {
        console.log('[完了] セッションを終了しました。');
        process.exit(0);
      } else {
        console.error('[エラー] セッション終了に失敗しました。');
        process.exit(1);
      }
    } else {
      console.log('[スキップ] アクティブなセッションがありません。');
      process.exit(0);
    }
  }

  console.log('=== SAP GUI 自動起動 ===\n');

  // Step 1: 既存セッション確認
  console.log('[確認] 既存セッションをチェック...');
  const existing = checkExistingSession();

  if (existing.STATUS === 'CONNECTED') {
    console.log(`[スキップ] 既にログイン済み: ${existing.SYSTEM} / クライアント ${existing.CLIENT} / ユーザー ${existing.USER}`);
    console.log(`[準備完了] セッションは利用可能です。`);
    process.exit(0);
  }

  console.log(`[状態] ${existing.STATUS} — 新規セッションを起動します。`);

  // Step 2: COM API 経由で接続・ログイン
  const session = launchAndLogin();

  if (session) {
    console.log(`[準備完了] ${session.SYSTEM} / クライアント ${session.CLIENT} / ユーザー ${session.USER}`);
    process.exit(0);
  } else {
    console.error('[失敗] SAP GUI セッションを確立できませんでした。');
    process.exit(1);
  }
}

main();
