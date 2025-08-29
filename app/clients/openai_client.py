"""OpenAI client wrapper for the Reddit bot.

This module exposes a single ``client`` instance configured with the
``OPENAI_API_KEY`` environment variable. The new ``openai`` Python package
(≥1.0) uses the :class:`OpenAI` class rather than the legacy
``openai.ChatCompletion`` interface. Other modules should import ``client``
from here and call ``client.chat.completions.create``.
"""

from __future__ import annotations

import os

from openai import OpenAI

# The API key is read from the environment. ``OpenAI`` lazily validates the
# key when the first request is made.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

__all__ = ["client"]
