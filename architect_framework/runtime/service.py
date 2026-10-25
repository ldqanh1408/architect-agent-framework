"""Shared current core services. Scheduling carries no approval authority."""
from __future__ import annotations
import json
from architect_framework.runtime import core_runs
from architect_framework.sdd_bridge import require_core


class RuntimeUnavailable(RuntimeError):
    """The requested execution capability is unavailable."""


def plan(workspace, tasks=None, only=None, *, base_change=None):
    require_core(workspace)
    return core_runs.plan(workspace, tasks, only, base_change=base_change)


def start(workspace, *, run_id=None, executor=None, only=None, tasks=None, base_change=None):
    require_core(workspace)
    if executor is not None: raise RuntimeUnavailable("Use host task claim and complete; managed execution is unavailable")
    return core_runs.start(workspace,tasks,run_id,only,base_change=base_change)


def status(workspace,run_id=None):
    require_core(workspace)
    return core_runs.status(workspace,run_id)


def tick(workspace,run_id=None,*,executor=None):
    require_core(workspace)
    if executor is not None:raise RuntimeUnavailable("Managed execution is unavailable")
    return core_runs.tick(workspace,run_id)


def recheck(workspace,run_id=None,*,executor=None):
    return tick(workspace,run_id,executor=executor)


def latest_run(workspace):
    return status(workspace).get('run_id')


def scorecard_text(workspace,run_id=None):
    from architect_framework.sdd_bridge import status_probe, workspace_mode
    out = dict(status(workspace,run_id))
    if workspace_mode(workspace) == 'core':
        out['sdd'] = status_probe(workspace)
    return json.dumps(out,ensure_ascii=False,indent=2)
