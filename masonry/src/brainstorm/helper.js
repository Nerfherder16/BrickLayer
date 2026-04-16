// helper.js — client-side module inlined into frame-template.html

let lastEventCount = 0;
let selectedSectionId = null;
let allSections = [];

function pollEvents() {
  fetch('/events')
    .then((res) => {
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            // Reconnect after a brief delay
            setTimeout(pollEvents, 1500);
            return;
          }
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop(); // keep incomplete line

          for (const line of lines) {
            if (!line.trim()) continue;
            try {
              const event = JSON.parse(line);
              handleEvent(event);
            } catch (_) {}
          }
          read();
        }).catch(() => {
          setTimeout(pollEvents, 1500);
        });
      }
      read();
    })
    .catch(() => {
      setTimeout(pollEvents, 1500);
    });
}

function handleEvent(event) {
  if (event.type === 'section_update') {
    fetchState();
  } else if (event.type === 'click') {
    updateStatusFromAction(event.section_id, event.action);
    if (event.action === 'expand' && event.section_id === selectedSectionId) {
      fetchState();
    }
  }
}

function fetchState() {
  fetch('/state')
    .then((r) => r.json())
    .then((data) => {
      allSections = data.sections || [];
      renderSidebar();
      updateHeader();
      if (selectedSectionId) {
        const section = allSections.find((s) => s.id === selectedSectionId);
        if (section) renderSection(section);
      } else if (allSections.length > 0) {
        selectSection(allSections[0].id);
      }
    })
    .catch(() => {});
}

function renderSidebar() {
  const list = document.getElementById('section-list');
  if (!list) return;
  list.innerHTML = '';
  for (const section of allSections) {
    const item = document.createElement('div');
    item.className = 'section-item' + (section.id === selectedSectionId ? ' active' : '');
    item.dataset.id = section.id;

    const dot = document.createElement('span');
    dot.className = 'status-dot';
    dot.id = 'dot-' + section.id;
    dot.style.backgroundColor = statusColor(section.status);

    const label = document.createElement('span');
    label.className = 'section-label';
    label.textContent = section.title;

    item.appendChild(dot);
    item.appendChild(label);
    item.addEventListener('click', () => selectSection(section.id));
    list.appendChild(item);
  }
}

function selectSection(id) {
  selectedSectionId = id;
  const section = allSections.find((s) => s.id === id);
  if (section) {
    renderSection(section);
  }
  // Update active state in sidebar
  document.querySelectorAll('.section-item').forEach((el) => {
    el.classList.toggle('active', el.dataset.id === id);
  });
}

function renderSection(section) {
  const emptyState = document.getElementById('empty-state');
  const canvasBody = document.getElementById('canvas-body');
  const titleEl = document.getElementById('canvas-title');
  const contentEl = document.getElementById('canvas-content');

  if (emptyState) emptyState.style.display = 'none';
  if (canvasBody) canvasBody.style.display = 'block';
  if (titleEl) titleEl.textContent = section.title;
  if (contentEl) contentEl.textContent = section.content || '(no content)';
}

function sendClick(sectionId, action) {
  fetch('/click', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ section_id: sectionId, action }),
  }).catch(() => {});
}

function updateStatusFromAction(sectionId, action) {
  let newStatus = null;
  if (action === 'approve') newStatus = 'approved';
  else if (action === 'flag') newStatus = 'flagged';

  if (newStatus) {
    updateStatus(sectionId, newStatus);
    const section = allSections.find((s) => s.id === sectionId);
    if (section) section.status = newStatus;
    updateHeader();
  }
}

function updateStatus(sectionId, status) {
  const dot = document.getElementById('dot-' + sectionId);
  if (dot) dot.style.backgroundColor = statusColor(status);
}

function statusColor(status) {
  if (status === 'approved') return '#3fb950';
  if (status === 'flagged') return '#f85149';
  return '#8b949e';
}

// Export for testing (no-op when inlined into HTML)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { statusColor };
} else if (typeof exports !== 'undefined') {
  exports.statusColor = statusColor;
}

function updateHeader() {
  const countEl = document.getElementById('section-count');
  if (!countEl) return;
  const approved = allSections.filter((s) => s.status === 'approved').length;
  countEl.textContent = approved + ' / ' + allSections.length + ' approved';
}

function onApprove() {
  if (!selectedSectionId) return;
  sendClick(selectedSectionId, 'approve');
}

function onFlag() {
  if (!selectedSectionId) return;
  sendClick(selectedSectionId, 'flag');
}

