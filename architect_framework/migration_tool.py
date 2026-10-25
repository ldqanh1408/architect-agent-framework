"""Separate old-to-core migration with an explicit owner and loss report."""
import argparse
import hashlib
import json
from pathlib import Path
import uuid

from sdd_core.bootstrap import initial_config
from sdd_core.migration import apply_migration_plan
from sdd_core.model import SddError
from sdd_core.workspace import TEXT_SUFFIXES

CONTROL={'.git','.sdd','.architect','.architect-runtime','.architect-build','__pycache__'}
OLD_AUTHORITY={'human-gate-ledger.yml','agent-question-ledger.yml','human-decisions.yml','sdd-context.yml','sdd-registry.yml','workflow-state.yml'}


def plan(source,workspace_id,reviewer,owner):
    source=Path(source)
    if source.is_symlink() or not source.is_dir() or (source/'sdd-workspace.yml').exists():
        raise SddError('MIGRATION_SOURCE_INVALID','Select a regular old workspace without a core marker')
    source=source.resolve();config=initial_config(workspace_id,reviewer)
    config['policy']['decision_authority']='external';config['control_directories']=['.architect','.architect-runtime','.architect-build']
    files,manifest,quarantine,unsupported,mapping={},{},[],[],[]
    namespace=uuid.uuid5(uuid.NAMESPACE_URL,'sdd-workspace:'+workspace_id)
    for path in sorted(source.rglob('*')):
        relative=path.relative_to(source).as_posix()
        if path.is_symlink():unsupported.append({'path':relative,'reason':'symlink'});continue
        if not path.is_file():continue
        raw=path.read_bytes();manifest[relative]=hashlib.sha256(raw).hexdigest()
        if any(part in CONTROL for part in path.relative_to(source).parts) or path.name in OLD_AUTHORITY:
            quarantine.append({'path':relative,'sha256':manifest[relative],'reason':'Old authority or machine state; retained only in the source'});continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            unsupported.append({'path':relative,'reason':'Unsupported format requires explicit conversion'});continue
        try:text=raw.decode('utf-8')
        except UnicodeDecodeError:unsupported.append({'path':relative,'reason':'Not UTF-8'});continue
        identity='DOC-'+uuid.uuid5(namespace,relative).hex[:20]
        config['artifacts'][identity]={'path':relative,'kind':'requirement' if 'requirement' in path.stem.lower() else 'document','owner':owner}
        files[relative]=text;mapping.append({'artifact_id':identity,'path':relative,'owner':owner,'requires':['kind confirmation','stable clauses','obligations','independent review']})
    config['skills']={owner:{'capabilities':['author','configure'],'write_scope':['sdd-workspace.yml',*sorted(files)]}}
    return {'status':'IMPORTED_UNVERIFIED','config':config,'files':files,'source_manifest':manifest,'quarantined':quarantine,'unsupported':unsupported,'ambiguities':mapping,'approval_reused':False}


def migrate(source, destination, workspace_id, reviewer, owner, resume=False, fault=None):
    mapping = plan(source, workspace_id, reviewer, owner)
    return apply_migration_plan(source, destination, mapping, resume, fault)


def main(argv=None):
    parser=argparse.ArgumentParser(prog='architect-migrate',allow_abbrev=False)
    parser.add_argument('source');parser.add_argument('--destination');parser.add_argument('--workspace-id',required=True)
    parser.add_argument('--reviewer',required=True);parser.add_argument('--owner',required=True);parser.add_argument('--resume',action='store_true')
    args=parser.parse_args(argv)
    try:
        mapping=plan(args.source,args.workspace_id,args.reviewer,args.owner)
        result=apply_migration_plan(args.source,args.destination,mapping,args.resume) if args.destination else {k:v for k,v in mapping.items() if k!='files'}
        print(json.dumps(result,ensure_ascii=False,indent=2));return 3 if args.destination else 0
    except SddError as error:print(json.dumps(error.to_dict(),ensure_ascii=False));return 3

if __name__=='__main__':raise SystemExit(main())
