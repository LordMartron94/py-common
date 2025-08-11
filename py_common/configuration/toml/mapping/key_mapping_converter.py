from typing import Dict


def get_model_key(key_mapping: Dict[str, str] | None, configuration_key: str) -> str | None:
    if not key_mapping:
        return configuration_key

    if configuration_key not in key_mapping:
        return None

    return key_mapping[configuration_key]
