"""Pure cardinality guard for explicit core template previews."""
import re

MULTI_INSTANCE = {'diagram','use_case','data_entity','api_contract','event_message','runtime_scenario'}


def cardinality_violations(data):
    """A concern with many identities needs an explicit key; no second writer can overwrite it implicitly."""
    return [row['path']+': multi-instance concern requires an explicit instance key'
            for row in data.get('slots',[]) if isinstance(row,dict)
            and row.get('page_class') in MULTI_INSTANCE
            and row.get('obligation') not in {'serial','derived'}
            and not re.search(r'\{[a-z][a-z0-9_-]*\}',row.get('path',''))]
