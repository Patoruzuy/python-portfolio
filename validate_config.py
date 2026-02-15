#!/usr/bin/env python3
"""Compatibility wrapper for scripts/validate_config.py."""

from scripts.validate_config import main, parse_args
import sys


if __name__ == "__main__":
    args = parse_args()
    sys.exit(main(args.env))
