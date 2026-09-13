let D=null;
const $=s=>document.querySelector(s);
const pct=v=>(v*100).toFixed(2)+'%';
fetch('data/demo.json').then(r=>r.json()).then(d=>{D=d;render();});

function card(label,num,unit,sub){return `<div class="glass card"><div class="label">${label}</div><div class="num">${num}<small>${unit||''}</small></div><div class="sub">${sub||''}</div></div>`;}

function render(){
 const h=D.meta.headline;
 $('#hero').innerHTML=
  card('Safe auto-handle',h.auto_handle,'%','of 200 golden-set tickets automated end-to-end')+
  card('Volume false auto',h.volume_false_auto,'%','dangerous tickets per 100 auto-handled (bar: ≤5%')+
  card('Risk miss',h.risk_miss,'%','true risks auto-handled ('+ (Math.round(h.risk_miss/100*16)) +'/16)')+
  card('Risk recall',Math.round(h.recall*100),'%','of true risks caught by the engine');
 $('#metrics').innerHTML=
  card('Intent accuracy',h.accuracy,'%','macro F1 '+h.macro_f1+' vs 0.46 simple baseline')+
  card('Calibration ECE',h.ece,'','verbalized confidence, 10-bin expected calibration error')+
  card('Judge safety agree',D.meta.agreement.safety??'–','','human–judge Spearman · groundedness '+(D.meta.agreement.groundedness??'–'))+
  card('Judge groundedness',D.meta.judge_means.groundedness,'/5','safety '+D.meta.judge_means.safety+' · helpfulness '+D.meta.judge_means.helpfulness);
 drawCurve(); setThr(parseFloat($('#thr').value));
 const chips=[['all','All 200'],['esc','Escalated'],['auto','Auto-handled'],['miss','Missed risks'],['rep','With drafted reply']];
 $('#chips').innerHTML=chips.map(c=>`<div class="chip${c[0]==='all'?' on':''}" data-f="${c[0]}">${c[1]}</div>`).join('');
 $('#chips').onclick=e=>{if(!e.target.dataset.f)return;document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));e.target.classList.add('on');listTickets(e.target.dataset.f);};
 listTickets('all');
 $('#foot').innerHTML='Disclosure: '+D.meta.disclosure+'<br>Full analysis, failure modes and decision log: <a href="../REPORT.md">REPORT.md</a> · Live-modification cheat sheet: <a href="../REVIEW.md">REVIEW.md</a> · Source: <a href="https://github.com/ShivamSharko/backstage-spotify-support-agent">GitHub</a>. This demo is fully static and precomputed — no API keys, no live model calls.';
}

function escOf(t,thr){return t.risk_score>=thr||t.kw;}
function setThr(thr){
 const a=D.tickets.filter(t=>!escOf(t,thr));
 const miss=a.filter(t=>t.true_escalate).length;
 const tr=D.tickets.filter(t=>t.true_escalate).length;
 $('#live').innerHTML=
  card('Auto-handle',pct(a.length/D.tickets.length),'',a.length+' of '+D.tickets.length+' tickets')+
  card('Volume false auto',a.length?pct(miss/a.length):'0.00%','',miss+' dangerous among auto-handled')+
  card('Risk miss',tr?pct(miss/tr):'0.00%','',miss+' of '+tr+' true risks');
 $('#thrlabel').textContent='threshold = '+thr.toFixed(2)+(Math.abs(thr-D.meta.coeffs.prob_thresh)<0.005?' (shipped operating point)':'');
 moveDot(thr);
}

function drawCurve(){
 const xs=t=>(t-0.05)/0.9*100, y=v=>40-v*40;
 const p1=D.curve.map(r=>xs(r.threshold).toFixed(1)+','+y(r.auto_handle_rate).toFixed(1)).join(' ');
 const p2=D.curve.map(r=>xs(r.threshold).toFixed(1)+','+y(r.risk_miss_rate).toFixed(1)).join(' ');
 $('#svg').innerHTML=`<polyline points="${p1}" fill="none" stroke="#ffd76a" stroke-width="0.8"/><polyline points="${p2}" fill="none" stroke="#ff6b6b" stroke-width="0.8"/><circle id="dot" r="1.6" fill="#fff"/>`;
}
function moveDot(thr){
 const r=D.curve.reduce((b,c)=>Math.abs(c.threshold-thr)<Math.abs(b.threshold-thr)?c:b);
 const d=$('#dot'); if(d){d.setAttribute('cx',(thr-0.05)/0.9*100); d.setAttribute('cy',40-r.auto_handle_rate*40);}
}
$('#thr').addEventListener('input',e=>setThr(parseFloat(e.target.value)));

