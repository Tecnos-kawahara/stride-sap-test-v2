#!/usr/bin/env node
/**
 * read.js — "参照のために見る"
 *
 * SAPオブジェクトのソースコードまたはDDIC定義を標準出力に表示するスクリプト。
 * ファイルは作成しない（参照専用）。
 *
 * Usage:
 *   node scripts/read.js <type> <name>
 *
 * Types:
 *   class, interface, program, function_group, include
 *   table, structure, data_element, domain
 *
 * Examples:
 *   node scripts/read.js class ZCL_MY_CLASS
 *   node scripts/read.js table ZTMY_TABLE
 *   node scripts/read.js data_element ZDE_EXAMPLE
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

// URI patterns for each object type
const URI_MAP = {
  class:          (name) => `/sap/bc/adt/oo/classes/${name.toLowerCase()}`,
  interface:      (name) => `/sap/bc/adt/oo/interfaces/${name.toLowerCase()}`,
  program:        (name) => `/sap/bc/adt/programs/programs/${name.toLowerCase()}`,
  function_group: (name) => `/sap/bc/adt/functions/groups/${name.toLowerCase()}`,
  include:        (name) => `/sap/bc/adt/programs/includes/${name.toLowerCase()}`,
  table:          (name) => `/sap/bc/adt/ddic/tables/${name.toLowerCase()}`,
  structure:      (name) => `/sap/bc/adt/ddic/structures/${name.toLowerCase()}`,
  data_element:   (name) => `/sap/bc/adt/ddic/dataelements/${name.toLowerCase()}`,
  domain:         (name) => `/sap/bc/adt/ddic/domains/${name.toLowerCase()}`,
};

const SOURCE_TYPES = new Set(['class', 'interface', 'program', 'function_group', 'include']);
const DDIC_TYPES = new Set(['table', 'structure', 'data_element', 'domain']);

function printUsage() {
  console.log(`Usage:
  node scripts/read.js <type> <name>

Types:
  class, interface, program, function_group, include,
  table, structure, data_element, domain`);
}

function parseArgs(argv) {
  const args = argv.slice(2);
  if (args.length < 2) {
    printUsage();
    process.exit(1);
  }
  const type = args[0];
  const name = args[1].toUpperCase();

  if (!URI_MAP[type]) {
    console.error(`Error: Unknown type "${type}".`);
    printUsage();
    process.exit(1);
  }
  return { type, name };
}

// ---------------------------------------------------------------------------
// DDIC formatting
// ---------------------------------------------------------------------------

function formatDdicElement(info) {
  const lines = [];
  lines.push(`=== DDIC Element ===`);
  if (info.name) lines.push(`Name:        ${info.name}`);
  if (info.type) lines.push(`Type:        ${info.type}`);
  if (info.description) lines.push(`Description: ${info.description}`);

  // Format fields / components if present
  const fields = info.fields || info.components || info.columns || [];
  if (Array.isArray(fields) && fields.length > 0) {
    lines.push('');
    lines.push('Fields:');
    lines.push('-'.repeat(80));
    const header = 'Name'.padEnd(30) + 'Type'.padEnd(20) + 'Length'.padEnd(10) + 'Description';
    lines.push(header);
    lines.push('-'.repeat(80));
    for (const f of fields) {
      const fname = String(f.name || f.FIELDNAME || '').padEnd(30);
      const ftype = String(f.type || f.DATATYPE || f.ROLLNAME || '').padEnd(20);
      const flen = String(f.length || f.LENG || '').padEnd(10);
      const fdesc = String(f.description || f.DDTEXT || '');
      lines.push(`${fname}${ftype}${flen}${fdesc}`);
    }
  }

  // Dump remaining properties for completeness
  if (info.properties) {
    lines.push('');
    lines.push('Properties:');
    for (const [k, v] of Object.entries(info.properties)) {
      lines.push(`  ${k}: ${v}`);
    }
  }

  return lines.join('\n');
}

function formatObjectStructure(structure) {
  // Try to produce useful output from objectStructure
  const lines = [];
  lines.push(`=== Object Structure ===`);

  function dump(obj, indent) {
    if (obj === null || obj === undefined) return;
    if (typeof obj === 'string' || typeof obj === 'number' || typeof obj === 'boolean') {
      lines.push(`${' '.repeat(indent)}${obj}`);
      return;
    }
    if (Array.isArray(obj)) {
      for (const item of obj) dump(item, indent);
      return;
    }
    if (typeof obj === 'object') {
      for (const [k, v] of Object.entries(obj)) {
        if (v === null || v === undefined) continue;
        if (typeof v === 'object') {
          lines.push(`${' '.repeat(indent)}${k}:`);
          dump(v, indent + 2);
        } else {
          lines.push(`${' '.repeat(indent)}${k}: ${v}`);
        }
      }
    }
  }

  dump(structure, 0);
  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  const { type, name } = parseArgs(process.argv);
  const client = createClient();
  const uri = URI_MAP[type](name);

  try {
    if (SOURCE_TYPES.has(type)) {
      // Retrieve and display source code
      console.log(`--- ${type.toUpperCase()}: ${name} ---`);
      console.log(`--- URI: ${uri}/source/main ---\n`);

      const source = await client.getObjectSource(`${uri}/source/main`);
      console.log(source);

      // For classes, also try to show test class source
      if (type === 'class') {
        try {
          const testSource = await client.getObjectSource(`${uri}/includes/testclasses`);
          if (testSource) {
            console.log(`\n--- TEST CLASS: ${name} ---\n`);
            console.log(testSource);
          }
        } catch (_) {
          // No test class — ignore
        }
      }
    } else if (DDIC_TYPES.has(type)) {
      console.log(`--- ${type.toUpperCase()}: ${name} ---`);
      console.log(`--- URI: ${uri} ---\n`);

      // Try ddicElement first for data_element / domain
      if (type === 'data_element' || type === 'domain') {
        try {
          const info = await client.ddicElement(name);
          console.log(formatDdicElement(info));
          return;
        } catch (_) {
          // Fall through to objectStructure
        }
      }

      // Use objectStructure for tables / structures or as fallback
      const structure = await client.objectStructure(uri);
      console.log(formatObjectStructure(structure));
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
