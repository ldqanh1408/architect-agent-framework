#!/usr/bin/env python3
"""Preview a template task under accepted grants; this command never writes documents."""
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architect_framework.template_plan import plan
from sdd_core.model import SddError

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace');parser.add_argument('--package',required=True)
    parser.add_argument('--bindings-file',type=Path);parser.add_argument('--select',action='append',default=[])
    args=parser.parse_args(argv)
    try:
        bindings=json.loads(args.bindings_file.read_text(encoding="utf-8")) if args.bindings_file else {}
        print(json.dumps(plan(args.workspace,args.package,bindings,args.select),ensure_ascii=False,indent=2));return 0
    except (SddError,ValueError,OSError) as error:
        print(json.dumps(error.to_dict() if hasattr(error,'to_dict') else {'status':'ERROR','message':str(error)}));return 3

if __name__=='__main__':raise SystemExit(main())
