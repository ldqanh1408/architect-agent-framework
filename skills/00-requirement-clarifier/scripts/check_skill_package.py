#!/usr/bin/env python3
"""Validate the one current skill workflow, full method references and package identity."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from _skill_contract import validate_active

def validate_skill(root):
    result=validate_active(root)
    return result if result is not None else ['A current workflow-contract.yml is required']

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('skill_dir',type=Path)
    errors=validate_skill(parser.parse_args().skill_dir)
    for error in errors:print(error)
    print('FAILED' if errors else 'PASSED');return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())
