"""Check alembic heads.

Make sure there is only one alembic head.
"""

import sys

from alembic.config import Config
from alembic.script import ScriptDirectory

alembic_cfg = Config("alembic.ini")
script = ScriptDirectory.from_config(alembic_cfg)
heads = script.get_heads()

if len(heads) > 1:
    print("Error: Multiple Alembic heads detected.")
    sys.exit(1)
else:
    print("Alembic head check passed.")
