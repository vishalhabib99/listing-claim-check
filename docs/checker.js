// Same rules as src/listing_claim_check/checker.py, driven by the same lexicon.json.
// tests/test_parity.py runs both on every eval case and fails on any difference.
(function (root) {
  "use strict";
  const CLAUSE_END = /[.!?;,\n]/g;

  const norm = s => String(s).toLowerCase().replace(/[^a-z0-9.]/g, "");
  const empty = v => v === null || v === undefined || v === "" || (Array.isArray(v) && v.length === 0);
  const truthy = v => !(empty(v) || v === false || v === 0);

  function fill(template, m) {
    return template.replace(/\$(\d)/g, (_, n) => m[+n] || "").trim().toLowerCase();
  }

  function negated(L, text, start, end) {
    const before = text.slice(Math.max(0, start - 60), start);
    let cut = 0;
    for (const b of before.matchAll(CLAUSE_END)) cut = b.index + b[0].length;
    let words = (before.slice(cut).toLowerCase().match(/[a-z']+/g) || []);
    let lastBreak = -1;
    words.forEach((w, i) => { if (L.clause_break_words.includes(w)) lastBreak = i; });
    if (lastBreak >= 0) words = words.slice(lastBreak + 1);
    words = words.slice(-L.negation_window_words);
    if (words.some(w => L.negations_before.includes(w) || w.endsWith("n't"))) return true;
    return new RegExp(L.negation_after_regex, "i").test(text.slice(end, end + 30));
  }

  function context(text, start, end) {
    const left = (text.slice(Math.max(0, start - 30), start).match(/\S+/g) || []).slice(-2);
    const right = (text.slice(end, end + 30).match(/\S+/g) || []).slice(0, 2);
    return (left.length || right.length) ? left.concat([text.slice(start, end)], right).join(" ") : text.slice(start, end);
  }

  const canonBrand = (L, s) => { const n = norm(s); return norm(L.brand_aliases[n] || n); };
  const modelNorm = (L, s) => norm(String(s).toLowerCase().split(/\s+/).filter(w => w && !L.model_strip_words.includes(w)).join(" "));

  function judge(L, det, claimed, specifics) {
    const key = det.specific, compare = det.compare, listed = specifics[key];
    if (compare === "true") {
      return truthy(listed) ? ["SUPPORTED", "specifics: " + key + " = " + pyStr(listed)] : ["UNSUPPORTED", "specifics don't record " + key];
    }
    if (empty(listed)) return ["UNSUPPORTED", "specifics don't say anything about " + key];
    let ok;
    if (compare === "equals") ok = norm(claimed) === norm(listed);
    else if (compare === "contains") {
      const A = L.color_aliases, c = A[claimed] || claimed;
      ok = norm(String(listed).toLowerCase().split(/\s+/).filter(Boolean).map(w => A[w] || w).join(" ")).includes(norm(c));
    } else if (compare === "model") ok = modelNorm(L, listed).includes(modelNorm(L, claimed));
    else if (compare === "min") ok = parseInt(claimed, 10) <= parseInt(listed, 10);
    else if (compare === "brand") ok = canonBrand(L, claimed) === canonBrand(L, listed);
    else if (compare === "condition") ok = L.condition_allows[claimed].includes(listed);
    else if (compare === "member") ok = listed.map(x => String(x).toLowerCase()).includes(claimed);
    else if (compare === "complete") { const items = listed.map(x => String(x).toLowerCase()); ok = items.includes("original box") && items.length >= 2; }
    else throw new Error("unknown compare " + compare);
    return [ok ? "SUPPORTED" : "CONTRADICTED", "specifics: " + key + " = " + pyStr(listed)];
  }

  // Match Python's str() for the values that appear in reasons.
  function pyStr(v) {
    if (Array.isArray(v)) return "[" + v.map(x => typeof x === "string" ? "'" + x + "'" : pyStr(x)).join(", ") + "]";
    if (v === true) return "True";
    if (v === false) return "False";
    return String(v);
  }

  function check(L, specifics, title, description) {
    const text = ((title || "") + "\n" + (description || "")).trim();
    if (!text) return { decision: "REVIEW", claims: [], reason: "empty listing" };
    const taken = [], claims = [], seen = new Set();
    const overlaps = (s, e) => taken.some(([ts, te]) => s < te && ts < e);
    for (const det of L.detectors) {
      for (const pat of det.patterns) {
        for (const m of text.matchAll(new RegExp(pat.regex, "gi"))) {
          const s = m.index, e = s + m[0].length;
          if (overlaps(s, e)) continue;
          taken.push([s, e]);
          if (negated(L, text, s, e)) continue;
          const claimed = fill(pat.value, m), ident = det.attribute + "\u0000" + claimed;
          if (seen.has(ident)) continue;
          seen.add(ident);
          const [status, why] = judge(L, det, claimed, specifics);
          claims.push({ attribute: det.attribute, claimed, text: m[0], status, harm: det.harm, reason: why });
        }
      }
    }
    const backed = new Set();
    for (const v of Object.values(specifics)) {
      for (const item of (Array.isArray(v) ? v : [v])) for (const n of (pyStr(item).match(/\d+(?:\.\d+)?/g) || [])) backed.add(n);
    }
    const rule = L.unbacked_numbers;
    for (const m of text.matchAll(new RegExp(rule.regex, "g"))) {
      const s = m.index, e = s + m[0].length;
      if (overlaps(s, e) || backed.has(m[0])) continue;
      taken.push([s, e]);
      claims.push({ attribute: "number", claimed: m[0], text: context(text, s, e), status: "UNSUPPORTED", harm: rule.harm,
        reason: "the number " + m[0] + " isn't in any item specific" });
    }
    const bad = claims.filter(c => c.status !== "SUPPORTED");
    return { decision: bad.length ? "REVIEW" : "PUBLISH", claims,
      reason: bad.length ? bad.length + " claim(s) not backed by the item specifics" : "every recognized claim is backed by the item specifics" };
  }

  const api = { check };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.ListingCheck = api;
})(this);
