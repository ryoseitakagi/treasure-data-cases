from pathlib import Path
import re

path = Path(__file__).resolve().parents[1] / 'template.html'
text = path.read_text(encoding='utf-8')

# Replace the hand-authored card block with a build marker. The current UI,
# styles and side panel remain the presentation template.
grid_start = text.index('<div class="grid" id="grid">')
no_results = text.index('  <div class="no-results"', grid_start)
text = (
    text[:grid_start]
    + '<div class="grid" id="grid">\n'
    + '  <!-- CASES_START -->\n'
    + '  <!-- CASES_END -->\n\n'
    + text[no_results:]
)

# Counts are written by build_site.py; never leave a stale hard-coded 46.
text = text.replace(
    '<div class="stat-number" id="visible-count">46</div>',
    '<div class="stat-number" id="visible-count">0</div>',
)
text = text.replace(
    '<div class="stat-number">46</div><div class="stat-label">総事例数</div>',
    '<div class="stat-number" id="total-count">0</div><div class="stat-label">総事例数</div>',
)
text = text.replace(
    '<p>treasure.ai/ja/customers 掲載事例 ― 業界 × 製品・機能で絞り込み（2026年6月時点）</p>',
    '<p>treasure.ai/ja/customers 掲載事例 ― 業界 × 製品・機能で絞り込み（<span id="sync-date">自動同期</span>）</p>',
)

# Long explanatory pills should wrap inside the same rounded pill instead of
# being clipped with an ellipsis or overflowing the purple band.
text = text.replace('white-space: nowrap;\n    }\n    .metric::before', 'white-space: normal;\n      line-height: 1.35;\n      overflow-wrap: anywhere;\n    }\n    .metric::before', 1)
text = text.replace(
    '    .card.hidden { display: none; }',
    '    .card.hidden { display: none; }\n    .card.unlinked .company-name::after { content: ""; }\n    .unlinked-note { font-size: .68rem; color: #9ca3af; margin-top: 2px; }',
)

# Prefer generated case data over the legacy background map.
text = text.replace(
    'var url = card.href || card.dataset.url || \'#\';',
    'var url = card.href || card.dataset.url || \'\';',
)
text = text.replace(
    "var bg = (typeof BACKGROUNDS !== 'undefined' ? BACKGROUNDS[slug] : '') || '';",
    "var bg = card.dataset.background || ((typeof BACKGROUNDS !== 'undefined' ? BACKGROUNDS[slug] : '') || '');",
)
text = text.replace(
    '    document.getElementById(\'panel-link\').href = url;\n',
    "    var panelLink = document.getElementById('panel-link');\n    panelLink.href = url || '#';\n    panelLink.style.display = url ? '' : 'none';\n",
)

# Make the count reflect the actual generated card set on first load.
text = text.replace(
    "  var countEl = document.getElementById('visible-count');\n  var searchEl",
    "  var countEl = document.getElementById('visible-count');\n  var totalEl = document.getElementById('total-count');\n  var searchEl",
)
text = text.replace(
    "  var activeProds = new Set();\n",
    "  var activeProds = new Set();\n  if (totalEl) totalEl.textContent = cards.length;\n  if (countEl) countEl.textContent = cards.length;\n",
)

# Case data now contains the full source context used by the chatbot.
text = text.replace(
    "      bg:      (typeof BACKGROUNDS !== 'undefined' && card.dataset.slug ? BACKGROUNDS[card.dataset.slug] : '') || '',\n      summary: card.dataset.summary || '',",
    "      bg:      card.dataset.background || ((typeof BACKGROUNDS !== 'undefined' && card.dataset.slug ? BACKGROUNDS[card.dataset.slug] : '') || ''),\n      summary: card.dataset.summary || '',\n      context: card.dataset.context || '',\n      catchcopy: card.dataset.catchcopy || '',\n      badges: (card.dataset.badges || '').split('|').filter(Boolean),",
)

