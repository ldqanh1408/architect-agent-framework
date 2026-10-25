from __future__ import annotations
import argparse, json, sys
from pathlib import Path
for candidate in (Path.cwd(), *Path(__file__).resolve().parents):
    if (candidate/'architect_framework').is_dir() and str(candidate) not in sys.path: sys.path.insert(0, str(candidate))
from architect_framework.orchestrator.skill_router import ProgressiveSkillRouter, RoutingError, select_module_owner
def main():
    parser=argparse.ArgumentParser(); sub=parser.add_subparsers(dest='command', required=True)
    catalog=sub.add_parser('catalog'); catalog.add_argument('--cluster'); catalog.add_argument('--family')
    route=sub.add_parser('route'); route.add_argument('--query', required=True); route.add_argument('--domain'); route.add_argument('--task'); route.add_argument('--limit', type=int, default=5); route.add_argument('--cluster')
    owner=sub.add_parser('owner', help='module owner: the policy charter build applies'); owner.add_argument('--intent', required=True); owner.add_argument('--owner', default=''); owner.add_argument('--owner-reason', default='')
    sub.add_parser('self-check', help='verify orchestrator routing catalog integrity')
    args=parser.parse_args()
    if args.command=='self-check':
        cat=ProgressiveSkillRouter().catalog()
        ok=isinstance(cat,dict) and len(cat.get('domains',[]))==110 and len(cat.get('tasks',[]))==186
        print(json.dumps({'status':'PASS' if ok else 'FAIL','domains':len(cat.get('domains',[])),'tasks':len(cat.get('tasks',[]))},sort_keys=True)); return 0 if ok else 1
    if args.command=='owner':
        verdict,refusal=select_module_owner(args.intent,args.owner,args.owner_reason)
        if refusal: verdict=dict(verdict,refusal=refusal)
        print(json.dumps(verdict,ensure_ascii=False,sort_keys=True)); return 0 if verdict.get('status')=='selected' and not refusal else 2
    router=ProgressiveSkillRouter()
    try:
        result=router.catalog(args.cluster,args.family) if args.command=='catalog' else router.route(args.query,args.domain,args.task,args.limit,args.cluster).to_dict()
    except RoutingError as exc:
        print(json.dumps({'status':'blocked','reason':str(exc)},sort_keys=True)); return 1
    print(json.dumps(result,ensure_ascii=False,sort_keys=True)); return 0 if args.command=='catalog' or result['status']=='selected' else 2
if __name__=='__main__': raise SystemExit(main())
