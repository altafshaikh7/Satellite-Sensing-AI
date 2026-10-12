from pathlib import Path

import yaml

_SPEC = yaml.safe_load((Path(__file__).parent / "tools.yaml").read_text(encoding="utf-8"))["tools"]


class ParamError(ValueError):
    pass


def tool_names() -> list[str]:
    return list(_SPEC.keys())


def tool_spec(tool: str) -> dict:
    if tool not in _SPEC:
        raise ParamError(f"unknown tool '{tool}'")
    return _SPEC[tool]


def validate_params(tool: str, params: dict) -> dict:
    """Return a complete, checked parameter dict, or raise ParamError."""
    rules = tool_spec(tool)["params"]

    for key in params:
        if key not in rules:
            raise ParamError(f"{tool}: parameter '{key}' is not permitted")

    out: dict = {}
    for key, rule in rules.items():
        value = params.get(key, rule["default"])
        kind = rule["type"]
        if kind == "int":
            if isinstance(value, bool) or not isinstance(value, int):
                raise ParamError(f"{tool}.{key} must be an int")
        elif kind == "float":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ParamError(f"{tool}.{key} must be a number")
            value = float(value)
        elif kind == "str":
            if not isinstance(value, str):
                raise ParamError(f"{tool}.{key} must be a string")
        if "choices" in rule and value not in rule["choices"]:
            raise ParamError(f"{tool}.{key}={value} not in {rule['choices']}")
        if "range" in rule:
            lo, hi = rule["range"]
            if not (lo <= value <= hi):
                raise ParamError(f"{tool}.{key}={value} outside [{lo}, {hi}]")
        out[key] = value
    return out