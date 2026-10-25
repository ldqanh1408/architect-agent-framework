"""Read-only UI adaptation. Accepted workspace grants remain the write authority."""
from collections.abc import Mapping

from architect_framework import skillpacks


def workspace_ui_adaptation_profile(snapshot):
    profiles=[]
    for identity,grant in sorted((snapshot.config.get('skills') or {}).items()):
        selected=skillpacks.slot(identity)
        contract=skillpacks._package_contract(selected.contract_home) if selected.contract_home else {}
        kinds=[str(row.get('page_class') or row.get('kind') or '') for row in contract.get('required_outputs',[]) if isinstance(row,Mapping) and (row.get('page_class') or row.get('kind'))]
        mode='req_trace_matrix' if identity=='00-requirement-clarifier' else 'critic_scorecard' if identity=='02-spec-critic' else 'adr_tradeoff_radar' if 'adr' in identity else 'workflow_state_dag' if contract else 'universal_inspector'
        profiles.append({'skill_id':identity,'tier':selected.state,'view_mode':mode,
            'console_title':identity,'primary_panels':['Documents','Evidence','Review'],
            'metric_badges':[], 'allowed_write_roots':list(grant.get('write_scope',[])) if isinstance(grant,Mapping) else [],
            'output_kinds':sorted(set(kinds)), 'jev_question_ids':[],
            'packed_http_requests_per_cluster':None})
    return {'contract_driven_ui':True,'core_shell_immutable':True,
        'external_fallback_mode':'universal_inspector','jev_pricing_per_million_input_usd':None,
        'skills':profiles}
