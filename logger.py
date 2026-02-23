"""Colored console logger with file logging."""

import sys
import io
import os
from datetime import datetime

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(WORK_DIR, "log")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
_log_file_handle = open(LOG_FILE, "w", encoding="utf-8")


def _strip_ansi(text):
    import re
    return re.sub(r'\033\[[0-9;]*m', '', text)


def _write(msg):
    print(msg)
    _log_file_handle.write(_strip_ansi(msg) + "\n")
    _log_file_handle.flush()


class Logger:
    G = "\033[92m"
    R = "\033[91m"
    Y = "\033[93m"
    C = "\033[96m"
    B = "\033[1m"
    D = "\033[2m"
    X = "\033[0m"

    @staticmethod
    def header(msg):
        _write(f"\n{'='*70}")
        _write(f"  {Logger.B}{Logger.C}{msg}{Logger.X}")
        _write(f"{'='*70}")

    @staticmethod
    def step(num, msg):
        _write(f"\n  {Logger.B}[Step {num}]{Logger.X} {msg}")

    @staticmethod
    def info(msg):
        _write(f"    {Logger.D}>{Logger.X} {msg}")

    @staticmethod
    def success(msg):
        _write(f"    {Logger.G}[OK]{Logger.X} {msg}")

    @staticmethod
    def warn(msg):
        _write(f"    {Logger.Y}[WARN]{Logger.X} {msg}")

    @staticmethod
    def error(msg):
        _write(f"    {Logger.R}[ERR]{Logger.X} {msg}")

    @staticmethod
    def result(key, value):
        _write(f"      {Logger.D}{key}:{Logger.X} {value}")

    @staticmethod
    def line(msg):
        _write(f"  {msg}")


log = Logger()
