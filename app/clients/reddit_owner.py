"""Reddit owner account client helper.

This module instantiates a PRAW client for the owner account.  It supports
either the traditional username/password based flow or a more stable
refresh-token flow.  Environment variables are validated to ensure the client
is configured correctly.
"""

from __future__ import annotations

import os
import praw


def create_reddit_owner() -> praw.Reddit:
    """Create and return a Reddit instance for the owner account.

    If ``OWNER_REDDIT_REFRESH_TOKEN`` is provided the refresh-token grant flow
    is used, avoiding password based tokens expiring.  Otherwise the legacy
    password flow is used.  Required environment variables are validated and a
    :class:`ValueError` is raised when any are missing.
    """

    client_id = os.getenv("OWNER_REDDIT_CLIENT_ID")
    client_secret = os.getenv("OWNER_REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("OWNER_REDDIT_USER_AGENT")
    refresh_token = os.getenv("OWNER_REDDIT_REFRESH_TOKEN")

    if refresh_token:
        required = {
            "OWNER_REDDIT_CLIENT_ID": client_id,
            "OWNER_REDDIT_CLIENT_SECRET": client_secret,
            "OWNER_REDDIT_USER_AGENT": user_agent,
            "OWNER_REDDIT_REFRESH_TOKEN": refresh_token,
        }
        missing = [name for name, val in required.items() if not val]
        if missing:
            raise ValueError(
                "Missing Reddit owner credentials: " + ", ".join(missing)
            )

        return praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            user_agent=user_agent,
        )

    # Fallback to username/password flow
    username = os.getenv("OWNER_REDDIT_USERNAME")
    password = os.getenv("OWNER_REDDIT_PASSWORD")
    required = {
        "OWNER_REDDIT_CLIENT_ID": client_id,
        "OWNER_REDDIT_CLIENT_SECRET": client_secret,
        "OWNER_REDDIT_USERNAME": username,
        "OWNER_REDDIT_PASSWORD": password,
        "OWNER_REDDIT_USER_AGENT": user_agent,
    }
    missing = [name for name, val in required.items() if not val]
    if missing:
        raise ValueError(
            "Missing Reddit owner credentials: " + ", ".join(missing)
        )

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        username=username,
        password=password,
        user_agent=user_agent,
    )


# Global instance used by the rest of the application
reddit_owner = create_reddit_owner()
