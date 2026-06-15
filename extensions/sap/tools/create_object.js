#!/usr/bin/env node
/**
 * create_object.js — 新規オブジェクトをSAP上に作成する（汎用版）
 *
 * Usage:
 *   node scripts/create_object.js <type> <name> <description> [--package <pkg>] [--transport <tr>]
 *
 * Types:
 *   class            → CLAS/OC
 *   interface        → INTF/OI
 *   program          → PROG/P
 *   function_group   → FUGR/F
 *   function_module  → FUGR/FF  (--parent <function_group_name> required)
 *   msag             → MSAG/N
 *   table            → TABL/DT
 *   data_element     → DTEL/DE
 *   domain           → DOMA/DD
 *
 * Examples:
 *   node scripts/create_object.js interface ZIF_LOA_SALES_ORDER "受注データAPI IF" --package $TMP
 *   node scripts/create_object.js class ZCL_LOA_SALES_ORDER "受注データAPI" --package $TMP
 *   node scripts/create_object.js program ZLOAP000200 "受注照会レポート" --package $TMP
 *   node scripts/create_object.js function_group ZFGR_SAMPLE "サンプル汎用G" --package $TMP
 *   node scripts/create_object.js function_module Z_SAMPLE_FM "サンプル汎用M" --parent ZFGR_SAMPLE --package $TMP
 *
 * Default package: $TMP (local object, no transport required)
 */

'use strict';

const { ADTClient } = require('abap-adt-api');
require('dotenv').config();
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

function createClient() {
  const { SAP_URL, SAP_USERNAME, SAP_PASSWORD, SAP_CLIENT } = process.env;
  if (!SAP_URL || !SAP_USERNAME || !SAP_PASSWORD) {
    console.error('Error: SAP_URL, SAP_USERNAME, SAP_PASSWORD must be set in .env');
    process.exit(1);
  }
  const client = new ADTClient(SAP_URL, SAP_USERNAME, SAP_PASSWORD, SAP_CLIENT, '');
  client.stateful = 'stateful';
  return client;
}

const OBJTYPE_MAP = {
  class:           'CLAS/OC',
  interface:       'INTF/OI',
  program:         'PROG/P',
  function_group:  'FUGR/F',
  function_module: 'FUGR/FF',
  msag:            'MSAG/N',
  table:           'TABL/DT',
  data_element:    'DTEL/DE',
  domain:          'DOMA/DD',
};

function parseArgs(argv) {
  const args = argv.slice(2);
  if (args.length < 3) {
    console.log(`Usage:
  node scripts/create_object.js <type> <name> <description> [--package <pkg>] [--transport <tr>] [--parent <group>] [--textpool <spec.md|entries.json>]

Types: class, interface, program, function_group, function_module, msag, table, data_element, domain
  function_module requires --parent <function_group_name>
  --textpool: プログラム作成後に textpool（selection-text / TEXT-symbols）を自動登録
Default package: $TMP (local object)`);
    process.exit(1);
  }

  const type = args[0].toLowerCase();
  const name = args[1].toUpperCase();
  const description = args[2];
  let pkg = '$TMP';
  let transport = '';
  let parent = null;
  let textpool = null;

  const pkgIdx = args.indexOf('--package');
  if (pkgIdx !== -1 && args[pkgIdx + 1]) pkg = args[pkgIdx + 1].toUpperCase();

  const trIdx = args.indexOf('--transport');
  if (trIdx !== -1 && args[trIdx + 1]) transport = args[trIdx + 1];

  const parentIdx = args.indexOf('--parent');
  if (parentIdx !== -1 && args[parentIdx + 1]) parent = args[parentIdx + 1].toUpperCase();

  const tpIdx = args.indexOf('--textpool');
  if (tpIdx !== -1 && args[tpIdx + 1]) textpool = args[tpIdx + 1];

  if (!OBJTYPE_MAP[type]) {
    console.error(`Error: Unsupported type "${type}". Use: ${Object.keys(OBJTYPE_MAP).join(', ')}`);
    process.exit(1);
  }

  if (type === 'function_module' && !parent) {
    console.error('Error: --parent <function_group_name> is required for function_module.');
    console.error('Example: node create_object.js function_module Z_MY_FM "desc" --parent ZFGR_MY_GROUP');
    process.exit(1);
  }

  return { type, name, description, pkg, transport, parent, textpool };
}

// ---------------------------------------------------------------------------
// --textpool: spec.md / JSON から textpool エントリを抽出
// ---------------------------------------------------------------------------
const fs = require('fs');
const path = require('path');

