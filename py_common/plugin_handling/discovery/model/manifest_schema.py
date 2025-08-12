from dataclasses import dataclass


@dataclass
class ManifestSchema:
    """
    Minimal, stable manifest contract.
    Required: name, version, api_version.
    Optional: capabilities (list[str]), metadata (dict).
    """
    name_key: str = "name"
    version_key: str = "version"
    api_version_key: str = "api_version"
    capabilities_key: str = "capabilities"
    metadata_key: str = "metadata"
