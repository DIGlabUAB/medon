(function () {
  "use strict";
  const D = window.MEDON_DATA, ORG = window.MEDON_ORG || {};
  const Q = D.questionnaire.questions, TOOL = Q.filter(q => q.type !== "status"), STAT = Q.filter(q => q.type === "status");
  const QID = {}; Q.forEach(q => { QID[q.id] = q; });
  const PHASES = D.items.phases;
  const NEUT = { function: "administrative", autonomy: "informs", model_type: "rules", source: "in_house", users: ["staff"], affects_care: "no", patient_level: "no", harm: "minimal", phi: "none", updates: "fixed", workload: "no" };
  const STEPS = ["intro"].concat(TOOL.map(q => "q:" + q.id), PHASES.map(p => "ex:" + p.id), ["results"]);
  let A = {}, P = { name: "", clinical_lead: "", date: new Date().toISOString().slice(0, 10) }, CK = {}, step = 0, OVR = "";
  const $ = id => document.getElementById(id);
  const el = (t, p, kids) => { const e = document.createElement(t); if (p) Object.keys(p).forEach(k => { if (k === "text") e.textContent = p[k]; else if (k === "on") Object.keys(p.on).forEach(ev => e.addEventListener(ev, p.on[ev])); else if (k === "data") Object.keys(p.data).forEach(d => e.dataset[d] = p.data[d]); else if (k === "attrs") Object.keys(p.attrs).forEach(a => e.setAttribute(a, p.attrs[a])); else e[k] = p[k]; }); (kids || []).forEach(c => e.append(c)); return e; };
  const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
  const split = l => { const m = /^(.*?) \((.*)\)$/.exec(l); return m ? [m[1], m[2]] : [l, ""]; };
  const save = () => { try { localStorage.setItem("medon2", JSON.stringify({ A, P, CK, step })); } catch (e) {} };
  const load = () => { try { const s = JSON.parse(localStorage.getItem("medon2")); if (s) { A = s.A || {}; P = Object.assign(P, s.P); CK = s.CK || {}; step = Math.min(s.step || 0, STEPS.length - 1); } } catch (e) {} };

  function live() {
    if (STEPS[step] === "results") return A;
    const a = {}; TOOL.forEach(q => { if (!(q.id in A)) a[q.id] = NEUT[q.id]; }); return Object.assign(a, A);
  }
  function plan() { return Medon.build(D, live(), ORG, OVR || null); }
  const eff = i => CK[i.id] ? "done" : i.status;
  function counts(p) { const c = { "done": 0, "in progress": 0, "open": 0 }; p.items.forEach(i => { c[eff(i)]++; }); return c; }

  /* ---------- stage ---------- */
  function exRows(phase) {
    const p = Medon.build(D, live(), ORG, null), seen = new Set(), out = {};
    PHASES.forEach(ph => { p.items.filter(i => i.phase === ph.id).forEach(i => { const q = i.status_q || null; });});
    const full = D.items.items;
    const byId = {}; full.forEach(i => { byId[i.id] = i; });
    PHASES.forEach(ph => { out[ph.id] = []; p.items.filter(i => i.phase === ph.id).forEach(i => { const sq = (byId[i.id] || {}).status_q; if (!sq || seen.has(sq)) { if (sq) out[ph.id].forEach(r => { if (r.q === sq) r.ids.push(i.id); }); return; } seen.add(sq); out[ph.id].push({ q: sq, ids: [i.id] }); }); });
    return out[phase] || [];
  }
  function setAns(id, v, advance) { A[id] = v; save(); renderProfile(); if (advance) setTimeout(() => go(1), 230); else renderStage(true); }

  function renderStage(keep) {
    const s = STEPS[step], st = $("stage"); const sy = st.scrollTop; st.innerHTML = "";
    if (s === "intro") {
      st.append(el("div", { className: "crumb", text: "Start" }), el("h2", { text: "Describe a clinical AI project." }),
        el("p", { className: "why", text: "Answer " + TOOL.length + " quick questions about the tool. Then say what governance already exists. Your risk profile and plan build on the right as you go." }));
      [["name", "Project or tool name"], ["clinical_lead", "Clinical lead"]].forEach(([k, l]) => { const i = el("input", { type: "text", value: P[k] || "", on: { input: () => { P[k] = i.value; save(); } } }); st.append(el("label", { className: "fld" }, [el("span", { text: l }), i])); });
      st.append(el("div", { className: "nav" }, [el("button", { className: "btn p", text: "Start", on: { click: () => go(1) } })]));
      st.append(el("p", { className: "note", text: D.disclaimer }));
    } else if (s.startsWith("q:")) {
      const q = QID[s.slice(2)], n = TOOL.indexOf(q) + 1, multi = q.type === "multi";
      st.append(el("div", { className: "crumb" }, [document.createTextNode("Question " + n), el("span", { text: "of " + TOOL.length })]), el("h2", { text: q.text }), el("p", { className: "why", text: q.why || "" }));
      const g = el("div", { className: "tiles" });
      const cur = A[q.id];
      q.options.forEach((o, k) => {
        const [m, sub] = split(o.label), on = multi ? (cur || []).includes(o.value) : cur === o.value;
        g.append(el("button", { className: "tile", style: "animation-delay:" + (k * 40) + "ms", attrs: { "aria-pressed": String(on) }, on: { click: () => { if (multi) { const sset = new Set(Array.isArray(cur) ? cur : []); sset.has(o.value) ? sset.delete(o.value) : sset.add(o.value); if (sset.size) A[q.id] = [...sset]; else delete A[q.id]; save(); renderProfile(); renderStage(true); } else setAns(q.id, o.value, true); } } },
          [el("span", { className: "k", text: String(k + 1) }), el("b", { text: m }), el("small", { text: sub })]));
      });
      if (!multi || true) g.append(el("button", { className: "tile ns", style: "animation-delay:" + (q.options.length * 40) + "ms", attrs: { "aria-pressed": String(cur === "unsure") }, on: { click: () => { A[q.id] = "unsure"; save(); renderProfile(); go(1); } } }, [el("b", { text: "Not sure" }), el("small", { text: "Counts toward a higher tier until confirmed" })]));
      st.append(g, el("div", { className: "nav" }, [el("button", { className: "btn", text: "Back", on: { click: () => go(-1) } }),
        multi ? el("button", { className: "btn p", text: "Continue", disabled: !A[q.id], on: { click: () => go(1) } }) : el("span")]));
    } else if (s.startsWith("ex:")) {
      const ph = PHASES.find(p => p.id === s.slice(3)), rows = exRows(ph.id);
      st.append(el("div", { className: "crumb" }, [document.createTextNode("What already exists"), el("span", { text: ph.title })]), el("h2", { text: ph.title }),
        el("p", { className: "why", text: rows.length ? "Is this already in place for this tool? Partly counts as in progress." : "Nothing to ask in this phase for this project." }));
      const w = el("div", { className: "rows" });
      rows.forEach((r, k) => {
        const seg = el("div", { className: "seg" });
        [["yes", "Yes"], ["partial", "Partly"], ["no", "No"], ["unsure", "Not sure"]].forEach(([v, l]) => seg.append(el("button", { text: l, attrs: { "aria-pressed": String(A[r.q] === v) }, on: { click: () => { A[r.q] = v; save(); renderProfile(); renderStage(true); } } })));
        w.append(el("div", { className: "row", style: "animation-delay:" + (k * 35) + "ms" }, [el("div", {}, [el("p", { text: QID[r.q].text }), el("div", { className: "ids", text: r.ids.join(" ") })]), seg]));
      });
      st.append(w, el("div", { className: "nav" }, [el("button", { className: "btn", text: "Back", on: { click: () => go(-1) } }), el("button", { className: "btn p", text: step === STEPS.length - 2 ? "See my plan" : "Next", on: { click: () => go(1) } })]));
    } else { renderResults(st); }
    if (keep) st.scrollTop = sy; else st.scrollTop = 0;
  }

  function go(d) {
    let n = step + d;
    while (n > 0 && n < STEPS.length - 1 && STEPS[n].startsWith("ex:") && exRows(STEPS[n].slice(3)).length === 0) n += d;
    step = Math.max(0, Math.min(STEPS.length - 1, n)); save(); renderStage(); renderProfile();
    $("pb").style.width = (step / (STEPS.length - 1) * 100) + "%";
  }

  /* ---------- profile ---------- */
  let rv = D.tiering.profile.map(() => 0), raf = 0, prevIds = new Set();
  const AX = D.tiering.profile, R = 82;
  function ang(i) { return -Math.PI / 2 + i * 2 * Math.PI / AX.length; }
  function pt(i, r) { return [Math.cos(ang(i)) * r, Math.sin(ang(i)) * r]; }
  function drawRadar(vals, p) {
    const svg = $("radar"); let h = "";
    [1, 2, 3].forEach(k => { h += '<polygon points="' + AX.map((_, i) => pt(i, R * k / 3).join(",")).join(" ") + '" fill="none" stroke="currentColor" stroke-opacity="' + (k === 3 ? .35 : .16) + '"/>'; });
    AX.forEach((a, i) => { const e = pt(i, R); h += '<line x1="0" y1="0" x2="' + e[0] + '" y2="' + e[1] + '" stroke="currentColor" stroke-opacity=".16"/>';
      const l = pt(i, R + 16); h += '<text x="' + l[0] + '" y="' + (l[1] + 3) + '" text-anchor="' + (Math.abs(l[0]) < 6 ? "middle" : l[0] > 0 ? "start" : "end") + '" font-size="9.5" fill="currentColor" fill-opacity=".75" font-family="inherit">' + a.label + "</text>"; });
    const tc = { low: "#2c8a6e", moderate: "#c98a12", high: "#c2462b" }[p.tier];
    h += '<polygon points="' + vals.map((v, i) => pt(i, R * v / 3).join(",")).join(" ") + '" fill="' + tc + '" fill-opacity=".22" stroke="' + tc + '" stroke-width="1.6" stroke-linejoin="round"/>';
    vals.forEach((v, i) => { const q = AX[i].q, pr = p.profile[i], answered = q in A; const c = pt(i, R * v / 3);
      h += '<circle cx="' + c[0] + '" cy="' + c[1] + '" r="3.6" fill="' + (answered && !pr.unsure ? tc : "var(--bg)") + '" stroke="' + tc + '" stroke-width="1.4" ' + (answered ? "" : 'stroke-dasharray="2 2" stroke-opacity=".6"') + "/>"; });
    svg.innerHTML = h;
  }
  function tween(target, p) { cancelAnimationFrame(raf); const from = rv.slice(), t0 = performance.now(), dur = matchMedia("(prefers-reduced-motion:reduce)").matches ? 1 : 420;
    const f = now => { const t = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - t, 3); rv = from.map((v, i) => v + (target[i] - v) * e); drawRadar(rv, p); if (t < 1) raf = requestAnimationFrame(f); }; raf = requestAnimationFrame(f); }
  function renderProfile() {
    const p = plan(), nA = TOOL.filter(q => q.id in A).length, final = STEPS[step] === "results";
    $("tw").textContent = p.tier; $("tw").dataset.t = p.tier; $("hp").textContent = "tier: " + p.tier; $("hp").dataset.t = p.tier;
    const rank = ["low", "moderate", "high"].indexOf(p.tier);
    [...$("mt").children].forEach((c, i) => { c.className = i <= rank ? "on" : ""; c.dataset.t = p.tier; });
    $("provl").textContent = final ? "final" : nA < TOOL.length ? "provisional " + nA + " of " + TOOL.length : "complete";
    $("why").textContent = p.tier_overridden ? "Set by override. Computed tier: " + p.tier_computed + "." : nA === 0 ? "Answer the questions to build the profile." : p.tier_why.length ? "" : "No higher tier rule matched.";
    const dv = $("drv"); dv.innerHTML = ""; if (!p.tier_overridden) p.tier_why.slice(0, 5).forEach((w, i) => dv.append(el("span", { text: w.replace(" (unanswered or unsure)", " (unsure)"), style: "animation-delay:" + i * 50 + "ms" })));
    tween(p.profile.map((x, i) => (AX[i].q in A) ? x.score : 0), p);
    // tiles
    const g = $("grid"), ids = new Set(p.items.map(i => i.id)); g.innerHTML = "";
    let lastPh = null;
    p.items.forEach(i => {
      if (i.phase !== lastPh) { lastPh = i.phase; g.append(el("div", { className: "phase", text: PHASES.find(x => x.id === i.phase).title })); }
      const t = el("button", { className: "pt", data: { s: eff(i) }, on: { click: () => openItem(i.id) } }, [el("span", { className: "i", text: i.id }), el("span", { className: "t", text: i.title })]);
      if (prevIds.has(i.id)) t.style.animation = "none"; g.append(t);
    });
    prevIds = ids; $("n").textContent = p.total;
    $("pb").style.width = (step / (STEPS.length - 1) * 100) + "%";
  }
  function openItem(id) {
    const i = plan().items.find(x => x.id === id), d = $("dlg"); if (!i) return; d.innerHTML = "";
    d.append(el("h4", { text: i.id + "  " + i.title }), el("p", {}, [el("b", { text: "Do " }), document.createTextNode(i.action)]), el("p", {}, [el("b", { text: "Evidence " }), document.createTextNode(i.evidence)]),
      el("p", {}, [el("b", { text: "Owner " }), document.createTextNode(i.owner || "Set by local policy (" + i.owner_role.replace(/_/g, " ") + ")")]));
    if (i.frequency_needed) d.append(el("p", {}, [el("b", { text: "Frequency " }), document.createTextNode(i.frequency || "Set by local policy")]));
    d.append(el("p", {}, [el("b", { text: "Source " }), document.createTextNode(i.sources.length ? "" : "none. Local consideration, not required by an encoded document.")]));
    i.sources.forEach(s => d.append(el("p", { text: s.framework + " " + s.clause + " (" + s.id + "): " + s.requirement })));
    d.append(el("div", { className: "nav" }, [el("button", { className: "btn", text: "Close", on: { click: () => d.close() } })])); d.showModal();
  }

  /* ---------- results ---------- */
  let F_PH = "all", F_ST = "all";
  function usedControls(p) { const u = {}; p.items.forEach(i => i.sources.forEach(s => { u[s.id] = s; })); return Object.keys(u).sort().map(k => u[k]); }
  function fwRefs() { const f = D.sources.frameworks; return Object.keys(f).map(k => f[k].cite); }
  function ownerOf(i) { return i.owner || "Set by local policy (role: " + i.owner_role.replace(/_/g, " ") + ")"; }
  function mdText(p) {
    const c = counts(p), L = ["# Governance plan: " + (P.name || "Unnamed project"), ""];
    if (ORG.organization) L.push("- Organization: " + ORG.organization); if (P.clinical_lead) L.push("- Clinical lead: " + P.clinical_lead);
    L.push("- Date: " + P.date, "- Risk tier: **" + p.tier + "**" + (p.tier_overridden ? " (override; computed " + p.tier_computed + ")" : ""));
    if (p.tier_why.length && !p.tier_overridden) L.push("- Tier reasons: " + p.tier_why.join("; "));
    L.push("- Items: " + p.total + " (" + c.done + " done, " + c["in progress"] + " in progress, " + c.open + " open)", "", D.disclaimer, "");
    PHASES.forEach(ph => { const its = p.items.filter(i => i.phase === ph.id); if (!its.length) return; L.push("## " + ph.title, "");
      its.forEach(i => { L.push("- [" + (eff(i) === "done" ? "x" : " ") + "] **" + i.id + " " + i.title + "** (" + eff(i) + ")" + (i.confirm ? " Confirm: depends on an unsure answer." : ""), "  - Do: " + i.action, "  - Evidence: " + i.evidence, "  - Owner: " + ownerOf(i));
        if (i.frequency_needed) L.push("  - Frequency: " + (i.frequency || "Set by local policy")); if (i.local_policy) L.push("  - Local policy: " + i.local_policy);
        L.push("  - Source: " + (i.sources.length ? i.sources.map(s => s.framework + " " + s.clause + " (" + s.id + ")").join("; ") : "none. Local consideration, not required by an encoded document.")); }); L.push(""); });
    L.push("## References", ""); fwRefs().forEach((r, k) => L.push((k + 1) + ". " + r)); L.push("", "### Clauses cited", "");
    usedControls(p).forEach(s => L.push("- " + s.id + " " + s.framework + " " + s.clause + ": " + s.requirement + " (status: " + s.status + ")")); return L.join("\n");
  }
  function csvText(p) { const q = s => '"' + String(s).replace(/"/g, '""') + '"';
    return ["id,phase,item,status,owner,frequency,action,evidence,sources"].concat(p.items.map(i => [i.id, i.phase, i.title, eff(i), ownerOf(i), i.frequency_needed ? (i.frequency || "Set by local policy") : "", i.action, i.evidence, i.sources.map(s => s.framework + " " + s.clause + " (" + s.id + ")").join("; ") || "none"].map(q).join(","))).join("\n"); }
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  function htmlText(p) {
    const c = counts(p), total = p.total, items = p.items, R = D.report, fws = Object.values(D.sources.frameworks), fcol = {};
    fws.forEach((f, k) => { fcol[f.short] = R.fwcol[k % R.fwcol.length]; });
    const cover = {}; items.forEach(i => { new Set(i.sources.map(s => s.framework)).forEach(f => { cover[f] = (cover[f] || 0) + 1; }); });
    const st = i => eff(i), ptn = (i, r, n) => { const th = -Math.PI / 2 + 2 * Math.PI * i / n; return [r * Math.cos(th), r * Math.sin(th)]; };
    const circ = 2 * Math.PI * 46; let off = 0, segs = "";
    [["done", "var(--done)"], ["in progress", "var(--prog)"], ["open", "var(--open)"]].forEach(([k, col]) => { const ln = total ? circ * c[k] / total : 0; segs += '<circle cx="60" cy="60" r="46" fill="none" stroke="' + col + '" stroke-width="14" stroke-dasharray="' + ln.toFixed(2) + " " + (circ - ln).toFixed(2) + '" stroke-dashoffset="' + (-off).toFixed(2) + '" transform="rotate(-90 60 60)"/>'; off += ln; });
    const donut = '<svg class="dn" viewBox="0 0 120 120"><circle cx="60" cy="60" r="46" fill="none" stroke="var(--line)" stroke-width="14"/>' + segs + '<text x="60" y="62" text-anchor="middle" font-size="22" font-weight="600" fill="currentColor">' + (total ? Math.round(100 * c.done / total) : 0) + '%</text><text x="60" y="76" text-anchor="middle" font-size="8" fill="var(--mut)">DONE</text></svg><div class="lg"><span><i style="background:var(--done)"></i>' + c.done + ' done</span><span><i style="background:var(--prog)"></i>' + c["in progress"] + ' in progress</span><span><i style="background:var(--open)"></i>' + c.open + ' open</span></div>';
    const pr = p.profile, n = pr.length, Rr = 62, tc = { high: "var(--hi)", moderate: "var(--mo)", low: "var(--lo)" }[p.tier];
    let g = ""; [1, 2, 3].forEach(k => { g += '<polygon fill="none" stroke="var(--line)" points="' + pr.map((_, i) => ptn(i, Rr * k / 3, n).map(v => v.toFixed(1)).join(",")).join(" ") + '"/>'; });
    pr.forEach((_, i) => { const q = ptn(i, Rr, n); g += '<line x1="0" y1="0" x2="' + q[0].toFixed(1) + '" y2="' + q[1].toFixed(1) + '" stroke="var(--line)"/>'; });
    let lab = ""; pr.forEach((x, i) => { const q = ptn(i, Rr + 14, n); lab += '<text x="' + q[0].toFixed(1) + '" y="' + (q[1] + 3).toFixed(1) + '" text-anchor="' + (Math.abs(q[0]) < 6 ? "middle" : q[0] > 0 ? "start" : "end") + '" font-size="8.5" fill="var(--mut)">' + esc(x.label) + "</text>"; });
    const radar = '<svg viewBox="-150 -92 300 184">' + g + '<polygon points="' + pr.map((x, i) => ptn(i, Rr * x.score / 3, n).map(v => v.toFixed(1)).join(",")).join(" ") + '" fill="' + tc + '" fill-opacity=".25" stroke="' + tc + '" stroke-width="1.6"/>' + lab + "</svg>";
    let phr = ""; PHASES.forEach(ph => { const its = items.filter(i => i.phase === ph.id); if (!its.length) return; const seg = [["done", "done"], ["in progress", "prog"], ["open", "open"]].map(([k, v]) => '<span style="width:' + (100 * its.filter(i => st(i) === k).length / its.length).toFixed(1) + '%;background:var(--' + v + ')"></span>').join(""); phr += '<div class="bar"><span>' + esc(ph.title.split(" and ")[0]) + '</span><div class="t">' + seg + "</div><b>" + its.length + "</b></div>"; });
    const fwr = Object.keys(cover).sort((a, b) => cover[b] - cover[a]).map(k => '<div class="bar"><span>' + esc(k) + '</span><div class="t"><span style="width:' + (100 * cover[k] / total).toFixed(1) + '%;background:' + (fcol[k] || "#607080") + '"></span></div><b>' + cover[k] + "</b></div>").join("");
    const meta = [ORG.organization, P.clinical_lead && "Lead: " + P.clinical_lead, P.date].filter(Boolean).join(" / ");
    let b = '<div class="pg"><div class="top"><span class="mono">Governance plan</span><span class="tier ' + p.tier + '">' + p.tier + ' tier</span><span class="mono">' + esc(meta) + "</span></div><h1>" + esc(P.name || "Unnamed project") + "</h1>";
    if (p.tier_why.length && !p.tier_overridden) b += '<div class="chips">' + p.tier_why.map(w => '<span class="chip">' + esc(w) + "</span>").join("") + "</div>";
    b += '<div class="viz"><div class="box"><h3>Status</h3>' + donut + '</div><div class="box"><h3>Risk profile</h3>' + radar + '</div><div class="box"><h3>Items by phase</h3>' + phr + '<h3 style="margin-top:12px">Items citing each framework</h3>' + fwr + "</div></div>";
    const nx = items.filter(i => st(i) !== "done").slice(0, 5);
    if (nx.length) b += '<div class="box next"><h3>Start here</h3><ol>' + nx.map(i => '<li><span class="id" style="display:inline-block">' + i.id + "</span>" + esc(i.title) + "</li>").join("") + "</ol></div>";
    PHASES.forEach(ph => { const its = items.filter(i => i.phase === ph.id); if (!its.length) return; b += "<h2><span>" + esc(ph.title) + "</span><span>" + its.filter(i => st(i) === "done").length + " of " + its.length + " done</span></h2>";
      its.forEach(i => { const cls = { "done": "done", "in progress": "progress", "open": "open" }[st(i)], fw = []; i.sources.forEach(s => { if (fw.indexOf(s.framework) < 0) fw.push(s.framework); });
        const tags = '<span class="tg">' + esc(i.owner || i.owner_role.replace(/_/g, " ")) + "</span>" + (i.frequency_needed ? '<span class="tg">' + esc(i.frequency || "Set by local policy") + "</span>" : "") + fw.slice(0, 3).map(k => '<span class="tg"><span class="dot" style="background:' + (fcol[k] || "#607080") + '"></span>' + esc(k) + "</span>").join("") + (fw.length > 3 ? '<span class="tg">+' + (fw.length - 3) + "</span>" : "");
        let d = "<p><b>Do</b> " + esc(i.action) + "</p><p><b>Evidence</b> " + esc(i.evidence) + "</p>"; if (i.local_policy) d += "<p><b>Local policy</b> " + esc(i.local_policy) + "</p>"; if (i.confirm) d += '<p class="cf">Confirm: depends on an unsure answer.</p>';
        d += "<p><b>Sources</b></p><ul>" + (i.sources.map(s => "<li>" + esc(s.framework + " " + s.clause + " (" + s.id + ")") + "</li>").join("") || "<li>Local consideration. No encoded clause.</li>") + "</ul>";
        b += '<details class="it"><summary><span class="ck ' + cls + '">' + (cls === "done" ? "&#10003;" : "") + '</span><span class="id">' + i.id + '</span><span class="tt">' + esc(i.title) + '</span><span class="mt">' + tags + '</span></summary><div class="bd">' + d + "</div></details>"; }); });
    b += '<p class="note">' + esc(D.disclaimer) + '</p><h2><span>References</span></h2><ol class="refs">' + fwRefs().map(r => "<li>" + esc(r) + "</li>").join("") + "</ol></div>";
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Governance plan</title><style>' + R.css + "</style>" + R.theme_js + "<body>" + b + "</body></html>";
  }
  function download(name, text, type) { const a = el("a", { href: URL.createObjectURL(new Blob([text], { type })), download: name }); document.body.append(a); a.click(); a.remove(); }
  const slug = () => (P.name || "governance plan").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim() || "governance plan";

  function renderResults(st) {
    const p = plan(), c = counts(p);
    st.append(el("div", { className: "crumb", text: "Your plan" }), el("h2", { text: (P.name || "Governance plan") }));
    const sel = el("select", { className: "btn", on: { change: () => { OVR = sel.value; renderProfile(); renderStage(true); } } }, ["", "low", "moderate", "high"].map(v => el("option", { value: v, text: v ? "Override: " + v : "Tier: computed", selected: OVR === v })));
    st.append(el("div", { className: "sum" }, [el("div", {}, [el("b", { text: cap(p.tier) }), el("span", { text: "risk tier" })]), el("div", {}, [el("b", { text: String(p.total) }), el("span", { text: "items" })]),
      el("div", {}, [el("b", { text: String(c.done) }), el("span", { text: "done" })]), el("div", {}, [el("b", { text: String(c["in progress"]) }), el("span", { text: "in progress" })]), el("div", {}, [el("b", { text: String(c.open) }), el("span", { text: "open" })])]));
    const dl = el("div", { className: "dl" }); const fn = ext => "governance plan " + slug() + "." + ext;
    [["Checklist (Markdown)", () => download(fn("md"), mdText(p), "text/markdown")], ["Checklist (HTML)", () => download(fn("html"), htmlText(p), "text/html")], ["Spreadsheet (CSV)", () => download(fn("csv"), csvText(p), "text/csv")], ["Print or save PDF", () => window.print()], ["Plan (JSON)", () => download(fn("json"), JSON.stringify({ project: P, plan: p, disclaimer: D.disclaimer }, null, 2), "application/json")], ["Answers (JSON)", () => download("answers " + slug() + ".json", JSON.stringify({ project: P, answers: A }, null, 2), "application/json")]]
      .forEach(([l, f], k) => dl.append(el("button", { className: "btn" + (k === 0 ? " p" : ""), text: l, on: { click: f } })));
    dl.append(sel, el("label", { className: "btn" }, [document.createTextNode("Load answers"), el("input", { type: "file", accept: ".json", hidden: true, on: { change: e => { const r = new FileReader(); r.onload = () => { try { const j = JSON.parse(r.result); A = j.answers || {}; P = Object.assign(P, j.project || {}); CK = {}; save(); renderStage(); renderProfile(); } catch (x) { alert("Not a valid answers file"); } }; r.readAsText(e.target.files[0]); } } })]));
    st.append(dl);
    const bar = el("div", { className: "bar" }); [["all", "All phases"]].concat(PHASES.map(x => [x.id, x.title])).forEach(([v, l]) => bar.append(el("button", { className: "chip", text: l, attrs: { "aria-pressed": String(F_PH === v) }, on: { click: () => { F_PH = v; renderStage(true); } } })));
    ["all", "open", "in progress", "done"].forEach(v => bar.append(el("button", { className: "chip", text: v === "all" ? "Any status" : v, attrs: { "aria-pressed": String(F_ST === v) }, on: { click: () => { F_ST = v; renderStage(true); } } })));
    st.append(bar);
    const list = el("div", { className: "ck" });
    p.items.filter(i => (F_PH === "all" || i.phase === F_PH) && (F_ST === "all" || eff(i) === F_ST)).forEach((i, k) => {
      const cb = el("input", { type: "checkbox", checked: eff(i) === "done", on: { click: e => e.stopPropagation(), change: () => { if (cb.checked) CK[i.id] = true; else delete CK[i.id]; save(); renderProfile(); renderStage(true); } } });
      const d = el("details", { className: "ci", style: "animation-delay:" + Math.min(k, 12) * 30 + "ms" });
      d.append(el("summary", {}, [cb, el("span", {}, [el("span", { className: "id", text: i.id }), el("span", { className: "tt", text: i.title })]), el("span", { className: "st " + eff(i).replace(" ", ""), text: eff(i) })]));
      const bd = el("div", { className: "bd" }, [el("p", {}, [el("b", { text: "Do " }), document.createTextNode(i.action)]), el("p", {}, [el("b", { text: "Evidence " }), document.createTextNode(i.evidence)]), el("p", {}, [el("b", { text: "Owner " }), document.createTextNode(ownerOf(i))])]);
      if (i.frequency_needed) bd.append(el("p", {}, [el("b", { text: "Frequency " }), document.createTextNode(i.frequency || "Set by local policy")]));
      if (i.confirm) bd.append(el("p", { text: "Confirm: this item depends on an unsure answer." }));
      if (i.sources.length) i.sources.forEach(s => bd.append(el("blockquote", {}, [el("b", { text: s.framework + " " + s.clause + " (" + s.id + ") " }), document.createTextNode(s.requirement)]))); else bd.append(el("p", { text: "Source: none. Local consideration, not required by an encoded document." }));
      d.append(bd); list.append(d);
    });
    st.append(list);
    const refs = el("div", { className: "refs" }, [el("h3", { text: "References" })]); fwRefs().forEach((r, k) => refs.append(el("p", { text: (k + 1) + ". " + r })));
    st.append(refs, el("div", { className: "nav" }, [el("button", { className: "btn", text: "Edit answers", on: { click: () => { step = 1; save(); renderStage(); renderProfile(); } } })]), el("p", { className: "note", text: D.disclaimer }));
  }

  /* ---------- boot ---------- */
  document.addEventListener("keydown", e => {
    if (/INPUT|SELECT|TEXTAREA/.test((document.activeElement || {}).tagName || "") || $("dlg").open) return;
    const s = STEPS[step];
    if (s.startsWith("q:") && /^[1-9]$/.test(e.key)) { const q = QID[s.slice(2)], o = q.options[+e.key - 1]; if (o) { const t = document.querySelectorAll(".tile")[+e.key - 1]; if (t) t.click(); } }
    if (e.key === "Backspace" && step > 0) go(-1);
  });
  window.addEventListener("DOMContentLoaded", () => {
    load(); $("reset").onclick = () => { A = {}; CK = {}; OVR = ""; P.name = ""; P.clinical_lead = ""; prevIds = new Set(); step = 0; save(); renderStage(); renderProfile(); };
    renderStage(); renderProfile();
  });
  window.__medon = { get md() { return mdText(plan()); }, get A() { return A; }, set(a, s) { A = a; if (s !== undefined) step = s; renderStage(); renderProfile(); }, STEPS };
})();
