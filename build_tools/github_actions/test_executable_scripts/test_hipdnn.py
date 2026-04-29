# Copyright Advanced Micro Devices, Inc.
# SPDX-License-Identifier: MIT

import logging
import os
import shlex
import subprocess
from pathlib import Path

THEROCK_BIN_DIR = os.getenv("THEROCK_BIN_DIR")
SCRIPT_DIR = Path(__file__).resolve().parent
THEROCK_DIR = SCRIPT_DIR.parent.parent.parent
AMDGPU_FAMILIES = os.getenv("AMDGPU_FAMILIES")

logging.basicConfig(level=logging.INFO)

from test_utils import get_ctest_junit_path

cmd = [
    "ctest",
    "--test-dir",
    f"{THEROCK_BIN_DIR}/hipdnn",
    "--output-on-failure",
    "--parallel",
    "8",
    "--timeout",
    "60",
    "--output-junit",
    str(get_ctest_junit_path("hipdnn")),
]

logging.info(f"++ Exec [{THEROCK_DIR}]$ {shlex.join(cmd)}")

subprocess.run(
    cmd,
    cwd=THEROCK_DIR,
    check=True,
)
