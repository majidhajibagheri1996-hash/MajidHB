# Majid Haji Bagheri — Research Portfolio

Static website. No build step — just upload these files to your repo and enable GitHub Pages.

## Deploy (GitHub Pages)
1. Create a repo (e.g. `majid-portfolio`, or `<username>.github.io` for a root domain).
2. Upload **everything in this folder**, keeping the structure intact.
3. Repo → **Settings → Pages** → Source: **Deploy from a branch** → Branch: **main**, folder **/ (root)** → Save.
4. Your site goes live at `https://<username>.github.io/<repo>/` in a minute or two.

## Structure
```
index.html                  Portfolio homepage
Majid_Haji_Bagheri_CV.pdf   Static PDF (backup)
styles.css                  Design tokens entry (used by the résumé pages)
tokens/                     Color / type / spacing / font tokens
assets/favicon.png          Browser/tab icon (MHB logo)
assets/apple-touch-icon.png Home-screen icon
assets/mhb-logo.png         Social-share (Open Graph) image
assets/figures/             Featured + paper/poster figures
assets/figures/papers/      Publication figures (001–013)
assets/figures/projects/    Research project images (01–07)
assets/fonts/               Self-hosted webfonts (Newsreader, IBM Plex)
resume/
  index.html                One-page résumé
  cv.html                   Full multi-page CV
  cv.css                    Shared print styles
.nojekyll                   Serve all files as-is
```

## Notes
- The homepage loads React and Google Fonts from CDNs, so it needs an internet connection.
- The résumé pages are self-hosted (offline-capable) and have a **Print / Save PDF** button.
- Contact form posts via Formspree — set your form ID in `index.html` (search `formspreeId`).
