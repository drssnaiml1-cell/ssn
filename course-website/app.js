// Renders the course data (data.js) into the page and wires up the interactions.
(function () {
  const C = window.COURSE;
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const code = (s) => esc(s).replace(/\b(\w+\.py|Trainer|timm)\b/g, '<code>$1</code>');
  const mod = (id) => C.modules.find((m) => m.id === id);

  // ---- mobile nav
  const toggle = $('.nav-toggle'), nav = $('.nav');
  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open);
  });
  nav.addEventListener('click', (e) => { if (e.target.tagName === 'A') nav.classList.remove('open'); });

  // ---- module chevrons
  $('#chevrons').innerHTML = C.modules.map((m) =>
    `<li><a href="#curriculum" data-module="${m.id}"><small>Module ${m.id} &bull; Days ${m.days}</small><strong>${esc(m.title)}</strong></a></li>`).join('');
  $('#chevrons').addEventListener('click', (e) => {
    const a = e.target.closest('a[data-module]');
    if (a) selectModule(+a.dataset.module);
  });

  // ---- day grid + detail
  let current = 1;
  $('#daygrid').innerHTML = C.days.map(([d, m]) =>
    `<button class="day" role="listitem" data-day="${d}" style="background:${mod(m).color}" aria-label="Day ${d}"><small>M${m}</small>${d}</button>`).join('');
  function showDay(d) {
    current = d;
    const [day, m, topic, lab, ref] = C.days[d - 1];
    const M = mod(m);
    document.querySelectorAll('.day').forEach((b) => b.classList.toggle('active', +b.dataset.day === d));
    $('#day-detail').innerHTML = `
      <div class="dnum">${day}</div>
      <div class="dmod" style="color:${M.color}">Module ${m} &bull; ${esc(M.title)}</div>
      <h3>${esc(topic)}</h3>
      <p><b>Hands-on lab:</b> ${code(lab)}</p>
      <div class="ref">Handbook reference: ${esc(ref)}</div>
      <div class="day-nav"><button data-step="-1" ${d === 1 ? 'disabled' : ''}>&larr; ${d > 1 ? 'Day ' + (d - 1) : 'Previous day'}</button>
        <button data-step="1" ${d === 30 ? 'disabled' : ''}>${d < 30 ? 'Day ' + (d + 1) : 'Next day'} &rarr;</button></div>`;
  }
  $('#daygrid').addEventListener('click', (e) => {
    const b = e.target.closest('.day');
    if (b) { showDay(+b.dataset.day); selectModule(C.days[+b.dataset.day - 1][1], false); }
  });
  $('#day-detail').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-step]');
    if (!b) return;
    const d = Math.min(30, Math.max(1, current + +b.dataset.step));
    showDay(d); selectModule(C.days[d - 1][1], false);
  });

  // ---- module tabs + table
  $('#module-tabs').innerHTML = C.modules.map((m) =>
    `<button class="tab" role="tab" data-module="${m.id}" aria-selected="false"><small>M${m.id}</small>${esc(m.title)}</button>`).join('');
  function selectModule(id, syncDay = true) {
    document.querySelectorAll('.tab').forEach((t) => t.setAttribute('aria-selected', +t.dataset.module === id));
    const M = mod(id);
    const rows = C.days.filter((d) => d[1] === id).map(([d, , topic, lab, ref]) =>
      `<tr><td class="daycell">${d}</td><td class="topic">${esc(topic)}</td><td class="lab">${code(lab)}</td><td class="ref">${esc(ref)}</td></tr>`).join('');
    $('#module-panel').innerHTML = `
      <p class="module-summary"><b style="color:${M.color}">Module ${M.id} &bull; Days ${M.days}.</b> ${esc(M.summary)}</p>
      <div class="table-wrap"><table><thead><tr><th>Day</th><th>Topic</th><th>Hands-on lab / outcome</th><th>Handbook</th></tr></thead>
      <tbody>${rows}</tbody></table></div>`;
    if (syncDay) showDay(C.days.find((d) => d[1] === id)[0]);
  }
  $('#module-tabs').addEventListener('click', (e) => {
    const t = e.target.closest('.tab');
    if (t) selectModule(+t.dataset.module);
  });
  selectModule(1);

  // ---- architectures
  $('#arch-grid').innerHTML = C.architectures.map((a) => `
    <article class="arch">
      <h3>${esc(a.name)}<small>${esc(a.full)}</small></h3>
      <p>${esc(a.idea)}</p>
      <div class="eq">${esc(a.eq)}</div>
      <dl><dt>Data</dt><dd>${esc(a.data)}</dd><dt>Landmarks</dt><dd>${esc(a.landmark)}</dd></dl>
    </article>`).join('');

  // ---- blueprints
  $('#bp-tabs').innerHTML = C.blueprints.map((b, i) =>
    `<button class="bp-tab" role="tab" data-i="${i}" aria-selected="${i === 0}"><b style="background:${b.color}">${b.sdg}</b>${esc(b.title)}</button>`).join('');
  function showBlueprint(i) {
    const b = C.blueprints[i];
    document.querySelectorAll('.bp-tab').forEach((t) => t.setAttribute('aria-selected', +t.dataset.i === i));
    const nodes = (arr, cls) => arr.map((s) => `<div class="bp-node ${cls}">${esc(s)}</div>`).join('');
    $('#blueprint').innerHTML = `
      <h3 class="bp-title"><span style="background:${b.color};color:#fff;border-radius:4px;padding:1px 7px;margin-right:8px">${b.sdg}</span>${esc(b.title)}
        <small style="color:#6e5810;font-weight:500"> &mdash; ${esc(b.tag)}</small></h3>
      <div class="bp-flow">
        <div class="bp-col"><h4>Data sources</h4>${nodes(b.sources, 'src')}</div>
        <div class="bp-col"><h4>Ingest / stream</h4>${nodes([b.ingest], 'dark')}</div>
        <div class="bp-col"><h4>Features / store</h4>${nodes([b.store], 'store')}</div>
        <div class="bp-col"><h4>Models</h4>${nodes(b.models, 'model')}</div>
        <div class="bp-col"><h4>Serving</h4>${nodes([b.serve], 'dark')}</div>
        <div class="bp-col"><h4>Users / action</h4>${nodes(b.users, 'user')}</div>
      </div>
      <div class="bp-loop">&#8634; MLOps feedback loop: ${esc(b.loop)}</div>`;
  }
  $('#bp-tabs').addEventListener('click', (e) => {
    const t = e.target.closest('.bp-tab');
    if (t) showBlueprint(+t.dataset.i);
  });
  showBlueprint(0);

  // ---- stack
  $('#stack-list').innerHTML = C.stack.map(([layer, tools]) =>
    `<div class="stack-row"><h4>${esc(layer)}</h4><div class="chips">${tools.split(', ').map((t) => `<span class="chip">${esc(t)}</span>`).join('')}</div></div>`).join('');

  // ---- roadmap
  $('#roadmap-list').innerHTML = C.roadmap.map(([phase, months, act, del]) =>
    `<li><h4>${esc(phase)}</h4><p class="months">Months ${esc(months)}</p><p>${esc(act)}</p><p class="deliv"><b>Deliverable:</b> ${esc(del)}</p></li>`).join('');

  // ---- enquiry form -> mailto (no server needed)
  $('#enquiry').addEventListener('submit', (e) => {
    e.preventDefault();
    const f = e.target, note = $('#form-note');
    const name = f.name.value.trim(), email = f.email.value.trim();
    if (!name || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      note.textContent = 'Please enter your name and a valid email address.';
      note.classList.add('err');
      return;
    }
    note.classList.remove('err');
    const body = `Name: ${name}\nEmail: ${email}\nPhone: ${f.phone.value.trim()}\nRole: ${f.role.value}\n\n${f.message.value.trim()}`;
    window.location.href = 'mailto:ceo@algoprofessor.com?subject=' +
      encodeURIComponent('Enquiry: Neurons to MoE 30-Day Bootcamp') + '&body=' + encodeURIComponent(body);
    note.textContent = 'Your email app should open now. If it does not, write to ceo@algoprofessor.com.';
  });
})();
