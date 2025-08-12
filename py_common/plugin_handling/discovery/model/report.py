from dataclasses import dataclass
from typing import Tuple

from .descriptor import PluginDescriptor
from .rejection import Rejection


@dataclass(frozen=True)
class DiscoveryReport:
    """
    Deterministic result of discovery.
    - accepted: descriptors sorted by identity
    - rejected: rejections sorted by path for reproducible logs
    """
    accepted: Tuple[PluginDescriptor, ...]
    rejected: Tuple[Rejection, ...]
