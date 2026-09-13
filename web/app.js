let D = null;
const $ = s => document.querySelector(s);
const pct = v => v.toFixed(2) + '%';
fetch('data/demo.json').then(r => r.json()).then(d => { D = d; render(); });

function num(label, value, unit, sub) {
  return '<div class="num"><b>' + value + (unit ? '<i>' + unit + '</i>' : '') + '</b><span>' + label + '</span><em>' + (sub || '') + '</em></div>';
}
function render() {
  const h = D.headline;
  $('#nums').innerHTML =
    num('safe auto-handle', h.auto_handle, '%', 'of 200 golden-set tickets automated') +
    num('volume false auto-handle', h.volume_false_auto, '%', 'dangerous per 100 automated (bar: 5%)') +
    num('intent macro F1', h.macro_f1, '', h.accuracy + '% accuracy vs 0.46 simple baseline');
  setThr(parseFloat($('#thr').value));
  $('#foot').innerHTML =
    'Human–judge agreement (Spearman): groundedness ' + D.agreement.groundedness + ' · safety ' + D.agreement.safety + ' · helpfulness ' + D.agreement.helpfulness +
    '. The judge is blind to hallucinated URLs — the symbolic verifier is the real guard.<br>' +
    'Live demo runs the intent/risk/draft prompts through a serverless proxy with lexical evidence and a simplified policy; all headline numbers come from the offline dense-retrieval pipeline. Most evaluation requests were served by qwen/qwen3.8-27b after gpt-oss-120b exhausted its daily token budget.<br>' +
    'Source: <a href="https://github.com/ShivamSharko/backstage-spotify-support-agent">github.com/ShivamSharko/backstage-spotify-support-agent</a>';
}
function setThr(t) {
  const auto = D.tickets.filter(x => !(x.risk_score >= t || x.kw));
  const miss = auto.filter(x => x.true_escalate).length;
  const tr = D.tickets.filter(x => x.true_escalate).length;
  $('#live').innerHTML =
    num('auto-handle', pct(auto.length / D.tickets.length * 100), '', 'of 200 real tickets answered by the AI alone') +
    num('volume false auto', auto.length ? pct(miss / auto.length * 100) : '0.00', '', 'dangerous tickets per 100 automated (target: 5 or fewer)') +
    num('risk miss', tr ? pct(miss / tr * 100) : '0.00', '', 'of the ' + tr + ' genuinely dangerous tickets wrongly automated');
  const shipped = Math.abs(t - D.headline.prob_thresh) < 0.005;
  const bubble = $('#thrval');
  bubble.style.left = (((t - 0.05) / 0.9) * 100) + '%';
  bubble.textContent = t.toFixed(2);
  bubble.className = 'thrval ' + (shipped ? '' : (t < D.headline.prob_thresh ? 'calm' : 'warn'));
  document.querySelectorAll('#live .num b').forEach(b => { b.classList.remove('pulse'); void b.offsetWidth; b.classList.add('pulse'); });
  $('#thrlabel').textContent = 'At cut-off ' + t.toFixed(2) + ': the AI automates ' + auto.length + ' of 200 tickets and lets ' + miss + ' of ' + tr + ' dangerous ones through. ' + (shipped ? 'This is the shipped operating point — the knife-edge between a paralysed system (0.45 and below automates nothing) and an unsafe one (0.55 and above misses nearly a third of risks).' : (t < D.headline.prob_thresh ? 'You are in the cautious zone: more tickets go to humans than the shipped policy.' : 'You are in the aggressive zone: automation rises but dangerous tickets slip through faster.'));
}
$('#thr').addEventListener('input', e => setThr(parseFloat(e.target.value)));

$('#run').addEventListener('click', async () => {
const ta = $('#tweet');
ta.addEventListener('input', () => { ta.style.height = 'auto'; ta.style.height = Math.min(ta.scrollHeight, 240) + 'px'; });
  const tweet = $('#tweet').value.trim();
  if (!tweet) return;
  const btn = $('#run');
  btn.disabled = true;
  $('#out').innerHTML = '<div class="stage"><span class="eyebrow">running</span>three model calls through the fallback router…</div>';
  try {
    const r = await fetch('/api/pipeline', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ tweet }) });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || ('http ' + r.status));
    $('#out').innerHTML =
      '<div class="stage"><span class="eyebrow">1 · pii redaction</span>' + j.redacted + '</div>' +
      '<div class="stage"><span class="eyebrow">2 · intent</span>' + j.intent + ' · confidence ' + j.confidence + '</div>' +
      '<div class="stage"><span class="eyebrow">3 · escalation decision</span><span class="' + (j.escalate ? 'bad' : 'ok') + '">' + (j.escalate ? 'ESCALATE' : 'AUTO-HANDLE') + '</span> — ' + j.reasons.join('; ') + '</div>' +
      '<div class="stage"><span class="eyebrow">4 · retrieved historical evidence</span>' + (j.evidence.length ? j.evidence.map(e => '<div class="ev">' + e.text.slice(0, 200) + '</div>').join('') : '<div class="ev">no lexical match — a dense-retrieval run would surface semantic neighbours</div>') + '</div>' +
      '<div class="stage"><span class="eyebrow">5 · drafted reply</span>' + j.reply + '</div>' +
      '<div class="fine">' + j.note + '<br>models: intent ' + j.models.intent + ' · risk ' + j.models.risk + ' · draft ' + j.models.draft + '</div>';
  } catch (e) {
    $('#out').innerHTML = '<div class="stage"><span class="eyebrow">error</span>' + e.message + ' — the offline numbers above still stand; see REPORT.md.</div>';
  }
  setTimeout(() => { btn.disabled = false; }, 4000);
});

