from pathlib import Path

from .model.code_entry import CodeEntry
from ..discovery.model.descriptor import PluginDescriptor


def resolve_entry(descriptor: PluginDescriptor) -> CodeEntry | None:
    entry = descriptor.metadata.get("entry")
    if not entry:
        return None
    t = str(entry.get("type", "module_file")).strip()
    p = entry.get("path")
    if not p:
        return None

    path = (descriptor.source_path.parent / Path(p)).resolve()
    attr = str(entry.get("attr", "register")).strip()
    return CodeEntry(type=t, path=path, attr=attr)
