"""Safe YAML decoding for registry data, with the optional compiled parser."""
import yaml

_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def safe_load(stream):
    return yaml.load(stream, Loader=_LOADER)
