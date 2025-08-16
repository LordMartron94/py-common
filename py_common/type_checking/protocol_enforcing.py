from inspect import Signature, signature, Parameter
from typing import get_type_hints, Any, Type


def _resolved_return_annotation(func) -> Any:
    try:
        hints = get_type_hints(func, include_extras=True)
    except Exception:
        return signature(func).return_annotation
    return hints.get('return', Signature.empty)


# noinspection t
def protocol_signatures_check_minimally_valid(obj: object, proto: Type[Any]) -> list[str]:
    if not getattr(proto, "_is_protocol", False):
        raise TypeError(f"{proto!r} is not a typing.Protocol subclass")

    errors: list[str] = []
    for name, proto_attr in proto.__dict__.items():
        if name.startswith('_') or not callable(proto_attr):
            continue
        impl = getattr(obj, name, None)
        if impl is None or not callable(impl):
            errors.append(f"Missing callable: {name}")
            continue

        expected = signature(proto_attr)
        actual = signature(impl)

        # Drop 'self' from protocol method params
        exp_params = list(expected.parameters.values())
        if exp_params and exp_params[0].name == "self":
            exp_params = exp_params[1:]
        expected_no_self = expected.replace(parameters=exp_params)

        # --- parameter compatibility (name-strict for required args) ---
        pos_args, kwargs = [], {}
        for p in expected_no_self.parameters.values():
            if p.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
                continue
            if p.default is not Parameter.empty:
                continue
            if p.kind == Parameter.POSITIONAL_ONLY:
                pos_args.append(object())
            else:
                kwargs[p.name] = object()

        try:
            actual.bind_partial(*pos_args, **kwargs)
        except TypeError as e:
            errors.append(f"{name} has incompatible signature: {e}")
            continue

        # --- return type check (strict by default) ---
        exp_ret = _resolved_return_annotation(proto_attr)
        act_ret = _resolved_return_annotation(impl)

        if exp_ret is not Signature.empty:
            if act_ret is Signature.empty:
                errors.append(f"{name} missing return annotation (expected {exp_ret!r})")
            else:
                if act_ret != exp_ret:
                    if not (isinstance(exp_ret, type) and isinstance(act_ret, type) and issubclass(act_ret, exp_ret)):
                        errors.append(f"{name} has return type {act_ret!r}, expected {exp_ret!r}")

    return errors
