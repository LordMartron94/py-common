from typing import Type, TypeVar, get_args

T = TypeVar("T")

def parse_literal(value: str, literal_type: Type[T]) -> T:
    allowed_values = get_args(literal_type)
    if value in allowed_values:
        return value
    raise ValueError(f"{value!r} is not a valid literal. Allowed: {allowed_values}")
