"""Shared public payload policy. Private catalogs are inputs, not public assets."""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import hashlib
import json
from functools import lru_cache

POLICY_VERSION = 'aaf-public-free-core/v2'
PUBLIC_ROOTS = frozenset({'architect_framework','contracts','scripts','plugins','exported_skills',
    'vendor','examples','tests','docs','.github','.claude-plugin','.agents','.claude','design-system'})
PUBLIC_FILES = frozenset({'VERSION','README.md','README-VI.md','LICENSE','NOTICE','CHANGELOG.md',
    'CONTRIBUTING.md','CONTRIBUTING-VI.md','SECURITY.md','CODE_OF_CONDUCT.md','pyproject.toml',
    'setup.py','setup.cfg','MANIFEST.in','uv.lock','package.json','package-lock.json',
    'pytest.ini','.gitignore','.gitattributes','.editorconfig','.env.example','Makefile','requirements.txt'})
PUBLIC_FILES = PUBLIC_FILES | frozenset({'INSTALL.md','INSTALL.vi.md','install.sh','install.ps1',
    'README.vi.md','CHANGELOG.vi.md','CONTRIBUTING.vi.md','CODE_OF_CONDUCT.vi.md','SECURITY.vi.md'})
STATE_PARTS = frozenset({'.git','.venv','venv','node_modules','__pycache__','.pytest_cache',
    '.sdd','.architect-build','.architect-runtime','.architect-framework','.staging','build','dist'})
SOURCE_MANIFEST = 'release-source.json'


def safe_relative(rel: str) -> bool:
    path = PurePosixPath(rel)
    return bool(path.parts and path.as_posix() == rel and not path.is_absolute()
        and '..' not in path.parts and '\\' not in rel and ':' not in rel)


def public_candidate(rel: str) -> bool:
    if not safe_relative(rel):return False
    path=PurePosixPath(rel)
    if rel.startswith(('tests/research/','scripts/research/')):return False
    if any(p.casefold() in STATE_PARTS for p in path.parts):return False
    if (path.name.startswith('.env') and path.name != '.env.example') or path.name in {'credentials.json','secrets.json','paid-fingerprints.json',SOURCE_MANIFEST}:
        return False
    if path.suffix in {'.pyc','.pyo','.sqlite','.db','.lock'} and path.name not in {'uv.lock','package-lock.json'}:
        return False
    return path.parts[0] in PUBLIC_ROOTS or rel in PUBLIC_FILES


def free_ids(root: Path) -> frozenset[str]:
    path=root/'architect_framework/data/skill-slots.yml'
    stat=path.stat()
    return _free_ids(str(path.resolve()),stat.st_mtime_ns,stat.st_size)


@lru_cache(maxsize=16)
def _free_ids(filename,mtime,size) -> frozenset[str]:
    import yaml
    data=yaml.safe_load(Path(filename).read_text(encoding='utf-8')) or {}
    return frozenset(row['id'] for row in data.get('slots',[]) if row.get('free'))


def public_data(data: bytes, rel: str, root: Path) -> bytes:
    """Remove private per-skill instructions from discoverable catalog inputs."""
    rel=rel.removeprefix('plugins/architect-agent-framework/')
    targets={'architect_framework/data/domain_skills.yaml':('clusters','skills'),
        'architect_framework/data/task_skills.yaml':('families','tasks')}
    if rel not in targets and rel!='architect_framework/data/skill-slots.yml':return data
    import yaml
    free=free_ids(root)
    value=yaml.safe_load(data)
    if rel in targets:
        group,children=targets[rel]
        rows=[]
        for row in value[group]:
            kept=[x for x in row.get(children,[]) if x['id'] in free]
            if kept:rows.append({**row,children:kept})
        value={group:rows}
    else:
        private=[x['id'] for x in value.get('slots',[]) if not x.get('free')]
        previous=value.get('distribution',{})
        value={'schema_version':value['schema_version'],'store':value.get('store',''),
            'packs':[],'suite':{},'slots':[{k:v for k,v in x.items() if k not in {'pack'}} for x in value.get('slots',[]) if x['id'] in free],
            'distribution':{'policy':POLICY_VERSION,'private_skill_count':len(private) or previous.get('private_skill_count',0),
                'private_catalog_digest':hashlib.sha256(json.dumps(sorted(private)).encode()).hexdigest() if private else previous.get('private_catalog_digest')}}
    return yaml.safe_dump(value,sort_keys=False,allow_unicode=True).encode()


def runtime_resource(rel: str, root: Path) -> bool:
    if not public_candidate(rel):return False
    if rel.startswith(('exported_skills/domains/','exported_skills/tasks/','exported_skills/orchestration/')):
        parts=PurePosixPath(rel).parts
        index=2 if parts[1]=='orchestration' else 3
        if len(parts)>index and parts[index] not in free_ids(root):return False
    if rel in {'exported_skills/release-manifest.yml','exported_skills/sbom.cdx.json',
        'exported_skills/provenance.intoto.jsonl','exported_skills/agent.md'}:return False
    return True
