#!/usr/bin/env node
/**
 * pull.js — "編集するために取得する"
 *
 * SAPオブジェクトのソースコードをローカルファイルに保存するスクリプト。
 * abaplint命名規則に従ったファイル名で src/{package}/{name}.{ext} に保存する。
 *
 * Usage:
 *   node scripts/pull.js <name> <type> [--dir <package_dir>]
 *
 * Types:
 *   class, interface, program, function_group, function_module, include
 *
 * Examples:
 *   node scripts/pull.js ZCL_MY_CLASS class
 *   node scripts/pull.js ZCL_MY_CLASS class --dir ZMYPACKAGE
 *   node scripts/pull.js ZREPORT program
 *   node scripts/pull.js Z_MY_FM function_module --fugr ZFGR_MY_GROUP
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
  interface:      (name) => `/sap/bc/adt/oo/interfaces/${name.toLowerCase()}`,
  program:        (name) => `/sap/bc/adt/programs/programs/${name.toLowerCase()}`,
  function_group: (name) => `/sap/bc/adt/functions/groups/${name.toLowerCase()}`,
  include:        (name) => `/sap/bc/adt/programs/includes/${name.toLowerCase()}`,
};

// abaplint file extensions
const EXT_MAP = {
  class:           '.clas.abap',
  interface:       '.intf.abap',
  program:         '.prog.abap',
  function_group:  '.fugr.abap',
  function_module: '.fugr.abap',
  include:         '.prog.abap',
};

const VALID_TYPES = new Set(Object.keys(URI_MAP));

function printUsage() {
  console.log(`Usage:
  node scripts/pull.js <name> <type> [--dir <package_dir>] [--fugr <group_name>]

Types:
  class, interface, program, function_group, function_module, include

function_module requires --fugr <function_group_name>`);
}

function parseArgs(argv) {
  const args = argv.slice(2);
  if (args.length < 2) {
    printUsage();
    process.exit(1);
  }

  const name = args[0].toUpperCase();
  const type = args[1];
  let dir = null;
  let fugr = null;

  const dirIdx = args.indexOf('--dir');
  if (dirIdx !== -1 && args[dirIdx + 1]) {
    dir = args[dirIdx + 1];
  }

  const fugrIdx = args.indexOf('--fugr');
  if (fugrIdx !== -1 && args[fugrIdx + 1]) {
    fugr = args[fugrIdx + 1].toUpperCase();
  }

  if (!VALID_TYPES.has(type)) {
    console.error(`Error: Unknown type "${type}".`);
    printUsage();
    process.exit(1);
  }

  if (type === 'function_module' && !fugr) {
    console.error('Error: --fugr <function_group_name> is required for function_module.');
    console.error('Example: node pull.js Z_MY_FM function_module --fugr ZFGR_MY_GROUP');
    process.exit(1);
  }

  return { name, type, dir, fugr };
}

/**
 * Resolve package name from object structure if not provided.
 */
async function resolvePackage(client, uri) {
  try {
    const structure = await client.objectStructure(uri);
    // The package info is typically in the structure metadata
    const pkg =
      structure?.metaData?.['adtcore:packageName'] ||
      null;

    // Try to find DEVC/K reference in the structure
    if (structure?.links) {
      for (const link of structure.links) {
        if (link.type && link.type.includes('package')) {
          return link.name || link.uri?.split('/').pop() || null;
        }
      }
    }

    // Try to extract from the structure object directly
    if (typeof structure === 'object') {
      // Walk the structure looking for package references
      const json = JSON.stringify(structure);
      const match = json.match(/"DEVC\/K"\s*,\s*"([^"]+)"/);
      if (match) return match[1];

      // Look for packageRef or similar
      if (structure.packageRef) {
        return structure.packageRef['adtcore:name'] || structure.packageRef.name || null;
      }
    }

    return pkg;
  } catch (_) {
    return null;
  }
}

function writeFile(filePath, content) {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  fs.writeFileSync(filePath, content, 'utf-8');
  console.log(`  Saved: ${filePath}`);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const { name, type, dir, fugr } = parseArgs(process.argv);
  const client = createClient();
  // function_module: 個別FM URI を構築
  const uri = (type === 'function_module')
    ? `/sap/bc/adt/functions/groups/${fugr.toLowerCase()}/fmodules/${name.toLowerCase()}`
    : URI_MAP[type](name);
  const lowerName = name.toLowerCase();

  try {
    // Resolve package directory
    let packageDir = dir;
    if (!packageDir) {
      console.log('Resolving package...');
      packageDir = await resolvePackage(client, uri);
      if (packageDir) {
        console.log(`  Package: ${packageDir}`);
      } else {
        packageDir = '_unknown';
        console.log('  Package could not be resolved, using "_unknown"');
      }
    }

    const baseDir = path.join('src', packageDir.toLowerCase(), lowerName);
    const ext = EXT_MAP[type];

    // Pull main source
    console.log(`\nPulling ${type} ${name}...`);
    const sourceUri = `${uri}/source/main`;
    const source = await client.getObjectSource(sourceUri);

    const mainFile = path.join(baseDir, `${lowerName}${ext}`);
    writeFile(mainFile, source);

    // For classes, also pull test classes
    if (type === 'class') {
      try {
        console.log(`\nPulling test class for ${name}...`);
        const testUri = `${uri}/includes/testclasses`;
        const testSource = await client.getObjectSource(testUri);
        if (testSource && testSource.trim().length > 0) {
          const testFile = path.join(baseDir, `${lowerName}.clas.testclasses.abap`);
          writeFile(testFile, testSource);
        } else {
          console.log('  No test class content found.');
        }
      } catch (err) {
        console.log('  No test class found (this is normal if none exists).');
      }
    }

    console.log('\nDone.');

    // Evidence output
    const stepId = getStepIdFromArgs();
    if (stepId) {
      const featureDirIdx = process.argv.indexOf('--feature-dir');
      const featureDir = (featureDirIdx !== -1 && process.argv[featureDirIdx + 1]) ? process.argv[featureDirIdx + 1] : null;
      if (featureDir) {
        writeEvidenceIfStepId({
          featureDir,
          stepId,
          toolName: 'pull.js',
          command: process.argv.join(' '),
          options: [name, type, dir ? `--dir ${dir}` : ''].filter(Boolean),
          resultSummary: `Saved: ${path.join('src', packageDir.toLowerCase(), lowerName)}`,
        });
      } else {
        console.error('Warning: --step-id specified but --feature-dir not provided. Skipping evidence output.');
      }
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
