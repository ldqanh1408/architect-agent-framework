"""Encode data safely inside an inline script element."""
import json


def script_json(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
