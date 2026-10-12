import re

LOCATE = re.compile(r"\b(where|locate|highlight|find|point out|bounding box|box)\b", re.I)
DESCRIBE = re.compile(
    r"\b(describe|description|explain|why|summar\w*|increase\w*|decrease\w*|unchanged|how much|how many)\b",
    re.I,
)


def input_config(modalities: list[str]) -> str:
    """Classify the upload into one of the three supported configurations."""
    n = len(modalities)
    if n == 1:
        return "single"
    if n != 2:
        raise ValueError("upload 1 or 2 images")
    if sorted(modalities) == ["optical", "sar"]:
        return "optical_sar"
    if modalities[0] == modalities[1] == "optical":
        return "bitemporal"
    raise ValueError(
        f"unsupported combination {modalities}: use one image, an optical+SAR pair, "
        "or two optical images of different dates"
    )


def route(config: str, query: str) -> list[str]:
    """Return the ordered list of tools to run. Change runs before change-VQA."""
    if config == "optical_sar":
        return ["fusion"]
    if config == "bitemporal":
        return ["change", "change_vqa"] if DESCRIBE.search(query) else ["change"]
    return ["grounding"] if LOCATE.search(query) else ["vqa"]