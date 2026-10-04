// Mirror of medon/engine.py. Tested against the Python engine in tests/testweb.py.
(function (root) {
  const TIERS = ["low", "moderate", "high"];
  function norm(a) {
    const o = {};
    Object.keys(a || {}).forEach(k => { let v = a[k]; if (v === true) v = "yes"; else if (v === false) v = "no"; o[k] = v; });
    return o;
  }
  function ev(c, a, d) {
    if (!c || Object.keys(c).length === 0) return [true, false];
    if (c.all) { const r = c.all.map(x => ev(x, a, d)); return [r.every(x => x[0]), r.some(x => x[1])]; }
    if (c.any) { const r = c.any.map(x => ev(x, a, d)); return [r.some(x => x[0]), r.some(x => x[1])]; }
    if (c.d) return d[c.d];
    const v = (c.q in a) ? a[c.q] : "unsure";
    const vals = Array.isArray(v) ? v : [v];
    if (vals.includes("unsure")) return [true, true];
    if ("eq" in c) return [v === c.eq, false];
    if ("in" in c) return [c.in.includes(v), false];
    if ("has" in c) return [vals.includes(c.has), false];
    if ("has_any" in c) return [c.has_any.some(x => vals.includes(x)), false];
    throw new Error("bad condition");
  }
  function label(c) {
    if (c.d) return c.d.replace(/_/g, " ");
    const k = ["eq", "in", "has", "has_any"].find(x => x in c);
    const val = Array.isArray(c[k]) ? c[k].join(", ") : c[k];
    return c.q + " " + (k === "eq" ? "is" : k === "in" ? "is one of" : "includes") + " " + val;
  }
  function leafUnsure(c, a, d) {
    if (c.d) return d[c.d][1];
    const v = (c.q in a) ? a[c.q] : "unsure";
    return (Array.isArray(v) ? v : [v]).includes("unsure");
  }
  function explain(c, a, d) {
    if (!c || Object.keys(c).length === 0) return [];
    if (c.all) return [].concat(...c.all.map(x => explain(x, a, d)));
    if (c.any) return [].concat(...c.any.filter(x => ev(x, a, d)[0]).map(x => explain(x, a, d)));
    return [label(c) + (leafUnsure(c, a, d) ? " (unanswered or unsure)" : "")];
  }
  function build(data, answers, org, override) {
    org = org || {};
    const a = norm(answers);
    const d = {};
    Object.keys(data.tiering.derived).forEach(n => { d[n] = ev(data.tiering.derived[n], a, {}); });
    let tier = "low", unc = false, why = [];
    for (const t of data.tiering.tiers) {
      const r = ev(t.when, a, d);
      if (r[0]) { tier = t.id; unc = r[1]; why = explain(t.when, a, d); break; }
    }
    const computed = tier;
    if (override) tier = override;
    const rank = TIERS.indexOf(tier);
    const ctl = {}; data.sources.controls.forEach(c => { ctl[c.id] = c; });
    const roles = org.roles || {}, cad = org.cadence || {}, loc = org.local_policy || {};
    const items = [];
    data.items.items.concat(org.extra_items || []).forEach(it => {
      if (TIERS.indexOf(it.min_tier || "low") > rank) return;
      const r = ev(it.applies, a, d);
      if (!r[0]) return;
      let status = "open";
      if (it.status_q) status = ({ yes: "done", partial: "in progress" })[a[it.status_q]] || "open";
      const f = it.cadence ? ((cad[it.cadence] || {})[tier] || null) : null;
      items.push({
        id: it.id, phase: it.phase, title: it.title, action: it.action, evidence: it.evidence,
        owner_role: it.owner, owner: roles[it.owner] || null, frequency: f,
        frequency_needed: !!it.cadence, status: status, confirm: r[1],
        sourced: it.sourced !== false, local_policy: loc[it.id] || null,
        sources: it.sources.map(c => ({ id: c, framework: data.sources.frameworks[ctl[c].framework].short,
          clause: ctl[c].clause, requirement: ctl[c].requirement, status: ctl[c].status }))
      });
    });
    const counts = { "done": 0, "in progress": 0, "open": 0 };
    items.forEach(i => { counts[i.status]++; });
    const profile = data.tiering.profile.map(ax => { const v = (ax.q in a) ? a[ax.q] : "unsure"; const u = v === "unsure" || !(v in ax.scores);
      return { id: ax.id, label: ax.label, score: u ? 2 : ax.scores[v], unsure: u }; });
    return { profile: profile, tier: tier, tier_computed: computed, tier_overridden: !!override && override !== computed,
      tier_uncertain: unc, tier_why: why, items: items, counts: counts, total: items.length,
      unanswered: data.questionnaire.questions.filter(q => q.type !== "status" && !(q.id in a)).map(q => q.id).sort() };
  }
  root.Medon = { build: build };
  if (typeof module !== "undefined") module.exports = { build: build };
})(typeof window !== "undefined" ? window : globalThis);
