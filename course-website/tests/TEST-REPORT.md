# Bootcamp website: test report

Tested page: `bootcamp.html`, deployed as `index.html` from `bootcamp-single-page-site.zip` on **Apache 2.4.58** (the web server used by cPanel / Hostinger shared hosting), with `.htaccess` active.  
Date: 2026-10-06

## Summary

| Area | Result |
|---|---|
| Browser tests (Chromium, Playwright) | **89/89 passed** |
| Hosting checks (Apache + .htaccess) | **16 passed, 0 failed** + HTTPS redirect verified |
| HTML validation (html-validate, recommended rules) | **0 problems** |
| Accessibility (axe-core, WCAG 2.1 AA rules) | **0 violations** |
| Lighthouse (mobile, simulated slow 4G) | Performance **99**, Accessibility **100**, Best Practices **100**, SEO **100** |
| Page speed | First paint 1.0 s, largest paint 1.0 s, layout shift 0 |
| Page weight | 54 KB raw, about 17 KB over the network with gzip |

## Contact form

- Recipient: **cto@algoprofessor.com**. JavaScript sends to `https://formsubmit.co/ajax/cto@algoprofessor.com`; the plain-HTML fallback (`action="https://formsubmit.co/cto@algoprofessor.com"`) covers browsers without JavaScript.
- Verified with intercepted requests: correct endpoint and POST method; JSON body with every field; empty honeypot; subject and table template; success message and form reset; only one request on double-click; fallback e-mail link to cto@algoprofessor.com with details prefilled on HTTP 500, on FormSubmit "success:false" (not yet activated) and when offline.
- **Cannot be tested from the build sandbox:** real delivery to the inbox (outbound internet is blocked here). After upload, send one enquiry from the live site and click **Activate** in the FormSubmit e-mail that arrives at cto@algoprofessor.com. Until activation, visitors see the e-mail fallback (tested above), so no enquiry is lost.

## Defects found and fixed during testing

| # | Defect | Fix |
|---|---|---|
| 1 | Page could scroll sideways by 8 px on phones and tablets while the day card or role card slid in | Horizontal overflow clipped on the page and the explorer |
| 2 | Gold text on white (tags, labels, day numbers) had contrast 2.4:1, below the WCAG 4.5:1 minimum | Darker text gold #7d600e (5.5:1) |
| 3 | White numbers on gold/orange day buttons, faded when not selected, were hard to read | Darker module colours (at least 4.8:1), no fading; selected day shown with an outline |
| 4 | Screen readers announced day buttons differently from their visible label | Visible text kept in the accessible name; topic added as screen-reader text |
| 5 | Grey body text on light-grey sections at 4.48:1 | Darkened to pass 4.5:1 |
| 6 | With "reduce motion" switched on, slide-in animations still ran | Animations disabled for reduced motion |
| 7 | No main landmark for screen-reader navigation | Page content wrapped in a main element |
| 8 | Google Fonts stylesheet blocked first paint (2.7 s on slow mobile) | Font loads without blocking: first paint 1.0 s, Lighthouse Performance 90 to 99 |
| 9 | Validator: missing explicit type on the menu button and two inputs | Added |

## Browser test cases


**1. Page load, SEO and structure**

