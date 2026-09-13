const evidence = require("../evidence.json");

const MODELS = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "llama-3.1-8b-instant"];
const STOP = new Set("a an the and or but if then than that this these those i you he she it we they me my your is are was were be been am do does did not no so of in on at to for with about into over after from by as".split(" "));
const RE = {
  email: /[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/g,
  url: /http\S+|www\.\S+/g,
  phone: /\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
  risk: /\b(?:hack\w*|stol\w*|steal\w*|fraud\w*|lawyer\w*|legal\w*|sue\w*|suing|unauthoriz\w*|compromis\w*|phish\w*|scam\w*|threat\w*|fuck\w*|shit\w*|bitch\w*|kill\w*)\b/i,
};

function redact(t) { return t.replace(RE.email, "[EMAIL]").replace(RE.url, "[URL]").replace(RE.phone, "[PHONE]"); }
function tokens(t) { return (t.toLowerCase().match(/[a-z0-9']+/g) || []).filter(w => w.length > 2 && !STOP.has(w)); }
function lexicalTop(query, k = 3) {
  const q = new Set(tokens(query));
  if (!q.size) return [];
  const scored = [];
  for (const doc of evidence) {
    const dt = tokens(doc);
    let hit = 0;
    for (const w of dt) if (q.has(w)) hit++;
    if (hit) scored.push([hit / Math.sqrt(q.size * dt.length), doc]);
  }
  scored.sort((a, b) => b[0] - a[0]);
  return scored.slice(0, k).map(s => ({ score: +s[0].toFixed(3), text: s[1] }));
}
async function groq(key, messages, jsonMode) {
  let last;
  for (const model of MODELS) {
    try {
      const r = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: { "content-type": "application/json", authorization: "Bearer " + key },
        body: JSON.stringify({ model, messages, temperature: 0, ...(jsonMode ? { response_format: { type: "json_object" } } : {}) }),
      });
      if (r.status === 429) { last = new Error("429 on " + model); continue; }
      if (!r.ok) { last = new Error(model + " http " + r.status); continue; }
      const data = await r.json();
      return { content: data.choices[0].message.content, model };
    } catch (e) { last = e; }
  }
  throw last || new Error("all models failed");
}

module.exports = async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  const tweet = ((req.body && req.body.tweet) || "").trim();
  if (!tweet || tweet.length > 500) return res.status(400).json({ error: "provide a tweet of 1-500 chars" });
  const key = process.env.GROQ_API_KEY;
  if (!key) return res.status(500).json({ error: "GROQ_API_KEY not configured on server" });

  const safe = redact(tweet);
  const reasons = [];
  if (RE.risk.test(safe)) reasons.push("high-risk keyword (deterministic backstop)");
  if (/cancel/i.test(safe) && /\b(?:can't|cannot|cant|unable|won't|wont)\b/i.test(safe)) reasons.push("cancellation dead-end");

  const [intentCall, riskCall] = await Promise.all([
    groq(key, [
      { role: "system", content: 'Classify into ONE: app_bug, account_login, billing_payment, feature_request, other. Return ONLY JSON: {"intent": "...", "confidence": 0.0, "rationale": "..."}' },
      { role: "user", content: safe },
    ], true).catch(e => ({ content: '{"intent":"other","confidence":0.5}', model: "fallback:" + e.message })),
    groq(key, [
      { role: "system", content: 'Flag risk=true ONLY for: account compromise/hacking, fraud or unauthorized charges, legal threats, threats of violence or self-harm, severe abusive hostility. NOT ordinary frustration, bugs, billing questions, sarcasm. Return JSON only: {"risk": false} or {"risk": true}' },
      { role: "user", content: safe },
    ], true).catch(() => ({ content: '{"risk": false}', model: "fallback" })),
  ]);

  let intent = "other", confidence = 0.5, llmRisk = false;
  try { const p = JSON.parse(intentCall.content); intent = p.intent || "other"; const c = +p.confidence; confidence = Number.isFinite(c) ? c : 0.5; } catch (e) {}
  try { llmRisk = !!JSON.parse(riskCall.content).risk; } catch (e) {}
  if (llmRisk) reasons.push("LLM risk classifier flag");
  if (confidence < 0.7) reasons.push("low intent confidence (< 0.7)");
  const escalate = reasons.length > 0;

  const ev = lexicalTop(safe);
  const draft = await groq(key, [
    { role: "system", content: "You are drafting a Spotify support reply. Use only facts from the evidence. Do not invent URLs, refunds, timelines or policies. Ask for a DM if the issue requires sensitive account details. Avoid emojis unless the retrieved evidence uses them.\nEvidence:\n" + ev.map(e => "- " + e.text).join("\n") },
    { role: "user", content: "Intent: " + intent + ".\nTweet: " + safe + "\nDraft:" },
  ], false).catch(() => ({ content: "[draft unavailable - model budget exhausted]", model: "none" }));

  res.setHeader("cache-control", "no-store");
  return res.status(200).json({
    redacted: safe, intent, confidence, evidence: ev, escalate,
    reasons: escalate ? reasons : ["safe to auto-handle"],
    reply: draft.content,
    models: { intent: intentCall.model, risk: riskCall.model, draft: draft.model },
    note: "Demo policy: keyword backstop + LLM risk + confidence gate with lexical evidence. The offline pipeline adds the calibrated dense-retrieval gate (see REPORT.md).",
  });
};

