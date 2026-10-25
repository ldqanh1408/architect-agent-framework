"""Read routing metadata from user-installed descriptors; never broaden a grant."""
from collections.abc import Mapping


def installed_rows(kind):
    from architect_framework import skillpacks
    rows=[]
    for identity,package in skillpacks.installed().items():
        if package.contract is None or not skillpacks.contract_trusted(package.home):continue
        data=skillpacks._package_contract(package.home)
        if data.get('kind')!=kind or data.get('skill')!=identity:continue
        front=skillpacks._frontmatter(package.home/skillpacks.SKILL_MD)
        routing=data.get('routing') or {}
        if not isinstance(routing,Mapping):continue
        group=str(data.get('cluster_id') or data.get('family_id') or package.group)
        if not group:continue
        base={'id':identity,'name':front.get('title') or identity,'description':str(front.get('description') or '')}
        if kind=='domain':
            base.update(cluster_id=group,cluster_name=str(data.get('cluster_name') or group),
                iso_aspects=list(data.get('iso_aspects') or []))
        else:base.update(procedural_steps=[],expected_outputs=[])
        # Only declared metadata is used; empty values stay empty. Pydantic
        # validates the actual model at the registry boundary.
        base.update({k:v for k,v in routing.items() if k not in {'id','cluster_id','cluster_name'}})
        rows.append((group,base))
    return rows
