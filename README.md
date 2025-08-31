# Legal Map

Simple React + Mapbox globe allowing community-submitted markers classified as Allowed, Restricted, Unofficial, or Illegal.

## Setup
1. Copy `config.sample.js` to `config.js` and fill in `MAPBOX_TOKEN` and optional `DISCORD_WEBHOOK_URL` for logging.
2. Serve the folder with any static file server or deploy to GitHub Pages.

## Usage
- Click on the map to add a spot. Provide name, country, and category.
- Use the text field or DM the Discord bot with `Name, Country, Category` (category optional).
- Country law info is fetched from [REST Countries](https://restcountries.com/).
- Events are optionally logged to Discord.

## Development
Run tests (none yet):
```bash
npm test
```