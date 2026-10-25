"""Resolve current runtime contracts from accepted grants and artifact metadata."""
import hashlib
from pathlib import Path
import yaml
from architect_framework.contracts import REPO_ROOT
from sdd_core.storage import Store
from sdd_core.workspace import capture
from sdd_core.model import SddError,digest


def compile_contract(workspace,skill):
    live=capture(Path(workspace));store=Store(Path(workspace));baseline=store.baseline()
    accepted=store.load_snapshot(baseline['snapshot_digest']) if baseline else live
    grant=accepted.config.get('skills',{}).get(skill)
    if grant is None:raise SddError('SKILL_UNREGISTERED','Select an accepted skill grant')
    source=REPO_ROOT/'contracts/foundation-workflows'/f'{skill}.yml'
    contract=yaml.safe_load(source.read_text(encoding='utf-8')) if source.is_file() else None
    current=live.config.get('artifacts',{})
    result={'schema_version':1,'skill':skill,'grant':grant,'origin_snapshot':live.digest,
            'base_acceptance':baseline['acceptance_id'] if baseline else None,
            'current_outputs':[dict(metadata,artifact_id=identity) for identity,metadata in current.items() if metadata['owner']==skill],
            'obligations':[o for o in live.config.get('obligations',[]) if o.get('owner')==skill],
            'workflow':contract['workflow_contract'] if contract else None,
            'source':{'path':source.relative_to(REPO_ROOT).as_posix(),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()} if contract else None}
    return result|{'contract_digest':digest(result)}
