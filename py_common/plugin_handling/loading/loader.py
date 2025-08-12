import sys
import traceback
from hashlib import blake2b
from importlib.util import spec_from_file_location, module_from_spec
from types import ModuleType
from typing import Type, Dict, Any, Mapping

from .entry_resolver import resolve_entry
from ...constants import COMMON_LOGGING_PREFIX
from ...logging import HoornLogger
from ..discovery.model.descriptor import PluginDescriptor
from .model.code_entry import CodeEntry
from .model.load_failure import LoadFailure
from .model.loaded_plugin import LoadedPlugin
from .protocol.registry_protocol import RegistryProtocol


class PluginLoader:
    """
    Loads plugin code from disk and calls its `register(registry)` function.

    Responsibilities:
    - Resolve a CodeEntry from the descriptor metadata
    - Dynamically import the module using importlib
    - Retrieve and call the register() function
    - Validate and filter returned exports against capability contracts
    - Return LoadedPlugin or LoadFailure
    """

    def __init__(
            self,
            logger: HoornLogger,
            *,
            capability_contracts: Mapping[str, Type[object]],
            refresh_import_caches: bool = True,
            strict_validation: bool = True,
    ):
        self._logger = logger
        self._separator: str = f"{COMMON_LOGGING_PREFIX}.Plugins.PluginLoader"

        self._capability_contracts: Dict[str, Type[object]] = dict(capability_contracts)

        self._refresh_import_caches = refresh_import_caches
        self._strict_validation = strict_validation

        self._logger.trace("Initialized.", separator=self._separator)

    # noinspection t
    def load(self, descriptor: PluginDescriptor, registry: RegistryProtocol) -> tuple[LoadedPlugin | None, LoadFailure | None]:
        entry = resolve_entry(descriptor)
        if entry is None:
            return None, LoadFailure(descriptor, "No code entry declared in manifest metadata under 'entry'.")

        if entry.type != "module_file":
            return None, LoadFailure(descriptor, f"Unsupported entry type: {entry.type!r}")

        try:
            module_name = self._build_unique_module_name(descriptor, entry)
            module = self._import_module_from_path(module_name, entry)
        except Exception as e:
            tb = traceback.format_exc()
            return None, LoadFailure(descriptor, "Import failure", f"{e!r}\n{tb}")

        try:
            register_fn = getattr(module, entry.attr, None)
            if register_fn is None or not callable(register_fn):
                return None, LoadFailure(descriptor, f"Missing callable entry attr: {entry.attr!r}")
        except Exception as e:
            tb = traceback.format_exc()
            return None, LoadFailure(descriptor, "Failed to access register()", f"{e!r}\n{tb}")

        # Call register() and get exports
        try:
            exports = register_fn(registry)
        except Exception as e:
            tb = traceback.format_exc()
            return None, LoadFailure(descriptor, "register() raised", f"{e!r}\n{tb}")

        # Validate shape of exports
        if not isinstance(exports, dict):
            return None, LoadFailure(descriptor, "register() must return a dict[str, Any] of exports")

        validated = self._validate_exports(descriptor, exports)

        if self._strict_validation and not validated:
            return None, LoadFailure(descriptor, "No valid capabilities exported")

        self._logger.info(
            f"Loaded plugin '{descriptor.name}' v{descriptor.version} "
            f"(API {descriptor.api_version}) with {len(validated)} capabilities.",
            separator=self._separator
        )
        return LoadedPlugin(descriptor=descriptor, module_name=module.__name__, exports=validated), None

    # ----- internals -----------------------------------------------------

    @staticmethod
    def _build_unique_module_name(descriptor: PluginDescriptor, entry: CodeEntry) -> str:
        base = f"{descriptor.identity[0]}_{descriptor.identity[1]}_{descriptor.identity[2]}"
        h = blake2b(str(entry.path).encode("utf-8"), digest_size=6).hexdigest()
        return f"plugins.{base}.{h}"

    def _import_module_from_path(self, module_name: str, entry: CodeEntry) -> ModuleType:
        if self._refresh_import_caches:
            try:
                import importlib
                importlib.invalidate_caches()
            except Exception:
                # Non-fatal: proceed even if cache invalidation fails
                pass

        spec = spec_from_file_location(module_name, str(entry.path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not create spec for {entry.path}")

        module = module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def _validate_exports(self, descriptor: PluginDescriptor, exports: Mapping[str, Any]) -> Dict[str, Any]:
        validated: Dict[str, Any] = {}
        for key, obj in exports.items():
            expected = self._capability_contracts.get(key)
            if expected is None:
                self._logger.debug(
                    f"Ignoring unknown capability '{key}' from {descriptor.name}.",
                    separator=self._separator
                )
                continue

            ok = self._runtime_protocol_check(expected, obj)
            if ok:
                validated[key] = obj
            else:
                self._logger.warning(
                    f"Capability '{key}' from {descriptor.name} does not satisfy its contract; skipping.",
                    separator=self._separator
                )
        return validated

    @staticmethod
    def _runtime_protocol_check(protocol: Type[object], obj: Any) -> bool:
        try:
            return isinstance(obj, protocol)
        except TypeError:
            required = getattr(protocol, "__dict__", {}).get("__annotations__", {})
            for attr in required.keys():
                if not hasattr(obj, attr):
                    return False
            return True