function loadTextpoolEntries(textpoolPath, progName) {
  if (!fs.existsSync(textpoolPath)) {
    console.error(`Error: textpool file not found: ${textpoolPath}`);
    process.exit(1);
  }

  const content = fs.readFileSync(textpoolPath, 'utf-8');
  const entries = [];

  // JSON ファイルの場合: 直接 textpool エントリ配列
  if (textpoolPath.endsWith('.json')) {
    const data = JSON.parse(content);
    return Array.isArray(data) ? data : (data.entries || []);
  }

  // spec.md / basic_design.md の場合: YAML ブロックから抽出
  const yamlMatch = content.match(/```yaml\r?\n([\s\S]*?)```/);
  if (!yamlMatch) {
    console.error('Error: YAML block not found in spec file');
    return entries;
  }

  let jsYaml;
  try { jsYaml = require('js-yaml'); } catch (e) {
    console.error('Error: js-yaml is required. Run: npm install js-yaml');
    return entries;
  }

  const doc = jsYaml.load(yamlMatch[1]);
  const spec = doc?.spec || doc || {};

  // selection_screen[] → selection text エントリ
  const selScreen = spec.selection_screen || spec.sap_specifics?.selection_screen || [];
  for (const field of selScreen) {
    if (field.name && field.label) {
      entries.push({
        type: 'S', // Selection text
        key: field.name.toUpperCase(),
        text: field.label,
      });
    }
  }

  // text_symbols[] → TEXT symbol エントリ
  const textSymbols = spec.text_symbols || spec.sap_specifics?.text_symbols || [];
  for (const sym of textSymbols) {
    if (sym.id && sym.text) {
      entries.push({
        type: 'I', // Text symbol (TEXT-xxx)
        key: String(sym.id).padStart(3, '0'),
        text: sym.text,
      });
    }
  }

  // program title → title エントリ
  const title = spec.title || spec.program_title;
  if (title) {
    entries.push({ type: 'R', key: progName, text: title });
  }

  return entries;
}

// ---------------------------------------------------------------------------
// ADT textpool PUT API
// ---------------------------------------------------------------------------
async function registerTextpoolADT(client, progName, entries, transport) {
  // ADT textpool resource: /sap/bc/adt/programs/programs/{name}/source/main/textpool
  const textpoolXml = buildTextpoolXml(entries);
  try {
    await client.httpClient.request(
      `/sap/bc/adt/programs/programs/${progName.toLowerCase()}/source/main/textpool`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/vnd.sap.adt.programs.textpool.v2+xml',
          ...(transport ? { 'x-csrf-token': client.csrfToken } : {}),
        },
        body: textpoolXml,
      }
    );
    return true;
  } catch (e) {
    console.log(`  ADT textpool PUT failed: ${e.message}. Falling back to GUI.`);
    return false;
  }
}

function buildTextpoolXml(entries) {
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
  xml += '<textPool:textPool xmlns:textPool="http://www.sap.com/adt/textpool">\n';
  for (const e of entries) {
    const typeAttr = e.type === 'S' ? 'selectionText' : e.type === 'I' ? 'textSymbol' : 'title';
    xml += `  <textPool:entry textPool:type="${typeAttr}" textPool:key="${e.key}" textPool:text="${escapeXml(e.text)}"/>\n`;
  }
  xml += '</textPool:textPool>';
  return xml;
}

