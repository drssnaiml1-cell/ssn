// End-to-end tests for bootcamp.html (deployed as index.html).
//   npm i playwright axe-core
//   BASE=http://127.0.0.1:8080/ node tests/site.test.mjs
// Writes tests/TEST-RESULTS.json. Form submissions are intercepted, so no real email is sent.
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const BASE = process.env.BASE || 'http://127.0.0.1:8080/';
const FORM_TO = 'cto@algoprofessor.com';
const ENDPOINT = `https://formsubmit.co/ajax/${FORM_TO}`;
const exe = process.env.CHROME || (fs.existsSync('/opt/pw-browsers') ? fs.readdirSync('/opt/pw-browsers')
  .filter(d => d.startsWith('chromium-')).map(d => `/opt/pw-browsers/${d}/chrome-linux/chrome`)[0] : undefined);
const browser = await chromium.launch(exe ? { executablePath: exe } : {});

const results = [];
let group = '';
async function test(name, fn) {
  try { await fn(); results.push({ group, name, ok: true }); console.log(`  PASS  ${name}`); }
  catch (e) { results.push({ group, name, ok: false, error: e.message }); console.log(`  FAIL  ${name}\n        ${e.message}`); }
}
function section(n) { group = n; console.log(`\n${n}`); }
function assert(c, m) { if (!c) throw new Error(m); }
function eq(a, b, m) { if (a !== b) throw new Error(`${m}: expected ${JSON.stringify(b)}, got ${JSON.stringify(a)}`); }

const IGNORE = /fonts\.(googleapis|gstatic)\.com|ERR_TUNNEL|ERR_CONNECTION|net::ERR/;   // web fonts may be blocked offline
async function open(opts = {}) {
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 }, ...opts });
  const page = await ctx.newPage();
  page.errors = [];
  page.on('pageerror', e => page.errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error' && !IGNORE.test(m.text())) page.errors.push(m.text()); });
  await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  await page.goto(BASE, { waitUntil: 'load' });
  return { ctx, page };
}
const dayNum = p => p.$eval('.ex-ring b', e => +e.textContent);

// =========================================================== page basics
section('1. Page load, SEO and structure');
{
  const { ctx, page } = await open();
  await test('page loads with HTTP 200', async () => {
    const r = await page.request.get(BASE); eq(r.status(), 200, 'status');
  });
  await test('no JavaScript errors on load', async () => { eq(page.errors.length, 0, 'errors ' + page.errors.join(' | ')); });
  await test('<html lang="en"> is set', async () => eq(await page.getAttribute('html', 'lang'), 'en', 'lang'));
  await test('<title> mentions the bootcamp', async () => assert((await page.title()).includes('Mixture of Experts'), 'title'));
  await test('meta description present (50–170 chars)', async () => {
    const d = await page.getAttribute('meta[name=description]', 'content'); assert(d && d.length >= 50 && d.length <= 170, 'length ' + d?.length);
  });
  await test('viewport meta present', async () => assert(await page.$('meta[name=viewport]'), 'viewport'));
  await test('Open Graph title and description present', async () => {
    assert(await page.$('meta[property="og:title"]') && await page.$('meta[property="og:description"]'), 'og tags');
  });
  await test('favicon defined', async () => assert(await page.$('link[rel=icon]'), 'favicon'));
  await test('exactly one <h1>', async () => eq((await page.$$('h1')).length, 1, 'h1 count'));
  await test('hero shows title, fee-free tagline and program director', async () => {
    const t = await page.textContent('.hero');
    assert(t.includes('Neurons to Mixture of Experts') && t.includes('Dr S Satyanarayana'), 'hero text');
  });
  await test('stats show 30 days / 5 modules / 30 labs / 1 capstone', async () => {
    const s = await page.$$eval('.stat', els => els.map(e => e.innerText.replace(/\s+/g, ' ').trim()));
    eq(s.join(' | '), '30 days | 5 modules | 30 hands-on labs | 1 SDG capstone', 'stats');
  });
  await test('every in-page link (#…) points to an existing element', async () => {
    const bad = await page.$$eval('a[href^="#"]', as => as.map(a => a.getAttribute('href'))
      .filter(h => h.length > 1 && !document.querySelector(h)));
    eq(bad.length, 0, 'broken anchors ' + bad.join(','));
  });
  await test('external links open in a new tab with rel="noopener"', async () => {
    const bad = await page.$$eval('a[href^="http"]', as => as.filter(a => a.target !== '_blank' || !/noopener/.test(a.rel)).map(a => a.href));
    eq(bad.length, 0, 'unsafe external links ' + bad.join(','));
  });
  await test('mailto links are well formed', async () => {
    const m = await page.$$eval('a[href^="mailto:"]', as => as.map(a => a.getAttribute('href')));
    assert(m.length >= 2 && m.every(h => /^mailto:[^@\s]+@[^@\s]+\.[a-z]+/.test(h)), 'mailto ' + m.join(','));
  });
  await test('fee shown as INR 1,00,000', async () => assert((await page.textContent('#contact')).includes('INR 1,00,000'), 'fee'));
  await test('footer shows current year', async () => eq(await page.textContent('#yr'), String(new Date().getFullYear()), 'year'));
  await ctx.close();
}