function onExpand() {
  if (!selectedSectionId) return;
  sendClick(selectedSectionId, 'expand');
}

// ── Chronicle tab ────────────────────────────────────────────────────────────

let currentTab = 'sections';

function switchTab(tab) {
  currentTab = tab;
  document.getElementById('tab-sections').classList.toggle('active', tab === 'sections');
  document.getElementById('tab-chronicle').classList.toggle('active', tab === 'chronicle');
  document.getElementById('section-list').style.display = tab === 'sections' ? '' : 'none';
  const chrPanel = document.getElementById('chronicle-panel');
  if (tab === 'chronicle') {
    chrPanel.classList.add('visible');
    loadChronicle();
  } else {
    chrPanel.classList.remove('visible');
  }
}

function loadChronicle() {
  const el = document.getElementById('chronicle-content');
  if (el) el.innerHTML = '<em style="color:#8b949e">Loading...</em>';
  fetch('/chronicle')
    .then((r) => r.json())
    .then((sessions) => renderChronicleList(sessions))
    .catch(() => {
      if (el) el.innerHTML = '<em style="color:#f85149">Chronicle unavailable</em>';
    });
}

function verdictHtml(v) {
  if (!v) return '<span style="color:#8b949e">—</span>';
  if (v === 'CLEAN') return '<span class="chr-verdict-clean">✓ CLEAN</span>';
  return '<span class="chr-verdict-drift">⚠ DRIFT</span>';
}

function renderChronicleList(sessions) {
  const el = document.getElementById('chronicle-content');
  if (!el) return;
  if (!sessions.length) {
    el.innerHTML = '<em style="color:#8b949e">No chronicle sessions yet.</em>';
    return;
  }
  let html = '<table class="chr-table"><thead><tr>'
    + '<th>Slug</th><th>Status</th><th>Sections</th><th>Builds</th><th>Drift</th><th>Started</th>'
    + '</tr></thead><tbody>';
  for (const s of sessions) {
    const date = s.started_at ? s.started_at.slice(0, 10) : '—';
    html += `<tr onclick="loadChronicleDetail(${s.id})">`
      + `<td>${s.slug}</td>`
      + `<td><span class="chr-status-badge">${s.status}</span></td>`
      + `<td>${s.section_count || 0}</td>`
      + `<td>${s.build_count || 0}</td>`
      + `<td>${verdictHtml(s.last_drift)}</td>`
      + `<td>${date}</td>`
      + '</tr>';
  }
  html += '</tbody></table>';
  el.innerHTML = html;
}

function loadChronicleDetail(id) {
  fetch('/chronicle/' + id)
    .then((r) => r.json())
    .then((detail) => renderChronicleDetail(detail))
    .catch(() => {});
}

function renderChronicleDetail(detail) {
  const el = document.getElementById('chronicle-content');
  if (!el) return;
  const { session, sections, builds } = detail;
  let html = `<div style="margin-bottom:10px"><button onclick="loadChronicle()" style="background:none;border:1px solid #30363d;color:#8b949e;padding:3px 8px;border-radius:4px;cursor:pointer;font-size:12px">← Back</button></div>`;
  html += `<div class="chr-detail"><h3>${session.slug}</h3>`;
  if (session.spec_path) html += `<div style="font-size:12px;color:#8b949e;margin-bottom:8px">Spec: ${session.spec_path}</div>`;
  html += `<div style="font-size:12px;color:#8b949e;margin-bottom:12px">Status: ${session.status} · Started: ${(session.started_at||'').slice(0,16)}</div>`;
  if (sections.length) {
    html += '<div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:#8b949e;margin-bottom:6px">Sections</div>';
    for (const s of sections) {
      const dot = s.status === 'approved' ? '#3fb950' : s.status === 'flagged' ? '#f85149' : '#8b949e';
      html += `<div class="chr-section-row"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${dot};margin-right:6px"></span><span>${s.title}</span></div>`;
    }
  }
  if (builds.length) {
    html += '<div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:#8b949e;margin:12px 0 6px">Builds</div>';
    for (const b of builds) {
      html += `<div class="chr-section-row">Build #${b.id} · ${verdictHtml(b.drift_verdict)} · ${(b.started_at||'').slice(0,16)}</div>`;
    }
  }
  html += '</div>';
  el.innerHTML = html;
}

// Init on load
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('btn-approve').addEventListener('click', onApprove);
  document.getElementById('btn-flag').addEventListener('click', onFlag);
  document.getElementById('btn-expand').addEventListener('click', onExpand);

  fetchState();
  pollEvents();
});
