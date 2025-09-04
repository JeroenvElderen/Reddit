# Legal Map

Simple React + Google Maps allowing community-submitted markers classified as Official, Restricted, Unofficial, Illegal or Secluded.

## Setup
1. Edit `config.js` and provide values for `GOOGLE_MAPS_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY` and optional `DISCORD_WEBHOOK_URL` for logging. Sample values live in `config.sample.js` to keep secrets out of version control.
2. Serve the folder with any static file server or deploy to GitHub Pages.
3. The app dynamically loads the Google Maps JavaScript API (with Places library). Ensure your API key has Maps and Places enabled.

## Usage
- Click on the map to add a spot. Provide name, country, **Reddit username**, category, and a description.
- Use the search box to find a location; you'll be prompted for your Reddit username before a marker is added.
- You can also DM the Discord bot with `Name, Country, Category, Description` (category optional).
- Events are optionally logged to Discord.
- Markers are stored in Supabase and automatically loaded on every visit.

## Development
Run tests (none yet):
```bash
npm test
```