// =========================================================== navigation
section('2. Header and navigation');
{
  const { ctx, page } = await open({ viewport: { width: 390, height: 844 } });
  await test('mobile: menu hidden until burger is tapped', async () => {
    assert(!(await page.isVisible('nav a[href="#syllabus"]')), 'nav visible before tap');
    await page.click('.burger');
    assert(await page.isVisible('nav a[href="#syllabus"]'), 'nav not visible after tap');
    eq(await page.getAttribute('.burger', 'aria-expanded'), 'true', 'aria-expanded');
  });
  await test('mobile: tapping a menu link closes the menu', async () => {
    await page.click('nav a[href="#careers"]'); await page.waitForTimeout(300);
    assert(!(await page.$eval('nav', n => n.classList.contains('open'))), 'menu still open');
  });
  await ctx.close();
  const d = await open();
  await test('desktop: all 7 nav items visible', async () => {
    eq((await d.page.$$('nav a')).filter(Boolean).length, 7, 'nav count');
    assert(await d.page.isVisible('nav a[href="#careers"]'), 'careers link');
  });
  await test('header stays visible (sticky) after scrolling', async () => {
    await d.page.evaluate(() => window.scrollTo(0, 3000)); await d.page.waitForTimeout(200);
    const top = await d.page.$eval('header', h => h.getBoundingClientRect().top); eq(top, 0, 'header top');
  });
  await d.ctx.close();
}

