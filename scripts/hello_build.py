#!/usr/bin/env python3
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--name", required=True)
args = parser.parse_args()
print(f"Hello, {args.name}! Build system works.")