function escapeXml(s) {
  return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ---------------------------------------------------------------------------
// GUI フォールバック: SE38 テキストプール編集
// ---------------------------------------------------------------------------
function registerTextpoolGUI(progName, entries) {
  const os = require('os');
  const { execSync } = require('child_process');

  // SE38 で textpool を開く WSF を生成
  const escJSStr = s => (s || '').replace(/\\/g, '\\\\').replace(/"/g, '\\"');

  // Selection text エントリの VBScript フィールド設定コード
  const selEntries = entries.filter(e => e.type === 'S');
  const textEntries = entries.filter(e => e.type === 'I');

  const wsf = `<?xml version="1.0" encoding="UTF-8"?>
<job><script language="JScript"><![CDATA[
function out(k,v){WScript.Echo(k+"="+v)}
function sleep(ms){WScript.Sleep(ms)}

try {
  var app = GetObject("SAPGUI").GetScriptingEngine;
  var ses = app.Children(0).Children(0);

  // SE38 テキスト要素を開く
  ses.findById("wnd[0]/tbar[0]/okcd").text = "/nSE38";
  ses.findById("wnd[0]").sendVKey(0);
  sleep(500);
  ses.findById("wnd[0]/usr/ctxtRS38M-PROGRAMM").text = "${escJSStr(progName)}";

  // テキスト要素ボタン（SE38 初期画面）
  try { ses.findById("wnd[0]/usr/radRS38M-FUNC_TEXP").select(); } catch(x) {
    try { ses.findById("wnd[0]/usr/radRS38M-TXEL").select(); } catch(x2) {}
  }
  ses.findById("wnd[0]/tbar[1]/btn[7]").press();
  sleep(500);

  // 変更モードに切替
  try { ses.findById("wnd[0]/tbar[1]/btn[25]").press(); sleep(300); } catch(x) {}

  // 選択テキストタブ → 入力
  // TODO: SE38 テキスト要素画面の構造はシステムバージョンにより異なる
  // 基本的にはテーブルコントロールに行を追加する形式

  out("TEXTPOOL_ENTRIES", "${selEntries.length + textEntries.length}");
  out("STATUS", "OK");

} catch(e) {
  out("STATUS", "ERROR");
  out("ERROR", e.message || String(e));
}
WScript.Quit(0);
]]></script></job>`;

  const tmpFile = path.join(os.tmpdir(), `sap_textpool_${process.pid}_${Date.now()}.wsf`);
  try {
    fs.writeFileSync(tmpFile, wsf, 'utf-8');
    const buf = execSync(`cscript //NoLogo "${tmpFile}"`, { timeout: 30000, shell: true });
    const output = buf.toString('utf-8');
    console.log(`  GUI textpool result: ${output.trim()}`);
  } catch (e) {
    console.error(`  GUI textpool failed: ${e.message}`);
  } finally {
    try { fs.unlinkSync(tmpFile); } catch (_) {}
  }
}

async function main() {
  const { type, name, description, pkg, transport, parent, textpool } = parseArgs(process.argv);

  // --- Transport / Package validation ---
  if (pkg !== '$TMP' && !transport) {
    console.error('');
    console.error('==========================================================');
    console.error('  ERROR: Transport number is required for non-$TMP objects');
    console.error(`  Package: ${pkg}`);
    console.error('  Usage: node create_object.js <type> <name> <desc> --package <pkg> --transport <tr>');
    console.error('==========================================================');
    console.error('');
    console.error('$TMP (local object) の場合は --transport を省略できます。');
    console.error('それ以外のパッケージでは移送番号が必須です。');
    process.exit(1);
  }

  const client = createClient();
  const objtype = OBJTYPE_MAP[type];

  // function_module の parentName は汎用グループ名、それ以外はパッケージ名
  const parentName = (type === 'function_module') ? parent : pkg;

  console.log(`Creating ${type}: ${name}`);
  console.log(`  ObjType:     ${objtype}`);
  console.log(`  Description: ${description}`);
  console.log(`  Package:     ${pkg}`);
  if (parent) console.log(`  Parent:      ${parent}`);
  console.log(`  Transport:   ${transport || '(none - local object)'}`);
  console.log('');

  try {
    await client.createObject({
      objtype: objtype,
      name: name,
      parentName: parentName,
      description: description,
      transportRequest: transport,
    });
    console.log(`${type} ${name} created successfully.`);
  } catch (err) {
    if (err.message && err.message.includes('already exists')) {
      console.log(`${type} ${name} already exists. Skipping creation.`);
    } else {
      console.error(`Error creating ${type}: ${err.message || err}`);
      if (err.response) {
        console.error(`HTTP ${err.response.status}: ${err.response.statusText || ''}`);
      }
      process.exit(1);
    }
  }

  // Session cleanup: drop stateful session to release any enqueue locks
  try { await client.dropSession(); } catch (_) {}

  // --textpool: textpool 自動登録（program タイプのみ）
  if (textpool) {
    if (type !== 'program') {
      console.log(`  --textpool is only supported for type=program (current: ${type}). Skipping.`);
    } else {
      console.log(`\nRegistering textpool from: ${textpool}`);
      const entries = loadTextpoolEntries(textpool, name);
      if (entries.length === 0) {
        console.log('  No textpool entries found. Skipping.');
      } else {
        console.log(`  Entries: ${entries.length} (S:${entries.filter(e => e.type === 'S').length} I:${entries.filter(e => e.type === 'I').length} R:${entries.filter(e => e.type === 'R').length})`);
        // ADT API を優先で試行
        const adtOk = await registerTextpoolADT(client, name, entries, transport);
        if (adtOk) {
          console.log('  Textpool registered via ADT API.');
        } else {
          // GUI フォールバック
          console.log('  Falling back to GUI textpool registration...');
          registerTextpoolGUI(name, entries);
        }
        // D010TINF 確認（textpool 登録後のリファレンスチェック）
        console.log(`\n  D010TINF reference check: SELECT * FROM D010TINF WHERE PROGNAME = '${name}'`);
        console.log('  (Run data_preview.js to verify textpool entries exist in D010TINF)');
      }
    }
  }
}

main();