start = text.index('  // 業種・製品の日本語→キー変換マップ')
end = text.index('  function addMsg', start)
new_chat = r'''  // 業種・製品・課題の概念辞書。単語が完全一致しない質問にも対応する。
  var IND_LABEL = {it:'IT・テクノロジー',media:'メディア・通信',finance:'金融・保険',retail:'流通・小売',ec:'EC',food:'飲食',consumer:'消費財',fashion:'ファッション',auto:'自動車・モビリティ',transport:'運輸・交通',health:'医療・ヘルスケア',entertain:'エンタメ・スポーツ',energy:'エネルギー',realestate:'不動産'};
  var PROD_LABEL = {cdp:'CDP',engage:'Engage Studio',journey:'Journey',ai_agent:'AI Agent Foundry',cleanroom:'Data Clean Room',audience:'Audience Studio'};
  var IND_ALIAS = {
    '金融':'finance','金融業':'finance','銀行':'finance','保険':'finance','証券':'finance',
    'メディア':'media','通信':'media','テレビ':'media','新聞':'media',
    '製造':'it','メーカー':'consumer','自動車':'auto','モビリティ':'auto','車':'auto',
    '小売':'retail','流通':'retail','ファッション':'fashion','アパレル':'fashion',
    'ec':'ec','通販':'consumer','消費財':'consumer','飲食':'food','食品':'food',
    '医療':'health','ヘルスケア':'health','製薬':'health',
    'エンタメ':'entertain','スポーツ':'entertain','エンターテイメント':'entertain',
    'エネルギー':'energy','電力':'energy','不動産':'realestate',
    '運輸':'transport','交通':'transport','鉄道':'transport',
    'it':'it','テクノロジー':'it'
  };
  var PROD_ALIAS = {
    'cdp':'cdp','顧客データ基盤':'cdp','データ基盤':'cdp','顧客データ':'cdp',
    'engage':'engage','engage studio':'engage','エンゲージ':'engage',
    'journey':'journey','ジャーニー':'journey','カスタマージャーニー':'journey',
    'ai agent':'ai_agent','aiエージェント':'ai_agent','生成ai':'ai_agent','foundry':'ai_agent',
    'クリーンルーム':'cleanroom','cleanroom':'cleanroom','データクリーンルーム':'cleanroom',
    'オーディエンス':'audience','audience studio':'audience'
  };
  var CONCEPT_GROUPS = [
    {label:'データ統合・サイロ解消', terms:['データサイロ','データが分散','顧客データの分散','顧客情報の分散','データ分断','部門ごと','システムが分かれ','バラバラ','分断','名寄せ','顧客id','データ統合','一元化']},
    {label:'業務工数削減・自動化', terms:['工数削減','時間削減','人手を減ら','省力化','自動化','効率化','業務効率','エンジニアへの依頼','sql','リードタイム','手作業','属人化','人海戦術']},
    {label:'パーソナライズ・顧客理解', terms:['パーソナライズ','一人ひとり','顧客理解','顧客の解像度','one to one','ワントゥワン','最適なタイミング','顧客体験','レコメンド','セグメント']},
    {label:'新規顧客獲得・広告改善', terms:['新規顧客','新規獲得','広告効率','広告最適化','roas','cpa','アッパーファネル','リターゲティング','潜在顧客']},
    {label:'継続購入・ファン化', terms:['ファン化','ロイヤルティ','ltv','リピート','継続購入','解約','離脱','休眠','再購入','f2転換']},
    {label:'AI活用・内製化', terms:['生成ai','aiエージェント','ai agent','自律','内製化','データ活用の民主化','非エンジニア','自走','経営判断']},
    {label:'営業・セールス変革', terms:['営業効率','営業活動','訪問準備','商談','インサイドセールス','リード育成','営業支援','情報武装化']}
  ];

  function normalize(value) {
    return (value || '').normalize('NFKC').toLowerCase().replace(/[\s　]+/g, '');
  }
  function escapeHtml(value) {
    return String(value || '').replace(/[&<>"']/g, function(ch) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch];
    });
  }
  function uniqueValues(values) {
    return values.filter(function(value, index, arr) { return value && arr.indexOf(value) === index; });
  }
  function expandQuery(q) {
    var normalized = normalize(q);
    var keys = [];
    Object.keys(IND_ALIAS).forEach(function(alias) { if (normalized.includes(normalize(alias))) keys.push(IND_ALIAS[alias]); });
    Object.keys(PROD_ALIAS).forEach(function(alias) { if (normalized.includes(normalize(alias))) keys.push(PROD_ALIAS[alias]); });
    return { normalized: normalized, keys: uniqueValues(keys) };
  }
  function labelForIndustry(inds) {
    return (inds || '').split(' ').map(function(i) { return IND_LABEL[i] || i; }).filter(Boolean).join(' / ');
  }
  function labelForProduct(prods) {
    return (prods || '').split(' ').map(function(p) { return PROD_LABEL[p] || p; }).filter(Boolean).join(' / ');
  }
  function scoreCard(c, q) {
    var query = expandQuery(q);
    var text = normalize([
      c.company, c.sub, c.search, c.desc, c.bg, c.summary, c.context,
      c.inds, c.prods, c.catchcopy
    ].concat(c.metrics || []).concat(c.results || []).concat(c.badges || []).join(' '));
    var score = 0;
    var reasons = [];
    var qTokens = q.normalize('NFKC').toLowerCase().split(/[\s、。,．・／/「」『』（）()!?！？]+/).filter(function(t) { return t.length >= 2; });

    query.keys.forEach(function(key) {
      var hasField = (c.inds || '').split(' ').indexOf(key) >= 0 || (c.prods || '').split(' ').indexOf(key) >= 0;
      if (hasField) score += 7;
    });
    CONCEPT_GROUPS.forEach(function(group) {
      var qHit = group.terms.some(function(term) { return query.normalized.includes(normalize(term)); });
      var cHit = group.terms.some(function(term) { return text.includes(normalize(term)); });
      if (qHit && cHit) { score += 6; reasons.push(group.label); }
    });
    qTokens.forEach(function(token) {
      if (text.includes(normalize(token))) score += token.length >= 4 ? 2 : 1;
    });
    if (query.normalized.length >= 3 && text.includes(query.normalized)) score += 10;
    if (c.company && query.normalized.includes(normalize(c.company))) score += 12;
    return { score: score, reasons: uniqueValues(reasons) };
  }

  function buildAnswer(q) {
    var ql = normalize(q);
    if (/全部|全件|すべて|一覧|リスト/.test(ql)) return '現在 <strong>' + caseData.length + '件</strong> の事例が登録されています。';
    var ranked = caseData.map(function(c) {
      var scored = scoreCard(c, q);
      return { c: c, s: scored.score, reasons: scored.reasons };
    }).filter(function(x) { return x.s > 0; }).sort(function(a, b) {
      return b.s - a.s || (a.c.featured === b.c.featured ? 0 : (a.c.featured ? -1 : 1));
    }).slice(0, 5);
    if (!ranked.length) return '「' + escapeHtml(q) + '」に近い事例が見つかりませんでした。<br>「データがバラバラ」「工数を減らしたい」「ファン化」「広告改善」など、課題や目的で試してみてください。';

    var lines = ranked.map(function(item) {
      var c = item.c;
      var name = escapeHtml(c.company || c.slug);
      var sub = c.sub ? '（' + escapeHtml(c.sub) + '）' : '';
      var why = item.reasons.length ? item.reasons.slice(0, 2).join('・') : '事例本文の課題・成果と質問が一致';
      var summary = c.summary || c.description || c.background || '';
      var result = uniqueValues((c.metrics || []).concat(c.results || [])).slice(0, 3).join(' / ');
      var link = c.url ? '<br><a href="' + escapeHtml(c.url) + '" target="_blank" rel="noopener">詳細を見る ↗</a>' : '<br><span style="color:#9ca3af">公式詳細ページは未確認</span>';
      return '<strong>' + name + '</strong>' + sub + '<br>関連理由：' + escapeHtml(why) + '<br>📋 ' + escapeHtml(summary.slice(0, 180)) + (result ? '<br>📊 ' + escapeHtml(result) : '') + '<br>🔧 ' + escapeHtml(labelForProduct(c.prods) || '製品情報を確認中') + link;
    });
    return ranked.length + '件の関連事例が見つかりました：<br><br>' + lines.join('<br><br>');
  }

'''
text = text[:start] + new_chat + text[end:]
path.write_text(text, encoding='utf-8')
print('prepared template:', path)
