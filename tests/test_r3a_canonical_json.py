import json

from utils.canonical_json import canonical_dumps, canonical_json_line


def test_canonical_json_line_has_single_trailing_newline():
    s = canonical_json_line({"b": 1, "a": 2})
    assert s.endswith("\n")
    assert s.count("\n") == 1


def test_canonical_dumps_is_sorted_and_minified_and_ascii():
    s = canonical_dumps({"b": 1, "a": "é"})
    # sorted keys: a before b
    assert s.startswith('{"a":"')
    # minified: no spaces after commas/colons
    assert ": " not in s and ", " not in s
    # ascii escaped
    assert "\\u00e9" in s


def test_roundtrip_json_loads():
    s = canonical_dumps({"x": 1, "y": [True, None, "z"]})
    obj = json.loads(s)
    assert obj["x"] == 1
