"""Constants for Weheat Control."""

from datetime import timedelta

DOMAIN = "weheat_control"
PLATFORMS = ["switch", "number"]
UPDATE_INTERVAL = timedelta(minutes=5)
