# Fashion Pulse

Daily fashion-industry news brief for a category manager — Global · India · Europe.
Static site + GitHub Actions RSS aggregator. Refreshes every day at **11:00 AM IST**.

## How it works
1. `.github/workflows/update.yml` runs daily at 05:30 UTC (11:00 IST)
2. `fetch_news.py` pulls every feed in `feeds.json`, tags region, dedupes, writes `data/news.json`
3. `index.html` (GitHub Pages) renders the JSON — tabs for Global / India / Europe, source filters, search

## Deploy (one time, ~5 minutes)
1. Create a new **public** repo on GitHub (e.g. `fashion-pulse`)
2. Upload all files in this folder (keep the `.github/workflows/` path intact)
3. Repo → **Settings → Pages** → Source: *Deploy from a branch* → Branch: `main` / `/ (root)` → Save
4. Repo → **Actions** tab → enable workflows → open *Daily fashion news refresh* → **Run workflow** (first manual run replaces the demo data)
5. Your site is live at `https://<username>.github.io/fashion-pulse/`

## Add / remove sources
Edit `feeds.json` — each feed needs `name`, `url` (RSS), `region` (Global | India | Europe).
Pushing the edit auto-triggers a refresh. Statista & Euromonitor have no public RSS, so they sit in `reference_links` as sidebar bookmarks.

## Run locally
```
pip install -r requirements.txt
python fetch_news.py
python -m http.server   # open http://localhost:8000
```
