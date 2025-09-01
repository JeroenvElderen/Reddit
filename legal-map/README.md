# Legal Map

Simple React + Mapbox globe allowing community-submitted markers classified as Allowed, Restricted, Unofficial, or Illegal.

## Setup
1. Edit `config.js` and provide values for `MAPBOX_TOKEN`, `SUPABASE_URL`, `SUPABASE_ANON_KEY` and optional `DISCORD_WEBHOOK_URL` for logging. Sample values live in `config.sample.js`.to keep secrets out of version control.
2. Serve the folder with any static file server or deploy to GitHub Pages.
3. Ensure Mapbox GL JS v2 is used. The included `index.html` loads v2.15.0 from the Mapbox CDN. If you're upgrading an existing project, update your CDN script tags or run `npm install mapbox-gl@^2`.

## Usage
- Click on the map to add a spot. Provide name, country, and category.
- Use the text field or DM the Discord bot with `Name, Country, Category` (category optional).
- Country law info is fetched from [REST Countries](https://restcountries.com/).
- Events are optionally logged to Discord.
- Markers are stored in Supabase and automatically loaded on every visit.

## Development
Run tests (none yet):
```bash
npm test
```