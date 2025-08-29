"""Data models for nudist spot submissions."""

from dataclasses import dataclass


@dataclass
class SpotSubmission:
    """Represents a user-submitted nudist spot awaiting moderation."""

    name: str
    latitude: float
    longitude: float
    official: bool = False
    description: str
    submitted_by: str
