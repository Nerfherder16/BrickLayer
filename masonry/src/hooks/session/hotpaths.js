'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

function getSlug(projectRoot) {
  return String(projectRoot).replace(/[:\\\/]+/g, '-').replace(/^-+|-+$/g, '').toLowerCase().slice(0, 80);
}

function getHotpathsFile(projectRoot) {
  return path.join(os.homedir(), '.masonry', 'state', getSlug(projectRoot), 'hotpaths.json');
}

function readData(projectRoot) {
  const file = getHotpathsFile(projectRoot);
  if (!fs.existsSync(file)) return {};
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return {}; }
}

function writeData(projectRoot, data) {
  const file = getHotpathsFile(projectRoot);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2), 'utf8');
}

function recordEdit(projectRoot, filePath) {
  const data = readData(projectRoot);
  data[filePath] = (data[filePath] || 0) + 1;
  writeData(projectRoot, data);
}

function getTopPaths(projectRoot, n = 5) {
  const data = readData(projectRoot);
  if (!Object.keys(data).length) return [];
  return Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, n).map(([file, count]) => ({ file, count }));
}

function injectContext(projectRoot) {
  const top = getTopPaths(projectRoot, 5);
  if (!top.length) return '';
  const lines = top.map((e, i) => `${i + 1}. ${e.file} (${e.count} edit${e.count === 1 ? '' : 's'})`);
  return '[Hot paths] Most-edited files this project:\n' + lines.join('\n');
}

module.exports = { recordEdit, getTopPaths, injectContext, getSlug, getHotpathsFile };
