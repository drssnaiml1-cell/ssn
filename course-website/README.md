# Neurons to Mixture of Experts: 30-Day Bootcamp website

Static course website for the AlgoProfessor 30-day Deep Learning Mastery Bootcamp,
built from Part E (pages 28–31) of the *Neural Architectures: A Comparative Reference* handbook.

| File | Purpose |
|------|---------|
| `index.html` | Page structure: hero, program, curriculum, architectures, SDG capstones, tool stack, roadmap, fee and enrolment, FAQ |
| `data.js` | **All course content** (modules, 30-day schedule, architectures, blueprints, stack, roadmap). Edit this file to update the site |
| `app.js` | Renders `data.js` and handles the interactive parts (day picker, module tabs, blueprint tabs, mobile menu, enquiry form) |
| `styles.css` | Navy and gold design matching the handbook; responsive down to phone width |
| `assets/neurons-to-moe-bootcamp-brochure.pdf` | Downloadable brochure (handbook pages 30–31) |

## Preview

Open `index.html` in a browser; no build step or server is needed.

## Publish

Upload the whole folder to any static host:
- **GitHub Pages:** push the folder to a repository and enable Pages (Settings → Pages).
- **Netlify / Vercel / Cloudflare Pages:** drag and drop the folder, or connect the repository.
- **Existing hosting (cPanel etc.):** upload the files to a sub-domain folder,
  for example `bootcamp.algoprofessor.com`.

## Enquiry form

The form has no server: it opens the visitor's email app with an enquiry addressed to
`ceo@algoprofessor.com`. To collect enquiries automatically instead, point the form at a form
service (Formspree, Google Forms, Netlify Forms) or your own backend in `app.js`.

## Things to confirm before going live

- Cohort start dates and delivery mode (online / on-site) are not in the handbook, so the FAQ
  asks visitors to enquire. Add them to the FAQ in `index.html` when they are fixed.
- The site says nothing about certificates, refunds or payment methods; add these if they apply.
