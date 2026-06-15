#!/usr/bin/env node
/**
 * search.js — "探す・一覧する"
 *
 * SAPシステム上のオブジェクト検索およびパッケージ内容一覧を行うスクリプト。
 *
 * Usage:
 *   node scripts/search.js object <query> [--type class|program|table|...]
 *   node scripts/search.js package <package_name>
 *
 * Examples:
 *   node scripts/search.js object ZCL_MY* --type class
 *   node scripts/search.js object ZTEST
 *   node scripts/search.js package ZMY_PACKAGE
 *
 * Environment (.env):
 *   SAP_URL       — SAP system URL (e.g. https://vhcalnplci:8000)
 *   SAP_USERNAME  — SAP user
 *   SAP_PASSWORD  — SAP password
 *   SAP_CLIENT    — SAP client number (e.g. 001)
 */

'use strict';

const { ADTClient } = require('abap-adt-api');
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

function printTable(rows, columns) {
  if (rows.length === 0) {
    console.log('(no results)');
    return;
  }
  // Calculate column widths
  const widths = {};
  for (const col of columns) {
    widths[col.key] = col.label.length;
  }
  for (const row of rows) {
    for (const col of columns) {
      const val = String(row[col.key] || '');
      if (val.length > widths[col.key]) widths[col.key] = val.length;
    }
  }
  // Header
  const header = columns.map(c => c.label.padEnd(widths[c.key])).join('  ');
  const separator = columns.map(c => '-'.repeat(widths[c.key])).join('  ');
  console.log(header);
  console.log(separator);
  // Rows
  for (const row of rows) {
    const line = columns.map(c => String(row[c.key] || '').padEnd(widths[c.key])).join('  ');
    console.log(line);
  }
  console.log(`\n${rows.length} result(s)`);
}

function parseArgs(argv) {
  const args = argv.slice(2);
  if (args.length === 0) {
    printUsage();
    process.exit(1);
  }
  const subcommand = args[0];
  if (subcommand !== 'object' && subcommand !== 'package') {
    console.error(`Error: Unknown subcommand "${subcommand}". Use "object" or "package".`);
    printUsage();
    process.exit(1);
  }
  if (!args[1]) {
    console.error(`Error: Missing argument for "${subcommand}".`);
    printUsage();
    process.exit(1);
  }
  const target = args[1];
  let type = null;
  const typeIdx = args.indexOf('--type');
  if (typeIdx !== -1 && args[typeIdx + 1]) {
    type = args[typeIdx + 1];
  }
  return { subcommand, target, type };
}

function printUsage() {
  console.log(`Usage:
  node scripts/search.js object <query> [--type class|program|table|...]
  node scripts/search.js package <package_name>`);
}

// ADT search type mapping
const TYPE_MAP = {
  class:          'CLAS',
  interface:      'INTF',
  program:        'PROG',
  function_group: 'FUGR',
  include:        'PROG',
  table:          'TABL',
  structure:      'TABL',
  data_element:   'DTEL',
  domain:         'DOMA',
  package:        'DEVC/K',
};

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function searchObject(client, query, type) {
  console.log(`Searching for objects matching "${query}"${type ? ` (type: ${type})` : ''}...\n`);

  // searchObject(query, objType?) — objType is a string like 'CLAS', 'PROG', etc.
  if (type && !TYPE_MAP[type]) {
    console.warn(`Warning: Unknown --type "${type}". Valid types: ${Object.keys(TYPE_MAP).join(', ')}`);
    console.warn('Searching without type filter.\n');
  }
  const objType = (type && TYPE_MAP[type]) ? TYPE_MAP[type] : undefined;
  const results = await client.searchObject(query, objType);

  const rows = (Array.isArray(results) ? results : []).map(r => ({
    name: r['adtcore:name'] || r.name || r['OBJECT_NAME'] || '',
    type: r['adtcore:type'] || r.type || r['OBJECT_TYPE'] || '',
    description: r['adtcore:description'] || r.description || r['DESCRIPTION'] || '',
  }));

  printTable(rows, [
    { key: 'name', label: 'Name' },
    { key: 'type', label: 'Type' },
    { key: 'description', label: 'Description' },
  ]);

  return rows.length;
}

async function listPackage(client, packageName) {
  console.log(`Listing contents of package "${packageName}"...\n`);

  const result = await client.nodeContents('DEVC/K', packageName);

  const nodes = result.nodes || result.objectNodes || [];
  const rows = (Array.isArray(nodes) ? nodes : []).map(n => ({
    name: n['OBJECT_NAME'] || n.name || n['adtcore:name'] || '',
    type: n['OBJECT_TYPE'] || n.type || n['adtcore:type'] || '',
    description: n['OBJECT_DESCRIPTION'] || n.description || n['adtcore:description'] || '',
  }));

  printTable(rows, [
    { key: 'name', label: 'Name' },
    { key: 'type', label: 'Type' },
    { key: 'description', label: 'Description' },
  ]);

  return rows.length;
}

function getFeatureDirFromArgs() {
  const idx = process.argv.indexOf('--feature-dir');
  if (idx !== -1 && idx + 1 < process.argv.length) {
    return process.argv[idx + 1];
  }
  return null;
}

async function main() {
  const { subcommand, target, type } = parseArgs(process.argv);
  const client = createClient();
  let resultCount = 0;

  try {
    if (subcommand === 'object') {
      resultCount = await searchObject(client, target, type);
    } else {
      resultCount = await listPackage(client, target);
    }
  } catch (err) {
    console.error(`\nError: ${err.message || err}`);
    if (err.response) {
      console.error(`HTTP ${err.response.status}: ${err.response.statusText || ''}`);
    }
    process.exit(1);
  }

  // Evidence output
  const stepId = getStepIdFromArgs();
  if (stepId) {
    const featureDir = getFeatureDirFromArgs();
    if (featureDir) {
      writeEvidenceIfStepId({
        featureDir,
        stepId,
        toolName: 'search.js',
        command: process.argv.join(' '),
        options: [subcommand, target, type ? `--type ${type}` : ''].filter(Boolean),
        resultSummary: `${resultCount} result(s)`,
      });
    } else {
      console.error('Warning: --step-id specified but --feature-dir not provided. Skipping evidence output.');
    }
  }
}

main();
