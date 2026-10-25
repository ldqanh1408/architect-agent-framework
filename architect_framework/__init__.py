"""
Architect Agent Framework
Based on ISO/IEC/IEEE 42010, TOGAF ADM, DDD, C4, arc42, ISO 25010, AWS WAF, and ATAM.
"""

from pathlib import Path
import sys

__version__ = "2.0.0"

_VENDOR_SDD = Path(__file__).resolve().parents[1] / "vendor" / "sdd-agent"
if (_VENDOR_SDD / "sdd_core").is_dir() and str(_VENDOR_SDD) not in sys.path:
    sys.path.insert(0, str(_VENDOR_SDD))
