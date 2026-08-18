import sys
from pathlib import Path

# Make project modules (config, agents, models, ...) importable when pytest
# is invoked from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
