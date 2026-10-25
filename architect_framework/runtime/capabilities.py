"""Canonical supported execution and authority boundary, shared by host surfaces."""
from __future__ import annotations

SCHEMA='aaf-capabilities/v1'
ACTIONS={
 'plan':{'mcp':'architect_runtime_plan','cli':'plan','ui':'overview','mutation':'none'},
 'start':{'mcp':'architect_runs_start','cli':'start','ui':None,'mutation':'run-store'},
 'observe':{'mcp':'architect_runs_observe','cli':'observe','ui':'runs','mutation':'none'},
 'control':{'mcp':'architect_runs_control','cli':'control','ui':'runs','mutation':'run-store'},
 'claim':{'mcp':'architect_task_claim','cli':'claim','ui':None,'mutation':'attempt-lease'},
 'heartbeat':{'mcp':'architect_task_heartbeat','cli':'heartbeat','ui':None,'mutation':'attempt-lease'},
 'complete':{'mcp':'architect_task_complete','cli':'complete','ui':None,'mutation':'isolated-candidate'},
 'read':{'mcp':'architect_sdd_read','cli':None,'ui':'documents','mutation':'none'},
 'check':{'mcp':'architect_sdd_check','cli':'sdd check','ui':'review','mutation':'none'},
 'candidate-review':{'mcp':'architect_candidate_review','cli':'sdd review-candidate','ui':'review','mutation':'review-evidence','qualification':'advisory until independently qualified'},
 'language-review':{'mcp':'architect_language_review','cli':'sdd language-review','ui':'review','mutation':'review-evidence','qualification':'unverified profile mapping remains unknown'},
 'language-repair':{'mcp':'architect_language_repair','cli':'sdd language-repair','ui':'review','mutation':'isolated-candidate','qualification':'host-authored; no acceptance authority'},
 'propose':{'mcp':'architect_sdd_propose','cli':'sdd changes propose','ui':None,'mutation':'isolated-candidate'},
 'style-check':{'mcp':'architect_style_check','cli':None,'ui':None,'mutation':'none','qualification':'subset only; unverified mapping and semantic review remain unknown'},
 'doctor':{'mcp':'architect_doctor','cli':'doctor','ui':None,'mutation':'none'},
 'init':{'mcp':'architect_sdd_init','cli':'sdd host-init','ui':None,'mutation':'workspace-init'},
 'extract-sources':{'mcp':'architect_sdd_extract','cli':'sdd extract-sources','ui':None,'mutation':'build-cache'},
 'materialize':{'mcp':'architect_sdd_materialize','cli':'sdd materialize','ui':None,'mutation':'workspace-tree'},
 'prepare-check':{'mcp':'architect_sdd_prepare_check','cli':'sdd prepare-check','ui':None,'mutation':'candidate-postprocess'},
 'plan-waves':{'mcp':None,'cli':'sdd plan-waves','ui':None,'mutation':'build-cache'},
 'probe-models':{'mcp':None,'cli':'sdd probe-models','ui':None,'mutation':'none'},
 'execute-standalone':{'mcp':'architect_execute_standalone','cli':'sdd execute-standalone','ui':None,'mutation':'standalone-output'},
 'scorecard':{'mcp':'architect_runtime_scorecard','cli':'scorecard','ui':'overview','mutation':'none'},
 'skills':{'mcp':'architect_runtime_skills','cli':'skills status','ui':'overview','mutation':'none'},
 'console-url':{'mcp':'architect_console_url','cli':'console url','ui':'review','mutation':'none'},
 'dashboard':{'mcp':None,'cli':'sdd dashboard','ui':'overview','mutation':'none'},
 'dispatch-decision':{'mcp':None,'cli':None,'ui':'gates','mutation':'signed-decision','human':True},
 'acceptance':{'mcp':None,'cli':'sdd accept','ui':'review','mutation':'signed-acceptance','human':True},
}


def describe():
    import copy
    return {'schema':SCHEMA,'execution':'host-managed','managed_model_execution':False,
            'observation':{'transport':'durable cursor polling','coverage':'partial','host_tool_trace':False,'host_usage':False},
            'human_signing_over_mcp':False,'unknown_usage_is_zero':False,
            'actions':copy.deepcopy(ACTIONS),'limits':{'tasks':100,'operations_per_task':200,'plan_bytes':5*1024*1024,
                'review_packet_bytes_default':200000,'task_graph_visual_nodes':50},
            'unsupported':['old phase/wave checkpoints','direct document writers','name-only acceptance','embedded historical viewer resource']}
