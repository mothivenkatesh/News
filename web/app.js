// fintech-inshorts — frontend logic
// Loads cards.json, renders Inshorts-style swipeable deck, handles category filters.

const feed = document.getElementById('feed');
const tabs = document.getElementById('tabs');
const meta = document.getElementById('meta');
const countEl = document.getElementById('count');

let allCards = [];
let activeCategory = 'all';

const CAT_LABELS = {
  rbi: 'RBI', npci: 'NPCI', sebi: 'SEBI', irdai: 'IRDAI',
  funding: 'Funding', personnel: 'Personnel', fraud: 'Fraud',
  vendor: 'Vendor', operator: 'Operator',
};

function timeAgo(iso) {
  const then = new Date(iso).getTime();
  const diffSec = Math.max(0, Math.floor((Date.now() - then) / 1000));
  if (diffSec < 60) return 'just now';
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  return `${Math.floor(diffSec / 86400)}d ago`;
}

function renderImportanceDots(score) {
  // 5 dots representing importance buckets: 1-2, 3-4, 5-6, 7-8, 9-10
  const filled = Math.ceil(score / 2);
  let html = '<span class="importance-dots" title="importance ' + score + '/10">';
  for (let i = 0; i < 5; i++) {
    html += `<span class="dot ${i < filled ? 'filled' : ''}"></span>`;
  }
  html += '</span>';
  return html;
}

function renderCard(c) {
  const img = c.image_url
    ? `<img src="${escapeAttr(c.image_url)}" alt="" loading="lazy" onerror="this.parentElement.innerHTML='<div class=\\'card-image-placeholder\\'>${CAT_LABELS[c.category] || c.category.toUpperCase()}</div>'">`
    : `<div class="card-image-placeholder">${CAT_LABELS[c.category] || c.category.toUpperCase()}</div>`;

  return `
    <article class="card" data-cat="${c.category}">
      <div class="card-image">${img}</div>
      <div class="card-meta">
        <span class="cat-pill cat-${c.category}">${CAT_LABELS[c.category] || c.category}</span>
        ${c.breaking ? '<span class="breaking-pill">BREAKING</span>' : ''}
        ${renderImportanceDots(c.importance)}
        <span class="source-name">${escapeHtml(c.source_name)}</span>
        <span class="age">${timeAgo(c.published_at)}</span>
      </div>
      <h2 class="card-headline">${escapeHtml(c.headline)}</h2>
      <p class="card-body">${escapeHtml(c.body)}</p>
      ${c.why_it_matters ? `<div class="why-it-matters"><strong>WHY IT MATTERS · </strong>${escapeHtml(c.why_it_matters)}</div>` : ''}
      <div class="card-actions">
        <a href="${escapeAttr(c.source_url)}" target="_blank" rel="noopener" class="btn btn-primary">Read source →</a>
        <button class="btn" onclick="shareCard('${c.id}')">Share</button>
      </div>
    </article>
  `;
}

function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function escapeAttr(s) {
  return escapeHtml(s);
}

function renderFeed() {
  const filtered = activeCategory === 'all'
    ? allCards
    : allCards.filter(c => c.category === activeCategory);

  if (filtered.length === 0) {
    feed.innerHTML = `
      <div class="empty">
        <h2>No cards in this category yet</h2>
        <p>Run <code>python build_cards.py</code> to fetch the latest stories.</p>
      </div>
    `;
    countEl.textContent = '0 cards';
    return;
  }
  feed.innerHTML = filtered.map(renderCard).join('');
  feed.scrollTop = 0;
  countEl.textContent = `${filtered.length} cards`;
}

function shareCard(id) {
  const card = allCards.find(c => c.id === id);
  if (!card) return;
  const text = `${card.headline}\n\n${card.body}\n\n${card.source_url}\n\nvia fintech-inshorts`;
  if (navigator.share) {
    navigator.share({ text, url: card.source_url, title: card.headline }).catch(() => {});
  } else {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!');
    });
  }
}

tabs.addEventListener('click', (e) => {
  if (!e.target.matches('.tab')) return;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  e.target.classList.add('active');
  activeCategory = e.target.dataset.cat;
  renderFeed();
});

async function load() {
  try {
    // cache-bust so reloads pick up freshly-built cards
    const res = await fetch('cards.json?t=' + Date.now());
    if (!res.ok) throw new Error('cards.json not found');
    const payload = await res.json();
    allCards = payload.cards || [];
    const generated = new Date(payload.generated_at);
    meta.textContent = `${allCards.length} cards · updated ${timeAgo(payload.generated_at)}`;
    renderFeed();
  } catch (err) {
    feed.innerHTML = `
      <div class="empty">
        <h2>No cards loaded yet</h2>
        <p>Run <code>python build_cards.py</code> in the project root.</p>
        <p style="margin-top:8px;font-size:11px;">${escapeHtml(err.message)}</p>
      </div>
    `;
    meta.textContent = 'no data';
  }
}

window.shareCard = shareCard;
load();
