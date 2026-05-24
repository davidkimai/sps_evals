#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SPECORACLE_FORMAL_VARIANT", "v2_2")

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from specoracle.vericoding.formal_eval_v1 import main


if __name__ == "__main__":
    raise SystemExit(main())
