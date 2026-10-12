import pytest

from controller import router


def test_single_image():
    assert router.input_config(["optical"]) == "single"


def test_optical_sar_pair():
    assert router.input_config(["sar", "optical"]) == "optical_sar"


def test_bitemporal_pair():
    assert router.input_config(["optical", "optical"]) == "bitemporal"


def test_sar_pair_rejected():
    with pytest.raises(ValueError):
        router.input_config(["sar", "sar"])


def test_three_images_rejected():
    with pytest.raises(ValueError):
        router.input_config(["optical", "optical", "optical"])


def test_grounding_route():
    assert router.route("single", "Highlight the water body") == ["grounding"]


def test_vqa_route():
    assert router.route("single", "Describe the land cover") == ["vqa"]


def test_change_route():
    assert router.route("bitemporal", "What changed between these dates?") == ["change"]


def test_change_with_description_route():
    assert router.route("bitemporal", "Describe what changed") == ["change", "change_vqa"]


def test_fusion_route():
    assert router.route("optical_sar", "Identify built-up and water") == ["fusion"]