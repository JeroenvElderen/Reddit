# Deployment

## Owner account token management

The decay reminder job sends messages from a dedicated "owner" Reddit
account. To ensure the job can run continuously without manual
intervention, use Reddit's **refresh token** flow instead of the
password-based script flow.

1. Create a Reddit script application for the owner account and note the
   *client id* and *client secret*.
2. Generate a refresh token (see PRAW's `obtain_refresh_token.py` example or
   use `praw-util`). Log in as the owner account when prompted.
3. Set the following environment variables for the bot process:
   - `OWNER_REDDIT_CLIENT_ID`
   - `OWNER_REDDIT_CLIENT_SECRET`
   - `OWNER_REDDIT_USER_AGENT`
   - `OWNER_REDDIT_REFRESH_TOKEN`
4. To rotate credentials, revoke the old token on Reddit's
   [authorized applications](https://www.reddit.com/prefs/apps) page and
   repeat the token generation. Update the `OWNER_REDDIT_REFRESH_TOKEN`
   environment variable and restart the process.

If a refresh token is not supplied the application falls back to the
username/password flow using `OWNER_REDDIT_USERNAME` and
`OWNER_REDDIT_PASSWORD`, but those credentials may expire and require
regular rotation.