"""Colored console logger."""

import sys
import io

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


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
        print(f"\n{'='*70}")
        print(f"  {Logger.B}{Logger.C}{msg}{Logger.X}")
        print(f"{'='*70}")

    @staticmethod
    def step(num, msg):
        print(f"\n  {Logger.B}[Step {num}]{Logger.X} {msg}")

    @staticmethod
    def info(msg):
        print(f"    {Logger.D}>{Logger.X} {msg}")

    @staticmethod
    def success(msg):
        print(f"    {Logger.G}[OK]{Logger.X} {msg}")

    @staticmethod
    def warn(msg):
        print(f"    {Logger.Y}[WARN]{Logger.X} {msg}")

    @staticmethod
    def error(msg):
        print(f"    {Logger.R}[ERR]{Logger.X} {msg}")

    @staticmethod
    def result(key, value):
        print(f"      {Logger.D}{key}:{Logger.X} {value}")

    @staticmethod
    def line(msg):
        print(f"  {msg}")


log = Logger()
