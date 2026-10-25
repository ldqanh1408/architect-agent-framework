"""Bounded, read-only support diagnostics. Bodies, leases, decisions and env are excluded."""
from __future__ import annotations
from pathlib import Path

from architect_framework.sdd_bridge.mode import classify
from architect_framework.runtime.capabilities import describe
from sdd_core.model import SddError


def doctor(workspace):
    from . import core_runs
    setup=classify(workspace)
    result={'schema':'aaf-doctor/v1','workspace':{key:setup[key] for key in ('state','code','next_action')},
            'capabilities':describe(),'retention':{'default':'preserve','automatic_history_deletion':False,
            'recovery':'Back up the run database with SQLite backup and preserve the source workspace before explicit recovery.'},
            'redaction':'Allowlist only. No document body, objective, key, token, full path, operations or decision payload.'}
    if setup['state']!='current':
        return result|{'status':'INCOMPLETE','runs':{'state':'unavailable'}}
    try:
        view=core_runs.observe(Path(workspace),limit=50,include_snapshot=False)
        state=core_runs.status(workspace)
        result['runs']={'state':state['state'],'tasks':len(state.get('tasks',[])),
                        'task_states':sorted({task['state'] for task in state.get('tasks',[])}),
                        'next_cursor':view['next_cursor'],'last_seq':view['last_seq'],'coverage':view['coverage']}
        result['status']='PASS'
    except (SddError,OSError) as error:
        result.update(status='INCOMPLETE',runs={'state':'unavailable','code':getattr(error,'code','STATE_IO_ERROR')})
    return result
