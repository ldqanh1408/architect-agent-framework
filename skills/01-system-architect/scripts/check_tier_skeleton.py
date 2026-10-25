#!/usr/bin/env python3
"""Check a current registered workspace through the canonical core engine."""
from pathlib import Path
import argparse,json,sys
for candidate in Path(__file__).resolve().parents:
    if (candidate/'architect_framework/__init__.py').is_file():
        sys.path.insert(0,str(candidate));sys.path.insert(0,str(candidate/'vendor/sdd-agent'));break

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('workspace')
    args=parser.parse_args(argv)
    try:
        from architect_framework.sdd_bridge import check
        report=check(args.workspace)
        print(json.dumps(report,ensure_ascii=False));return report['exit_code']
    except ImportError:
        print(json.dumps({'status':'INCOMPLETE','code':'CORE_RUNTIME_REQUIRED','message':'Install architect-agent-framework[sdd] to check a current workspace'}));return 3

if __name__=='__main__':raise SystemExit(main())
