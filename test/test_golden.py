from pathlib import Path
from typing import Any, Dict

import pytest
import tree_sitter_talon as talon


def node_dict_simplify(node_dict: Dict[str, Any]) -> None:
    if len(node_dict) > 4:
        del node_dict["text"]

    del node_dict["start_position"]
    del node_dict["end_position"]

    for key in node_dict.keys():
        if isinstance(node_dict[key], dict):
            node_dict_simplify(node_dict[key])
        if isinstance(node_dict[key], list):
            for val in node_dict[key]:
                if isinstance(val, dict):
                    node_dict_simplify(val)


@pytest.mark.golden_test("golden/*.yml")
def test_golden(golden):
    node_dict = talon.parse(golden["input"]).to_dict()
    node_dict_simplify(node_dict)
    assert node_dict == golden.out["output"]
