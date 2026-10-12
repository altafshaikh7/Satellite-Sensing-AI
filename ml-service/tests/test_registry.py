import pytest

from registry.registry import ParamError, validate_params


def test_defaults_applied():
    assert validate_params("change", {})["min_area_px"] == 50


def test_unknown_tool_rejected():
    with pytest.raises(ParamError):
        validate_params("hacked_tool", {})


def test_unknown_parameter_rejected():
    with pytest.raises(ParamError):
        validate_params("change", {"threshold_hack": 1})


def test_range_enforced():
    with pytest.raises(ParamError):
        validate_params("change", {"min_area_px": 0})


def test_choice_enforced():
    with pytest.raises(ParamError):
        validate_params("vqa", {"adapter": "unknown_adapter"})


def test_wrong_type_rejected():
    with pytest.raises(ParamError):
        validate_params("change", {"min_area_px": "fifty"})


def test_float_param_accepts_int():
    out = validate_params("fusion", {"water_ndwi_min": 0})
    assert out["water_ndwi_min"] == 0.0