"""Location of machine trust state. No workspace execution records are read."""
from pathlib import Path
import os


def state_home():
    override = os.environ.get("ARCHITECT_STATE_HOME")
    if override:
        return Path(override)
    from architect_framework.skillpacks import home_dir
    return home_dir()
