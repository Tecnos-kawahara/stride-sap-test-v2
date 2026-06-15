#!/usr/bin/env node
/**
 * activate.js — "保存・有効化する"
 *
 * ローカルファイルのABAPソースをSAPにアップロードし、有効化するスクリプト。
 * フロー: Lock → Upload → (テストクラス検出・Upload) → Activate → Unlock
 *
 * Usage:
 *   node scripts/activate.js <file_path> <transport_number> [--type <type>] [--name <name>]
 *
 * Examples:
 *   node scripts/activate.js src/zpackage/zcl_example/zcl_example.clas.abap DEVK900001
 *   node scripts/activate.js src/zpackage/zreport/zreport.prog.abap DEVK900001
 *   node scripts/activate.js myfile.abap DEVK900001 --type class --name ZCL_EXAMPLE
 *   node scripts/activate.js src/z_my_fm.fugr.abap --fugr ZFGR_MY_GROUP --name Z_MY_FM
 *
 * File extensions (auto-detect):
 *   .clas.abap              → class (main source)
 *   .clas.testclasses.abap  → class (test class)
 *   .prog.abap              → program
 *   .intf.abap              → interface
 *   .fugr.abap              → function_group
 *   .incl.abap              → include
 *
 * Include program (--main-program):
 *   既に他プログラムに INCLUDE されている Include を有効化する場合、
 *   親プログラムの指定が必要。--main-program を省略すると usageReferences
 *   で自動検索し、候補を提示する。
 *
 * Function Module (--fugr):
 *   --fugr <group_name> を指定すると、function_group ではなく個別の
 *   function_module として扱う。ソースは ABAP 宣言構文形式
 *   (FUNCTION name IMPORTING... ENDFUNCTION.) で記述すること。
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
  const client = new ADTClient(SAP_URL, SAP_USERNAME, SAP_PASSWORD, SAP_CLIENT, '');
  client.stateful = 'stateful';
  return client;
}

// Extension → type + sourceType mapping
const EXTENSION_MAP = {
  '.clas.testclasses.abap': { type: 'class', sourceType: 'testclasses' },
  '.prog.testclasses.abap': { type: 'program', sourceType: 'testclasses' },
  '.clas.abap':             { type: 'class', sourceType: 'main' },
  '.prog.abap':             { type: 'program', sourceType: 'main' },
  '.intf.abap':             { type: 'interface', sourceType: 'main' },
  '.fugr.abap':             { type: 'function_group', sourceType: 'main' },
  '.incl.abap':             { type: 'include', sourceType: 'main' },
};

const URI_MAP = {
  class:          (name) => `/sap/bc/adt/oo/classes/${name.toLowerCase()}`,
  interface:      (name) => `/sap/bc/adt/oo/interfaces/${name.toLowerCase()}`,
  program:        (name) => `/sap/bc/adt/programs/programs/${name.toLowerCase()}`,
  function_group: (name) => `/sap/bc/adt/functions/groups/${name.toLowerCase()}`,
  include:        (name) => `/sap/bc/adt/programs/includes/${name.toLowerCase()}`,
  table:          (name) => `/sap/bc/adt/ddic/tables/${name.toLowerCase()}`,
  data_element:   (name) => `/sap/bc/adt/ddic/dataelements/${name.toLowerCase()}`,
  domain:         (name) => `/sap/bc/adt/ddic/domains/${name.toLowerCase()}`,
};

/**
 * Detect type and name from file path extension.
 * Checks longest extensions first to avoid false matches.
 */
function detectFromFile(filePath) {
  const basename = path.basename(filePath).toLowerCase();

  // Check extensions from longest to shortest
  const sortedExts = Object.keys(EXTENSION_MAP).sort((a, b) => b.length - a.length);
  for (const ext of sortedExts) {
    if (basename.endsWith(ext)) {
      const name = basename.slice(0, basename.length - ext.length).toUpperCase();
      return { ...EXTENSION_MAP[ext], name };
    }
  }
  return null;
}

function printUsage() {
  console.log(`Usage:
  node scripts/activate.js <file_path> <transport_number> [--type <type>] [--name <name>]

File extensions (auto-detect):
  .clas.abap              → class
  .clas.testclasses.abap  → class (test class)
  .prog.abap              → program
  .intf.abap              → interface
  .fugr.abap              → function_group

Explicit --type required for DDIC objects:
  table, data_element, domain`);
}

