# Hephaestus Website

This directory contains the standalone marketing / product website for Hephaestus.

## Why This Exists

The product-facing application lives in:

- `frontend/`

The external landing / marketing website lives in:

- `website/`

This keeps the product app and the public-facing product site separate.

## Structure

- `index.html`
  Main landing page
- `styles.css`
  Standalone website styling
- `assets/`
  Static assets used by the website

## Deployment

This folder is designed to be easy to deploy as a static site, including GitHub Pages.

You can publish this directory with:

- GitHub Pages
- Vercel static hosting
- Netlify
- Any static web server

This repository also includes a GitHub Actions workflow:

- `.github/workflows/deploy-website.yml`

That workflow publishes the contents of `website/` to GitHub Pages.

## Notes

- The website content is intentionally product/marketing oriented.
- It should not be mixed into the product app entrypoints in `frontend/`.
- If the product application gets its own public deployment later, links in this site can be updated accordingly.

Triggered deployment refresh on 2026-05-02.