function listTickets(f){
 const rows=D.tickets.map((t,i)=>({t,i})).filter(({t})=>
   f==='all'||(f==='esc'&&t.pred_escalate)||(f==='auto'&&!t.pred_escalate)||
   (f==='miss'&&(!t.pred_escalate&&t.true_escalate))||(f==='rep'&&t.reply));
 $('#list').innerHTML=rows.map(({t,i})=>`<div class="row" data-i="${i}">
   <span class="badge ${(!t.pred_escalate&&t.true_escalate)?'miss':(t.pred_escalate?'esc':'auto')}">${(!t.pred_escalate&&t.true_escalate)?'MISSED RISK':(t.pred_escalate?'ESCALATE':'AUTO')}</span>
   <span style="opacity:.9">${t.text.slice(0,110)}</span></div>`).join('');
 $('#list').onclick=e=>{const r=e.target.closest('.row'); if(r)showTicket(D.tickets[+r.dataset.i]);};
}

function showTicket(t){
 let html=`<h3>"${t.text}"</h3><div class="kv">
  <span class="pill">intent: ${t.pred_intent} (true: ${t.true_intent})</span>
  <span class="pill">confidence: ${t.confidence}</span>
  <span class="pill">retrieval: ${t.retrieval_score}</span>
  <span class="pill">risk score: ${t.risk_score}</span>
  <span class="pill">decision: ${t.pred_escalate?'ESCALATE':'AUTO-HANDLE'}</span>
  <span class="pill">reason: ${t.reason}</span></div>`;
 if(t.safe_text!==t.text)html+=`<div class="sub">PII-redacted input: "${t.safe_text}"</div>`;
 if(t.evidence)html+=`<div class="label" style="margin-top:14px">Retrieved historical evidence</div>`+t.evidence.map(e=>`<div class="ev">${e.slice(0,220)}</div>`).join('');
 if(t.reply)html+=`<div class="label" style="margin-top:14px">Drafted reply (verifier violations: ${t.verifier_violations})</div><div style="margin-top:6px">${t.reply}</div>`;
 if(t.judge)html+=`<div class="kv" style="margin-top:12px"><span class="pill">judge G/S/H: ${t.judge.groundedness}/${t.judge.safety}/${t.judge.helpfulness}</span>${t.human?`<span class="pill">human G/S/H: ${t.human.groundedness}/${t.human.safety}/${t.human.helpfulness}</span>`:''}</div>`;
 $('#detail').innerHTML=html;
}

const RE={email:/[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/g,url:/http\S+|www\.\S+/g,phone:/\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
risk:/\b(?:hack\w*|stol\w*|steal\w*|fraud\w*|lawyer\w*|legal\w*|sue|sued|suing|unauthoriz\w*|compromis\w*|phish\w*|scam\w*|threat\w*)\b/i};
$('#sandbox').addEventListener('input',e=>{
 const v=e.target.value;
 const masked=v.replace(RE.email,'[EMAIL]').replace(RE.url,'[URL]').replace(RE.phone,'[PHONE]');
 const dead=/cancel/i.test(v)&&/(can't|cannot|unable|won't)/i.test(v);
 $('#sbout').innerHTML=`<span class="pill">redacted: ${masked.slice(0,90)||'—'}</span>
  <span class="pill" style="background:${RE.risk.test(v)?'rgba(255,60,60,.5)':'rgba(90,200,150,.3)'}">keyword backstop: ${RE.risk.test(v)?'ESCALATE':'clear'}</span>
  <span class="pill" style="background:${dead?'rgba(255,160,60,.45)':'rgba(255,255,255,.14)'}">dead-end rule: ${dead?'ESCALATE':'clear'}</span>`;
});

