"""Compatibility accessor; contract locations have one authority."""
from architect_framework.contracts import framework_home


def runtime_root():
    return framework_home()