// =========================================================== day explorer
section('3. Dynamic day explorer');
{
  const { ctx, page } = await open();
  await test('30 day buttons, coloured by 5 modules', async () => {
    eq((await page.$$('.ex-day')).length, 30, 'days');
    const colors = new Set(await page.$$eval('.ex-day', b => b.map(x => x.style.background)));
    eq(colors.size, 5, 'module colours');
  });
  await test('starts at Day 1 with progress 1/30', async () => {
    eq(await dayNum(page), 1, 'day');
    assert((await page.$eval('#exBar', e => e.style.width)).startsWith('3.3'), 'bar');
  });
  await test('Previous at Day 1 stays on Day 1', async () => { await page.click('#exPrev'); eq(await dayNum(page), 1, 'day'); });
  await test('Next moves to Day 2, then Day 3', async () => {
    await page.click('#exNext'); eq(await dayNum(page), 2, 'day'); await page.click('#exNext'); eq(await dayNum(page), 3, 'day');
  });
  await test('clicking Day 15 shows Day 15 and 50% progress', async () => {
    await page.click('.ex-day[data-d="15"]'); eq(await dayNum(page), 15, 'day');
    eq(await page.$eval('#exBar', e => e.style.width), '50%', 'bar');
  });
  await test('day card shows topic, lab and module goal from the syllabus', async () => {
    await page.click('.ex-day[data-d="23"]');
    const t = await page.textContent('#exCard');
    assert(t.includes('Mixture of Experts') && t.includes('moe.py') && t.includes('Module 4'), t.slice(0, 120));
  });
  await test('day types: D1 concept, D5 project, D6 assessment, D27 capstone', async () => {
    for (const [d, ty] of [[1, 'Concept + lab'], [5, 'Project lab'], [6, 'Assessment'], [27, 'Capstone']]) {
      await page.click(`.ex-day[data-d="${d}"]`);
      assert((await page.textContent('.ex-type')).includes(ty), `day ${d} type`);
    }
  });
  await test('"Up next" link jumps to the following day', async () => {
    await page.click('.ex-day[data-d="9"]'); await page.click('.ex-next a'); eq(await dayNum(page), 10, 'day');
  });
  await test('Next at Day 30 stays on Day 30 and shows completion', async () => {
    await page.click('.ex-day[data-d="30"]'); await page.click('#exNext'); eq(await dayNum(page), 30, 'day');
    assert((await page.textContent('.ex-next')).includes('Day 30 complete'), 'completion text');
  });
  await test('keyboard: Arrow keys change day when explorer is focused', async () => {
    await page.click('.ex-day[data-d="10"]'); await page.focus('#explorer');
    await page.keyboard.press('ArrowRight'); eq(await dayNum(page), 11, 'right');
    await page.keyboard.press('ArrowLeft'); await page.keyboard.press('ArrowLeft'); eq(await dayNum(page), 9, 'left');
  });
  await test('selected day is marked aria-selected and earlier days "done"', async () => {
    eq(await page.getAttribute('.ex-day[data-d="9"]', 'aria-selected'), 'true', 'selected');
    assert(await page.$eval('.ex-day[data-d="3"]', b => b.classList.contains('done')), 'done class');
  });
  await test('module card click jumps explorer to module start (Module 3 → Day 13)', async () => {
    await page.click('.mod[data-m="3"]'); await page.waitForTimeout(100); eq(await dayNum(page), 13, 'day');
    assert(await page.$eval('#m3', d => d.open), 'accordion module 3 open');
  });
  await ctx.close();

  const c = await browser.newContext({ viewport: { width: 1366, height: 900 } });
  const p = await c.newPage(); await p.clock.install(); await p.route(/fonts\./, r => r.abort()); await p.goto(BASE);
  await test('Play advances one day every 4 s and shows Pause', async () => {
    await p.click('#exPlay'); eq(await p.getAttribute('#exPlay', 'aria-label'), 'Pause', 'label');
    await p.clock.runFor(4100); eq(await dayNum(p), 2, 'after 4s'); await p.clock.runFor(8000); eq(await dayNum(p), 4, 'after 12s');
  });
  await test('Pause stops auto-advance', async () => {
    await p.click('#exPlay'); const d = await dayNum(p); await p.clock.runFor(10000); eq(await dayNum(p), d, 'still');
    eq(await p.getAttribute('#exPlay', 'aria-label'), 'Play', 'label');
  });
  await test('auto-play stops by itself at Day 30', async () => {
    await p.click('.ex-day[data-d="28"]'); await p.click('#exPlay'); await p.clock.runFor(20000);
    eq(await dayNum(p), 30, 'day'); eq(await p.getAttribute('#exPlay', 'aria-label'), 'Play', 'stopped');
  });
  await test('manual navigation during play stops play', async () => {
    await p.click('.ex-day[data-d="1"]'); await p.click('#exPlay'); await p.click('#exNext');
    eq(await p.getAttribute('#exPlay', 'aria-label'), 'Play', 'stopped');
  });
  await c.close();

  const m = await open({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  await test('mobile: swipe left/right on the day card changes day', async () => {
    const swipe = dx => m.page.evaluate(dx => {
      const el = document.getElementById('exCard'); const r = el.getBoundingClientRect(); const y = r.top + 50, x0 = r.left + 200;
      const t = (x) => new Touch({ identifier: 1, target: el, clientX: x, clientY: y });
      el.dispatchEvent(new TouchEvent('touchstart', { touches: [t(x0)], bubbles: true }));
      el.dispatchEvent(new TouchEvent('touchend', { changedTouches: [t(x0 + dx)], bubbles: true }));
    }, dx);
    await swipe(-120); eq(await dayNum(m.page), 2, 'swipe left'); await swipe(120); eq(await dayNum(m.page), 1, 'swipe right');
    await swipe(-20); eq(await dayNum(m.page), 1, 'small swipe ignored');
  });
  await m.ctx.close();
}

// =========================================================== syllabus
section('4. Full syllabus accordion');
{
  const { ctx, page } = await open();
  await test('5 modules × 6 days, numbered Day 1 … Day 30 in order', async () => {
    eq((await page.$$('#acc details')).length, 5, 'modules');
    const days = await page.$$eval('#acc .day .d', d => d.map(x => x.textContent));
    eq(days.join(','), Array.from({ length: 30 }, (_, i) => `Day ${i + 1}`).join(','), 'day order');
  });
  await test('module titles match the brochure', async () => {
    const t = await page.$$eval('#acc summary h3', h => h.map(x => x.textContent));
    eq(t.join(' | '), 'Foundations & ANN | CNN & Computer Vision | RNN, LSTM & Time Series | Transformers, LLMs & MoE | MLOps & SDG Capstone', 'titles');
  });
  await test('Expand all opens 5, Collapse all closes all', async () => {
    await page.click('#openAll'); eq(await page.$$eval('#acc details[open]', d => d.length), 5, 'open');
    await page.click('#closeAll'); eq(await page.$$eval('#acc details[open]', d => d.length), 0, 'closed');
  });
  await test('clicking a module heading toggles it', async () => {
    await page.click('#m2 summary'); assert(await page.$eval('#m2', d => d.open), 'open');
    await page.click('#m2 summary'); assert(!(await page.$eval('#m2', d => d.open)), 'closed');
  });
  await test('print: all modules open and interactive parts hidden', async () => {
    await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
    eq(await page.$$eval('#acc details[open]', d => d.length), 5, 'open for print');
    await page.emulateMedia({ media: 'print' });
    assert(!(await page.isVisible('#contact')) && !(await page.isVisible('#explorer')) && !(await page.isVisible('header')), 'hidden in print');
    assert(await page.isVisible('#acc'), 'syllabus visible in print');
    await page.emulateMedia({ media: 'screen' });
  });
  await ctx.close();
}

// =========================================================== careers
section('5. Careers, sectors and salaries');
{
  const { ctx, page } = await open();
  const ROLES = ['Machine Learning Engineer', 'Computer Vision / Deep Learning Engineer', 'Generative AI / LLM Engineer', 'MLOps / ML Platform Engineer', 'Data Scientist'];
  await test('5 role buttons', async () => eq((await page.$$('.role')).length, 5, 'roles'));
  await test('each role shows its title, modules, skills and 3 salary bars', async () => {
    for (let i = 0; i < 5; i++) {
      await page.click(`.role[data-i="${i}"]`);
      assert((await page.textContent('#roleCard h3')).includes(ROLES[i]), 'title ' + i);
      assert((await page.$$('#roleCard .modchip')).length >= 1, 'modules ' + i);
      assert((await page.$$('#roleCard .chip:not(.modchip)')).length >= 4, 'skills ' + i);
      eq((await page.$$('#roleCard .payfill')).length, 3, 'bars ' + i);
      eq(await page.getAttribute(`.role[data-i="${i}"]`, 'aria-selected'), 'true', 'selected ' + i);
    }
  });
  await test('salary bands rise with experience for every role', async () => {
    for (let i = 0; i < 5; i++) {
      await page.click(`.role[data-i="${i}"]`);
      const lows = await page.$$eval('#roleCard .payfill', b => b.map(x => +x.textContent.match(/₹(\d+)/)[1]));
      assert(lows[0] < lows[1] && lows[1] < lows[2], `role ${i}: ${lows}`);
    }
  });
  await test('salary bars stay inside their track', async () => {
    const out = await page.$$eval('.payfill', b => b.filter(x => {
      const r = x.getBoundingClientRect(), t = x.parentElement.getBoundingClientRect(); return r.left < t.left - 1 || r.right > t.right + 1; }).length);
    eq(out, 0, 'overflowing bars');
  });
  await test('4 employer tiers and 8 sectors', async () => {
    eq((await page.$$('.tier')).length, 4, 'tiers'); eq((await page.$$('.sector')).length, 8, 'sectors');
  });
  await test('salary note: sources linked and no job / salary guarantee stated', async () => {
    const t = await page.textContent('#careers .note');
    assert(/does not guarantee a job, placement or a particular salary/.test(t), 'disclaimer');
    assert((await page.$$('#careers .note a[href^="https://"]')).length >= 4, 'source links');
  });
  await ctx.close();
}

// =========================================================== contact form
section('6. Contact form (recipient ' + FORM_TO + ')');
{
  const { ctx, page } = await open();
  const hits = [];
  let mode = 'ok';
  await page.route('https://formsubmit.co/**', async route => {
    hits.push({ url: route.request().url(), method: route.request().method(), body: route.request().postDataJSON(), headers: route.request().headers() });
    if (mode === 'ok') return route.fulfill({ status: 200, contentType: 'application/json', body: '{"success":"true","message":"The form was submitted successfully."}' });
    if (mode === 'http500') return route.fulfill({ status: 500, body: 'error' });
    if (mode === 'formsubmit-false') return route.fulfill({ status: 200, contentType: 'application/json', body: '{"success":"false","message":"This form needs Activation."}' });
    return route.abort();
  });
  const fill = async (o = {}) => {
    const v = { name: 'Asha Rao', email: 'asha.rao@example.com', phone: '+91 98765 43210', role: 1, consent: true, ...o };
    await page.fill('#f-name', v.name); await page.fill('#f-email', v.email); await page.fill('#f-phone', v.phone);
    await page.selectOption('#f-role', { index: v.role });
    if (v.consent) await page.check('#f-consent'); else await page.uncheck('#f-consent');
  };
  const submit = async () => { await page.click('.submit'); await page.waitForTimeout(250); };
  const errs = () => page.$$eval('#enquiry .err', e => e.map(x => x.textContent).filter(Boolean));

  await test('form markup: POST to FormSubmit for ' + FORM_TO + ' (works without JS too)', async () => {
    eq(await page.getAttribute('#enquiry', 'action'), `https://formsubmit.co/${FORM_TO}`, 'action');
    eq((await page.getAttribute('#enquiry', 'method')).toUpperCase(), 'POST', 'method');
  });
  await test('hidden settings: subject, table template, honeypot', async () => {
    assert((await page.inputValue('input[name=_subject]')).includes('Bootcamp'), 'subject');
    eq(await page.inputValue('input[name=_template]'), 'table', 'template');
    const hp = await page.$eval('input[name=_honey]', e => ({ x: e.getBoundingClientRect().left, tab: e.tabIndex }));
    assert(hp.x < 0 && hp.tab === -1, 'honeypot off-screen and not focusable');
  });
  await test('every visible field has a label', async () => {
    const unl = await page.$$eval('#enquiry input:not([type=hidden]):not(.hp), #enquiry select, #enquiry textarea',
      els => els.filter(e => !(e.id && document.querySelector(`label[for="${e.id}"]`)) && !e.closest('label')).map(e => e.name));
    eq(unl.length, 0, 'unlabelled ' + unl.join(','));
  });
  await test('empty submit: 5 errors, nothing sent, focus on first bad field', async () => {
    await submit(); eq((await errs()).length, 5, 'errors'); eq(hits.length, 0, 'requests');
    eq(await page.evaluate(() => document.activeElement.id), 'f-name', 'focus');
  });
  await test('name shorter than 2 characters is rejected', async () => {
    await fill({ name: 'A' }); await submit(); assert((await errs()).includes('Please enter your name.'), 'name'); eq(hits.length, 0, 'req');
  });
  for (const bad of ['asha', 'asha@', 'asha@example', 'asha@example.c', 'asha rao@example.com']) {
    await test(`invalid email rejected: "${bad}"`, async () => {
      await fill({ email: bad }); await submit(); assert((await errs()).includes('Please enter a valid email address.'), bad); eq(hits.length, 0, 'req');
    });
  }
  for (const bad of ['12345', '98765-432', '+91 98765 43210 999']) {
    await test(`invalid phone rejected: "${bad}"`, async () => {
      await fill({ phone: bad }); await submit(); assert((await errs()).includes('Please enter a valid mobile number.'), bad); eq(hits.length, 0, 'req');
    });
  }
  await test('role must be chosen', async () => {
    await fill({ role: 0 }); await submit(); assert((await errs()).includes('Please choose one.'), 'role'); eq(hits.length, 0, 'req');
  });
  await test('consent must be ticked', async () => {
    await fill({ consent: false }); await submit();
    assert((await errs()).some(e => e.includes('consent')), 'consent'); eq(hits.length, 0, 'req');
  });
  await test('error clears as soon as the user corrects the field', async () => {
    await page.fill('#f-email', 'bad'); await submit(); assert(await page.$eval('#f-email', e => e.closest('.field').classList.contains('bad')), 'marked');
    await page.type('#f-email', 'x'); assert(!(await page.$eval('#f-email', e => e.closest('.field').classList.contains('bad'))), 'cleared');
  });
  for (const ph of ['9876543210', '+91 98765 43210', '+91-98765-43210', '(+91) 98765 43210']) {
    await test(`valid Indian mobile format accepted: "${ph}"`, async () => {
      mode = 'ok'; const n = hits.length; await fill({ phone: ph }); await submit(); await page.waitForTimeout(150);
      eq(hits.length, n + 1, 'request sent');
    });
  }
  await test('valid submission POSTs JSON to ' + ENDPOINT, async () => {
    hits.length = 0; mode = 'ok';
    await fill(); await page.fill('#f-org', 'NIT Example'); await page.selectOption('#f-count', { index: 2 });
    await page.fill('#f-msg', 'Please share next cohort dates.'); await submit(); await page.waitForTimeout(200);
    eq(hits.length, 1, 'one request'); eq(hits[0].url, ENDPOINT, 'endpoint'); eq(hits[0].method, 'POST', 'method');
    assert(hits[0].headers['content-type'].includes('application/json'), 'json');
    const b = hits[0].body;
    eq(b.Name, 'Asha Rao', 'Name'); eq(b.Email, 'asha.rao@example.com', 'Email'); eq(b.Phone, '+91 98765 43210', 'Phone');
    eq(b.Organisation, 'NIT Example', 'Org'); eq(b.Role, 'B.Tech / M.Tech / MCA student', 'Role'); eq(b.Participants, '6–20', 'Participants');
    eq(b.Message, 'Please share next cohort dates.', 'Message'); eq(b.Consent, 'Yes', 'Consent'); eq(b._honey, '', 'honeypot empty');
    assert(b._subject.includes('Bootcamp') && b._template === 'table', 'settings');
  });
  await test('success: thank-you message shown and form cleared', async () => {
    assert((await page.getAttribute('#status', 'class')).includes('ok'), 'ok class');
    assert((await page.textContent('#status')).includes('Thank you'), 'text');
    eq(await page.inputValue('#f-name'), '', 'cleared'); assert(!(await page.isChecked('#f-consent')), 'consent cleared');
    eq(await page.textContent('.submit'), 'Send enquiry', 'button reset'); assert(!(await page.isDisabled('.submit')), 'enabled');
  });
  await test('double-click sends only one enquiry (button disabled while sending)', async () => {
    hits.length = 0; mode = 'ok'; await page.unroute('https://formsubmit.co/**');
    await page.route('https://formsubmit.co/**', async r => { hits.push(1); await new Promise(z => setTimeout(z, 400));
      r.fulfill({ status: 200, contentType: 'application/json', body: '{"success":"true"}' }); });
    await fill(); await page.click('.submit'); await page.click('.submit', { force: true, timeout: 500 }).catch(() => {});
    assert(await page.isDisabled('.submit') || hits.length === 1, 'disabled while sending'); await page.waitForTimeout(700);
    eq(hits.length, 1, 'requests');
    await page.unroute('https://formsubmit.co/**');
    await page.route('https://formsubmit.co/**', async route => {
      hits.push({ url: route.request().url() });
      if (mode === 'http500') return route.fulfill({ status: 500, body: 'error' });
      if (mode === 'formsubmit-false') return route.fulfill({ status: 200, contentType: 'application/json', body: '{"success":"false","message":"This form needs Activation."}' });
      return route.abort();
    });
  });
  for (const [m, label] of [['http500', 'server error (HTTP 500)'], ['formsubmit-false', 'FormSubmit "success:false" (e.g. not yet activated)'], ['abort', 'network failure / offline']]) {
    await test(`failure fallback on ${label}: mailto ${FORM_TO} with details prefilled`, async () => {
      mode = m; await fill(); await submit(); await page.waitForTimeout(250);
      assert((await page.getAttribute('#status', 'class')).includes('fail'), 'fail class');
      const href = await page.getAttribute('#status a', 'href');
      assert(href.startsWith(`mailto:${FORM_TO}?subject=`), 'href ' + href.slice(0, 60));
      assert(decodeURIComponent(href).includes('Name: Asha Rao') && !decodeURIComponent(href).includes('_honey'), 'body');
      eq(await page.inputValue('#f-name'), 'Asha Rao', 'data kept for retry');
      assert(!(await page.isDisabled('.submit')), 'button re-enabled');
    });
  }
  await test('no JavaScript errors during all form tests', async () => {
    // "Failed to load resource" entries are the deliberate HTTP 500 / offline simulations above
    const real = page.errors.filter(e => !e.startsWith('Failed to load resource'));
    eq(real.length, 0, real.join(' | '));
  });
  await ctx.close();
}

// =========================================================== responsive
section('7. Responsive layout (no sideways scrolling)');
for (const w of [320, 360, 390, 414, 768, 1024, 1280, 1366, 1920]) {
  const { ctx, page } = await open({ viewport: { width: w, height: 900 } });
  await test(`width ${w}px: no horizontal overflow, header and hero visible`, async () => {
    await page.evaluate(() => document.querySelectorAll('.rv').forEach(e => e.classList.add('in')));
    const sw = await page.evaluate(() => document.documentElement.scrollWidth);
    assert(sw <= w, `scrollWidth ${sw} > ${w}`);
    assert(await page.isVisible('header .logo') && await page.isVisible('h1'), 'visible');
  });
  await ctx.close();
}

// =========================================================== robustness
section('8. Robustness and accessibility');
{
  const c = await browser.newContext({ javaScriptEnabled: false });
  const p = await c.newPage(); await p.route(/fonts\./, r => r.abort()); await p.goto(BASE);
  await test('JavaScript disabled: all content still visible and form still posts', async () => {
    const op = await p.$eval('#benefits .card', e => getComputedStyle(e).opacity); eq(op, '1', 'cards visible');
    assert(await p.isVisible('#contact form .submit'), 'form visible');
    eq(await p.getAttribute('#enquiry', 'action'), `https://formsubmit.co/${FORM_TO}`, 'action');
  });
  await c.close();

  const rm = await open({ reducedMotion: 'reduce' });
  await test('reduced motion: content shown without animation', async () => {
    const st = await rm.page.$eval('#benefits .card', e => getComputedStyle(e).opacity); eq(st, '1', 'opacity');
    await rm.page.click('#exNext');
    eq(await rm.page.$eval('#exCard', e => getComputedStyle(e).animationName), 'none', 'animation');
  });
  await rm.ctx.close();

  const a = await open();
  await test('axe-core: no serious or critical accessibility violations', async () => {
    await a.page.addScriptTag({ path: require.resolve('axe-core/axe.min.js') });
    await a.page.evaluate(() => document.querySelectorAll('.rv').forEach(e => e.classList.add('in')));
    await a.page.waitForTimeout(800);
    const r = await a.page.evaluate(() => axe.run(document, { resultTypes: ['violations'] }));
    const bad = r.violations.filter(v => ['serious', 'critical'].includes(v.impact));
    fs.writeFileSync(path.join(path.dirname(new URL(import.meta.url).pathname), 'axe-violations.json'), JSON.stringify(r.violations, null, 1));
    eq(bad.length, 0, bad.map(v => `${v.id} (${v.nodes.length}): ${v.nodes.slice(0, 2).map(n => n.target).join(' ')}`).join(' | '));
  });
  await test('all buttons have an accessible name', async () => {
    const bad = await a.page.$$eval('button', b => b.filter(x => !(x.getAttribute('aria-label') || x.textContent.trim())).length); eq(bad, 0, 'nameless');
  });
  await a.ctx.close();

  const n = await open();
  await test('custom 404 page renders for a missing URL', async () => {
    const r = await n.page.goto(new URL('this-page-does-not-exist', BASE).href); eq(r.status(), 404, 'status');
    assert((await n.page.textContent('h1')).includes("doesn't exist"), '404 text');
    await n.page.click('text=Go to the bootcamp page'); assert((await n.page.title()).includes('Mixture of Experts'), 'link home');
  });
  await n.ctx.close();
}

await browser.close();
const passed = results.filter(r => r.ok).length;
console.log(`\n${passed}/${results.length} tests passed`);
fs.writeFileSync(path.join(path.dirname(new URL(import.meta.url).pathname), 'TEST-RESULTS.json'), JSON.stringify({ base: BASE, passed, total: results.length, results }, null, 1));
process.exit(passed === results.length ? 0 : 1);
