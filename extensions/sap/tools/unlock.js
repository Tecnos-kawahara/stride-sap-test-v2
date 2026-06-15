#!/usr/bin/env node
/**
 * unlock.js — "ロックを解除する"
 *
 * SAPオブジェクトのロックを緊急解除するスクリプト。
 * lock() → 即座に unLock() の手順でロックをリリースする。
 *
 * Usage:
 *   node scripts/unlock.js --type <type> --name <name>
 *
 * Types:
 *   class, interface, program, function_group, include
 *
 * Examples:
 *   node scripts/unlock.js --type class --name ZCL_MY_CLASS
 *   node scripts/unlock.js --type program --name ZREPORT
 *
 * Environment (.env):
 *   SAP_URL       — SAP system URL
 *   SAP_USERNAME  — SAP user
 *   SAP_PASSWORD  — SAP password
 *   SAP_CLIENT    — SAP client number
 */

'use strict';

const { ADTClient } = require('abap-adt-api');
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
  msag:           (name) => `/sap/bc/adt/messageclass/${name.toLowerCase()}`,
};

function printUsage() {
  console.log(`Usage:
  node scripts/unlock.js --type <type> --name <name>

Types:
  class, interface, program, function_group, include`);
}

function parseArgs(argv) {
  const args = argv.slice(2);

  let type = null;
  let name = null;

  const typeIdx = args.indexOf('--type');
  if (typeIdx !== -1 && args[typeIdx + 1]) type = args[typeIdx + 1];

  const nameIdx = args.indexOf('--name');
  if (nameIdx !== -1 && args[nameIdx + 1]) name = args[nameIdx + 1].toUpperCase();

  if (!type || !name) {
    console.error('Error: --type and --name are required.');
    printUsage();
    process.exit(1);
  }

  if (!URI_MAP[type]) {
    console.error(`Error: Unsupported type "${type}".`);
    printUsage();
    process.exit(1);
  }

  return { type, name };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const { type, name } = parseArgs(process.argv);
  const client = createClient();
  client.stateful = 'stateful';
  const uri = URI_MAP[type](name);

  console.log(`Attempting to release lock for ${type} ${name}...`);
  console.log(`URI: ${uri}\n`);

  try {
    // Step 1: Acquire lock (to get a lock handle)
    let lockHandle;
    try {
      lockHandle = await client.lock(uri);
      console.log(`  Lock acquired: ${lockHandle}`);
    } catch (lockErr) {
      const msg = (lockErr.message || String(lockErr)).toLowerCase();

      // If already locked by someone else, report it
      if (msg.includes('locked') || msg.includes('enqueue')) {
        console.error(`\nError: Object is locked by another user.`);
        console.error(`  ${lockErr.message || lockErr}`);
        console.error(`\nThis script can only release locks owned by the current user (${process.env.SAP_USERNAME}).`);
        console.error('For locks held by other users, use transaction SM12 in the SAP GUI.');
        process.exit(1);
      }

      // If "not locked" or "already unlocked", treat as success
      if (msg.includes('not locked') || msg.includes('unlocked') || msg.includes('not found')) {
        console.log('  Object is not currently locked. Nothing to do.');
        process.exit(0);
      }

      // Unknown lock error
      throw lockErr;
    }

    // Step 2: Immediately unlock
    try {
      await client.unLock(uri, lockHandle);
      console.log('  Lock released successfully.');
    } catch (unlockErr) {
      const msg = (unlockErr.message || String(unlockErr)).toLowerCase();
      if (msg.includes('not locked') || msg.includes('unlocked')) {
        console.log('  Object was already unlocked.');
      } else {
        throw unlockErr;
      }
    }

    console.log('\nDone.');
  } catch (err) {
    console.error(`\nError: ${err.message || err}`);
    if (err.response) {
      console.error(`HTTP ${err.response.status}: ${err.response.statusText || ''}`);
    }
    console.error('\nAlternative: Use transaction SM12 in SAP GUI to manage locks manually.');
    process.exit(1);
  }
}

main();
