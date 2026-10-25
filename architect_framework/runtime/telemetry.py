"""Optional OTel span event adapter. Durable business state remains authoritative.

The supplied span only needs the public add_event protocol. No SDK, exporter,
network access, source bodies or host usage are inferred by this adapter.
"""
from __future__ import annotations

SCHEMA = 'aaf-otel-events/v1'
FIELDS = ('event_id','event_type','run_id','task_id','attempt_id','parent_event_id',
          'trace_id','plan_digest','state','previous_state','decision_id','action')


def export(events, span, *, max_events=1000):
    if type(max_events) is not int or not 1 <= max_events <= 1000:
        raise ValueError('Use a bounded event batch of 1..1000')
    count = 0
    for event in events:
        if count == max_events:
            return {'schema':SCHEMA,'status':'PARTIAL','exported':count,'authority':'none'}
        attributes = {'aaf.schema':SCHEMA,'aaf.coverage':'partial','aaf.usage':'unknown'}
        attributes.update({'aaf.'+key:value for key in FIELDS
                           if isinstance((value:=event.get(key)),(str,bool,int,float))})
        try:
            span.add_event(str(event.get('event_type','aaf.event')),attributes=attributes)
        except Exception:
            return {'schema':SCHEMA,'status':'EXPORT_UNAVAILABLE','exported':count,'authority':'none'}
        count += 1
    return {'schema':SCHEMA,'status':'EXPORTED','exported':count,'authority':'none'}