- PASS: page loads with HTTP 200
- PASS: no JavaScript errors on load
- PASS: <html lang="en"> is set
- PASS: <title> mentions the bootcamp
- PASS: meta description present (50–170 chars)
- PASS: viewport meta present
- PASS: Open Graph title and description present
- PASS: favicon defined
- PASS: exactly one <h1>
- PASS: hero shows title, fee-free tagline and program director
- PASS: stats show 30 days / 5 modules / 30 labs / 1 capstone
- PASS: every in-page link (#…) points to an existing element
- PASS: external links open in a new tab with rel="noopener"
- PASS: mailto links are well formed
- PASS: fee shown as INR 1,00,000
- PASS: footer shows current year

**2. Header and navigation**

- PASS: mobile: menu hidden until burger is tapped
- PASS: mobile: tapping a menu link closes the menu
- PASS: desktop: all 7 nav items visible
- PASS: header stays visible (sticky) after scrolling

**3. Dynamic day explorer**

- PASS: 30 day buttons, coloured by 5 modules
- PASS: starts at Day 1 with progress 1/30
- PASS: Previous at Day 1 stays on Day 1
- PASS: Next moves to Day 2, then Day 3
- PASS: clicking Day 15 shows Day 15 and 50% progress
- PASS: day card shows topic, lab and module goal from the syllabus
- PASS: day types: D1 concept, D5 project, D6 assessment, D27 capstone
- PASS: "Up next" link jumps to the following day
- PASS: Next at Day 30 stays on Day 30 and shows completion
- PASS: keyboard: Arrow keys change day when explorer is focused
- PASS: selected day is marked aria-selected and earlier days "done"
- PASS: module card click jumps explorer to module start (Module 3 → Day 13)
- PASS: Play advances one day every 4 s and shows Pause
- PASS: Pause stops auto-advance
- PASS: auto-play stops by itself at Day 30
- PASS: manual navigation during play stops play
- PASS: mobile: swipe left/right on the day card changes day

**4. Full syllabus accordion**

- PASS: 5 modules × 6 days, numbered Day 1 … Day 30 in order
- PASS: module titles match the brochure
- PASS: Expand all opens 5, Collapse all closes all
- PASS: clicking a module heading toggles it
- PASS: print: all modules open and interactive parts hidden

**5. Careers, sectors and salaries**

- PASS: 5 role buttons
- PASS: each role shows its title, modules, skills and 3 salary bars
- PASS: salary bands rise with experience for every role
- PASS: salary bars stay inside their track
- PASS: 4 employer tiers and 8 sectors
- PASS: salary note: sources linked and no job / salary guarantee stated

**6. Contact form (recipient cto@algoprofessor.com)**

- PASS: form markup: POST to FormSubmit for cto@algoprofessor.com (works without JS too)
- PASS: hidden settings: subject, table template, honeypot
- PASS: every visible field has a label
- PASS: empty submit: 5 errors, nothing sent, focus on first bad field
- PASS: name shorter than 2 characters is rejected
- PASS: invalid email rejected: "asha"
- PASS: invalid email rejected: "asha@"
- PASS: invalid email rejected: "asha@example"
- PASS: invalid email rejected: "asha@example.c"
- PASS: invalid email rejected: "asha rao@example.com"
- PASS: invalid phone rejected: "12345"
- PASS: invalid phone rejected: "98765-432"
- PASS: invalid phone rejected: "+91 98765 43210 999"
- PASS: role must be chosen
- PASS: consent must be ticked
- PASS: error clears as soon as the user corrects the field
- PASS: valid Indian mobile format accepted: "9876543210"
- PASS: valid Indian mobile format accepted: "+91 98765 43210"
- PASS: valid Indian mobile format accepted: "+91-98765-43210"
- PASS: valid Indian mobile format accepted: "(+91) 98765 43210"
- PASS: valid submission POSTs JSON to https://formsubmit.co/ajax/cto@algoprofessor.com
- PASS: success: thank-you message shown and form cleared
- PASS: double-click sends only one enquiry (button disabled while sending)
- PASS: failure fallback on server error (HTTP 500): mailto cto@algoprofessor.com with details prefilled
- PASS: failure fallback on FormSubmit "success:false" (e.g. not yet activated): mailto cto@algoprofessor.com with details prefilled
- PASS: failure fallback on network failure / offline: mailto cto@algoprofessor.com with details prefilled
- PASS: no JavaScript errors during all form tests

**7. Responsive layout (no sideways scrolling)**

- PASS: width 320px: no horizontal overflow, header and hero visible
- PASS: width 360px: no horizontal overflow, header and hero visible
- PASS: width 390px: no horizontal overflow, header and hero visible
- PASS: width 414px: no horizontal overflow, header and hero visible
- PASS: width 768px: no horizontal overflow, header and hero visible
- PASS: width 1024px: no horizontal overflow, header and hero visible
- PASS: width 1280px: no horizontal overflow, header and hero visible
- PASS: width 1366px: no horizontal overflow, header and hero visible
- PASS: width 1920px: no horizontal overflow, header and hero visible

**8. Robustness and accessibility**

- PASS: JavaScript disabled: all content still visible and form still posts
- PASS: reduced motion: content shown without animation
- PASS: axe-core: no serious or critical accessibility violations
- PASS: all buttons have an accessible name
- PASS: custom 404 page renders for a missing URL

## Hosting checks (Apache)

- PASS home page / returns 200
- PASS index.html returns 200
- PASS robots.txt returns 200
- PASS styles.css (404 page styling) returns 200
- PASS unknown page returns 404
- PASS unknown page shows custom 404 page
- PASS .htaccess is not downloadable (403)
- PASS directory listing disabled (no index -> 403/404)
- PASS HTML served as text/html; charset utf-8
- PASS X-Content-Type-Options: nosniff
- PASS Referrer-Policy set
- PASS HTML not cached long (max-age=0)
- PASS gzip compression on HTML
- PASS CSS cached for 7 days
- PASS CSS compressed
- PASS robots.txt served as text/plain
- INFO page size: 54633 bytes raw, 17205 bytes over the wire (gzip)
- INFO server response time: 0.000704s (local)
- PASS HTTPS redirect lines in .htaccess, when uncommented, return 301 to https:// (tested, then restored to the safe default)

## How to re-run (also works against the live site)

```
npm i playwright axe-core
BASE=https://your-live-domain/ node tests/site.test.mjs
tests/hosting_checks.sh https://your-live-domain
```
