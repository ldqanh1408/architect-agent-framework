"""Turn declarative package templates into a scoped core task preview, never live writes."""
from __future__ import annotations
from pathlib import Path, PurePosixPath
import re
import yaml
from sdd_core.model import SddError
from architect_framework.runtime import core_runs


from architect_framework.cardinality import cardinality_violations


def plan(workspace,package,bindings=None,selected=None):
    package=Path(package);bindings=bindings or {};selected=set(selected or [])
    path=package/'workspace-template.yml'
    if not path.is_file() or path.stat().st_size>2*1024*1024:
        raise SddError('TEMPLATE_INVALID','Select a bounded declarative workspace template')
    try:data=yaml.safe_load(path.read_text(encoding='utf-8'))
    except (yaml.YAMLError,UnicodeError) as error:raise SddError('TEMPLATE_INVALID','Template YAML is invalid') from error
    if not isinstance(data,dict) or not isinstance(data.get('skill'),str) or not isinstance(data.get('slots'),list):
        raise SddError('TEMPLATE_INVALID','Template needs skill identity and declarative slots')
    if len(data['slots'])>200 or any(not isinstance(key,str) or not isinstance(value,(str,list)) or any(not isinstance(v,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+',v) for v in (value if isinstance(value,list) else [value])) or isinstance(value,list) and not 1<=len(value)<=100 for key,value in bindings.items()):
        raise SddError('TEMPLATE_BINDING_INVALID','Use bounded text path bindings')
    violations=cardinality_violations(data)
    if violations:raise SddError('TEMPLATE_CARDINALITY_INVALID','; '.join(violations))
    def expand(text, current):
        if not isinstance(text,str):raise SddError('TEMPLATE_INVALID','Template paths must be text')
        for key,value in current.items():text=text.replace('{'+key+'}',value)
        if '{' in text or '}' in text or not text:raise SddError('TEMPLATE_BINDING_REQUIRED','Bind every selected template path explicitly')
        p=PurePosixPath(text)
        if p.is_absolute() or '..' in p.parts or '\\' in text or ':' in text:
            raise SddError('TEMPLATE_PATH_INVALID','Template path escapes its document scope')
        return text
    outputs=[];deferred=[]
    for row in data['slots']:
        if not isinstance(row,dict) or not isinstance(row.get('path'),str):raise SddError('TEMPLATE_INVALID','Each slot needs a path')
        if row.get('when')!='always' and row['path'] not in selected:
            deferred.append({'path':row['path'],'reason':'Conditional slot requires explicit source-backed selection'})
            continue
        from itertools import product
        text=data.get('owns_root','')+'/'+row['path']
        keys=sorted(set(re.findall(r'\{([^{}]+)\}',text)))
        if any(key not in bindings for key in keys):raise SddError('TEMPLATE_BINDING_REQUIRED','Bind every selected path key explicitly')
        values=[bindings[key] if isinstance(bindings[key],list) else [bindings[key]] for key in keys]
        count=1
        for choices in values:count*=len(choices)
        if count>200 or count+len(outputs)>200:raise SddError('TEMPLATE_EXPANSION_LIMIT','Use at most 200 explicit output paths')
        for combination in product(*values):
            current=dict(zip(keys,combination));root=expand(data.get('owns_root',''),current).rstrip('/')
            rel=expand(row['path'],current)
            if row.get('kind')=='folder' or rel.endswith('/'):continue
            path=root+'/'+rel
            if any(output['path']==path for output in outputs):raise SddError('TEMPLATE_COLLISION','Expanded output paths must be distinct')
            outputs.append({'path':path})
    unknown=selected-{row['path'] for row in data['slots']}
    if unknown:raise SddError('TEMPLATE_SLOT_UNKNOWN','Selection names a slot absent from this template')
    task={'id':'T-template','skill':data['skill'],'writes':[row['path'] for row in outputs],
          'required_outputs':outputs,'objective':'Author selected template concerns from current registered sources; preserve authored content'}
    return core_runs.plan(workspace,[task])|{'template':{'skill':data['skill'],'deferred':deferred,
            'authority':'Planning input only; accepted workspace grants authorize writes',
            'authored_content':'Read before proposing exact-revision patches; this planner writes no content'}}