function parseArgs(argv) {
  const args = argv.slice(2);
  if (args.length < 1) {
    printUsage();
    process.exit(1);
  }

  const filePath = args[0];
  // transport is now optional (not required for $TMP)
  const transport = args[1] || '';

  let type = null;
  let name = null;
  let pkg = null;

  const typeIdx = args.indexOf('--type');
  if (typeIdx !== -1 && args[typeIdx + 1]) type = args[typeIdx + 1];

  const nameIdx = args.indexOf('--name');
  if (nameIdx !== -1 && args[nameIdx + 1]) name = args[nameIdx + 1].toUpperCase();

  const pkgIdx = args.indexOf('--package');
  if (pkgIdx !== -1 && args[pkgIdx + 1]) pkg = args[pkgIdx + 1].toUpperCase();

  let fugr = null;
  const fugrIdx = args.indexOf('--fugr');
  if (fugrIdx !== -1 && args[fugrIdx + 1]) fugr = args[fugrIdx + 1].toUpperCase();

  let mainProgram = null;
  const mpIdx = args.indexOf('--main-program');
  if (mpIdx !== -1 && args[mpIdx + 1]) mainProgram = args[mpIdx + 1].toUpperCase();

  return { filePath, transport, type, name, pkg, fugr, mainProgram };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

/**
 * Resolve the package of an existing SAP object via ADT API.
 * Returns the package name (e.g. '$TMP', 'ZPACKAGE') or null if not found.
 */
async function resolvePackage(client, baseUri) {
  try {
    const metadata = await client.objectStructure(baseUri);
    if (metadata && metadata.metaData && metadata.metaData['adtcore:packageName']) {
      return metadata.metaData['adtcore:packageName'].toUpperCase();
    }
    // Try alternative structure
    if (metadata && metadata.metaData) {
      for (const [key, value] of Object.entries(metadata.metaData)) {
        if (key.toLowerCase().includes('package') && typeof value === 'string') {
          return value.toUpperCase();
        }
      }
    }
  } catch (_) {
    // ignore - package resolution is best-effort
  }
  return null;
}

async function main() {
  const { filePath, transport, type: argType, name: argName, pkg: argPkg, fugr, mainProgram } = parseArgs(process.argv);

  // Read source file
  if (!fs.existsSync(filePath)) {
    console.error(`Error: File not found: ${filePath}`);
    process.exit(1);
  }
  const source = fs.readFileSync(filePath, 'utf-8');

  // Detect or use provided type/name
  const detected = detectFromFile(filePath);
  let objType = argType || (detected && detected.type);
  const objName = argName || (detected && detected.name);
  const sourceType = (detected && detected.sourceType) || 'main';

  // --fugr 指定時: function_group ではなく function_module として扱う
  if (fugr && objType === 'function_group') {
    objType = 'function_module';
  }

  if (!objType || !objName) {
    console.error('Error: Could not detect object type/name from file extension.');
    console.error('Use --type and --name to specify explicitly.');
    process.exit(1);
  }

  let baseUri, sourceUri;
  if (objType === 'function_module' || fugr) {
    // 汎用モジュール個別: /sap/bc/adt/functions/groups/{fugr}/fmodules/{fm}
    const fugrName = fugr || argName; // --fugr 未指定の場合はフォールバック
    if (!fugr) {
      console.error('Error: --fugr <function_group_name> is required for function_module.');
      process.exit(1);
    }
    baseUri = `/sap/bc/adt/functions/groups/${fugrName.toLowerCase()}/fmodules/${objName.toLowerCase()}`;
    sourceUri = `${baseUri}/source/main`;
  } else {
    if (!URI_MAP[objType]) {
      console.error(`Error: Unsupported type "${objType}".`);
      process.exit(1);
    }
    baseUri = URI_MAP[objType](objName);
    sourceUri = sourceType === 'testclasses'
      ? `${baseUri}/includes/testclasses`
      : `${baseUri}/source/main`;
  }

  const client = createClient();
  let lockHandle = null;

  // --- Transport / Package validation ---
  let pkg = argPkg;
  if (!pkg) {
    // Try to resolve package from SAP
    pkg = await resolvePackage(client, baseUri);
    if (pkg) {
      console.log(`Package (auto-detected): ${pkg}`);
    }
  }

  if (pkg && pkg !== '$TMP' && !transport) {
    console.error('');
    console.error('==========================================================');
    console.error('  ERROR: Transport number is required for non-$TMP objects');
    console.error(`  Package: ${pkg}`);
    console.error('  Usage: node activate.js <file> <transport_number>');
    console.error('==========================================================');
    console.error('');
    console.error('$TMP (local object) の場合は transport を省略できます。');
    console.error('それ以外のパッケージでは移送番号が必須です。');
    process.exit(1);
  }

  if (!pkg && !transport) {
    console.warn('');
    console.warn('WARNING: パッケージを特定できず、移送番号も指定されていません。');
    console.warn('  $TMP (ローカルオブジェクト) として続行します。');
    console.warn('  $TMP 以外のパッケージの場合、アップロード時にエラーになる可能性があります。');
    console.warn('  明示的に指定するには: --package <PKG> と移送番号を渡してください。');
    console.warn('');
  }

  console.log(`Object:    ${objType} ${objName}`);
  console.log(`Source:    ${sourceType}`);
  console.log(`Transport: ${transport || '(none - local object)'}`);
  console.log(`Package:   ${pkg || '(unknown)'}`);
  console.log(`File:      ${filePath}`);
  console.log(`URI:       ${sourceUri}`);
  console.log('');

  try {
    // Step 1: Lock
    console.log('Locking object...');
    try {
      const lockResult = await client.lock(baseUri);
      lockHandle = (typeof lockResult === 'object' && lockResult.LOCK_HANDLE)
        ? lockResult.LOCK_HANDLE
        : lockResult;
      console.log(`  Lock acquired: ${lockHandle}`);
    } catch (lockErr) {
      console.error(`\nError: Failed to lock object.`);
      console.error(`  ${lockErr.message || lockErr}`);
      console.error('\nThe object may be locked by another user.');
      console.error('Check transaction SM12 or use: node scripts/unlock.js --type ' + objType + ' --name ' + objName);
      process.exit(1);
    }

    // Step 2: Upload source
    console.log('Uploading source...');
    await client.setObjectSource(sourceUri, source, lockHandle, transport);
    console.log('  Source uploaded.');

    // Step 2b: If this is a main source, check for companion test class file
    if (sourceType === 'main') {
      const dir = path.dirname(filePath);
      const lowerName = objName.toLowerCase();
      // Map object type to its testclasses file extension
      const testExtMap = {
        'class': `.clas.testclasses.abap`,
        'program': `.prog.testclasses.abap`,
      };
      const testExt = testExtMap[objType];
      if (testExt) {
        const testFile = path.join(dir, `${lowerName}${testExt}`);
        if (fs.existsSync(testFile)) {
          console.log('Uploading test class...');
          const testSource = fs.readFileSync(testFile, 'utf-8');
          const testUri = `${baseUri}/includes/testclasses`;
          try {
            await client.setObjectSource(testUri, testSource, lockHandle, transport);
          } catch (testUploadErr) {
            const errMsg = String(testUploadErr.message || testUploadErr);
            const errData = testUploadErr.response && testUploadErr.response.data
              ? String(testUploadErr.response.data) : '';
            const combined = errMsg + ' ' + errData;
            if (combined.includes('無効なバージョン') || combined.includes('invalid version') || combined.includes('does not exist')) {
              // createTestInclude uses /sap/bc/adt/oo/classes/{name}/includes (class-only API)
              if (objType === 'class') {
                console.log('  Test include does not exist yet. Creating...');
                await client.createTestInclude(objName.toLowerCase(), lockHandle, transport);
                console.log('  Test include created. Retrying upload...');
                await client.setObjectSource(testUri, testSource, lockHandle, transport);
              } else {
                console.error('  Error: Test include does not exist. For programs, create the test include in SE80/ADT first.');
                throw testUploadErr;
              }
            } else {
              throw testUploadErr;
            }
          }
          console.log('  Test class uploaded.');
        }
      }
    }

    // Step 3: Unlock (before activation to avoid "currently processing" error)
    console.log('Unlocking...');
    await client.unLock(baseUri, lockHandle);
    lockHandle = null;
    console.log('  Unlocked.');

    // Step 4: Activate
    // Include プログラムの場合、親プログラムの指定が必要な場合がある
    let resolvedMainProgram = mainProgram || null;
    if (objType === 'include' && !resolvedMainProgram) {
      console.log('Searching for parent programs (usageReferences)...');
      try {
        const refs = await client.usageReferences(baseUri);
        const parentPrograms = (refs || [])
          .filter(r => r['adtcore:type'] && r['adtcore:type'].startsWith('PROG'))
          .map(r => ({ name: r['adtcore:name'], uri: r.uri, type: r['adtcore:type'] }));

        if (parentPrograms.length === 1) {
          resolvedMainProgram = parentPrograms[0].name;
          console.log(`  Parent program found: ${resolvedMainProgram} (auto-selected)`);
        } else if (parentPrograms.length > 1) {
          console.log(`  Multiple parent programs found:`);
          for (const p of parentPrograms) {
            console.log(`    - ${p.name} (${p.type})`);
          }
          console.error('\nError: Multiple parent programs found for this include.');
          console.error('Specify one with: --main-program <PROGRAM_NAME>');
          process.exit(1);
        } else {
          console.log('  No parent program found. Attempting standalone activation...');
        }
      } catch (refErr) {
        console.log(`  Could not search parent programs: ${refErr.message || refErr}`);
        console.log('  Attempting standalone activation...');
      }
    }

    console.log('Activating...');
    if (resolvedMainProgram) {
      console.log(`  Main program: ${resolvedMainProgram}`);
    }
    try {
      const mainIncludeUri = resolvedMainProgram
        ? `/sap/bc/adt/programs/programs/${resolvedMainProgram.toLowerCase()}`
        : undefined;
      const actResult = await client.activate(objName, baseUri, mainIncludeUri);
      if (actResult && actResult.success === false) {
        console.error('\nError: Activation failed.');
        if (actResult.messages && actResult.messages.length) {
          for (const msg of actResult.messages) {
            const line = msg.line ? ` (line ${msg.line})` : '';
            console.error(`  [${msg.type}]${line} ${msg.shortText || msg.text || ''}`);
          }
        }
        if (objType === 'include' && !resolvedMainProgram) {
          console.error('\nHint: This include may require a parent program for activation.');
          console.error('Use: --main-program <PROGRAM_NAME>');
        }
        process.exit(1);
      }
      console.log('  Activation successful.');
    } catch (actErr) {
      console.error(`\nError: Activation failed.`);
      console.error(`  ${actErr.message || actErr}`);
      if (objType === 'include' && !resolvedMainProgram) {
        console.error('\nHint: This include may require a parent program for activation.');
        console.error('Use: --main-program <PROGRAM_NAME>');
      }
      process.exit(1);
    }

    console.log('\nDone. Object activated successfully.');

    // Evidence output
    const stepId = getStepIdFromArgs();
    if (stepId) {
      // Derive feature-dir from source file path or --feature-dir arg
      const fdIdx = process.argv.indexOf('--feature-dir');
      let featureDir = (fdIdx !== -1 && process.argv[fdIdx + 1]) ? process.argv[fdIdx + 1] : null;
      if (!featureDir) {
        const absFile = path.resolve(filePath);
        const specsIdx = absFile.indexOf(path.sep + 'specs' + path.sep);
        if (specsIdx !== -1) {
          const afterSpecs = absFile.substring(specsIdx + 6);
          const featureName = afterSpecs.split(path.sep)[0];
          if (featureName) {
            featureDir = absFile.substring(0, specsIdx) + path.sep + 'specs' + path.sep + featureName;
          }
        }
      }
      if (featureDir) {
        writeEvidenceIfStepId({
          featureDir,
          stepId,
          toolName: 'activate.js',
          command: process.argv.join(' '),
          options: [filePath, transport || '(none)'].filter(Boolean),
          resultSummary: `Activation successful: ${objType} ${objName}`,
        });
      } else {
        console.error('Warning: --step-id specified but --feature-dir not provided and could not be inferred. Skipping evidence output.');
      }
    }
  } catch (err) {
    console.error(`\nError: ${err.message || err}`);
    if (err.response) {
      console.error(`HTTP ${err.response.status}: ${err.response.statusText || ''}`);
      if (err.response.data) {
        const data = typeof err.response.data === 'string'
          ? err.response.data
          : JSON.stringify(err.response.data, null, 2);
        console.error(`Response body:\n${data}`);
      }
    }
    if (err.properties) {
      console.error('Error properties:', JSON.stringify(err.properties, null, 2));
    }
    // Always try to unlock in finally-like fashion
    if (lockHandle) {
      try {
        console.log('Attempting emergency unlock...');
        await client.unLock(baseUri, lockHandle);
        console.log('  Unlocked.');
      } catch (_) {
        console.error('  Warning: Could not unlock object. Use SM12 to release manually.');
      }
    }
    process.exit(1);
  }
}

main();
