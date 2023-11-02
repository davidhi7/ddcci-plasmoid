from typing import Tuple

import pytest as pytest

from ddcci_plasmoid_backend.Node import Node


@pytest.fixture
def sample_nodes() -> Tuple[Node, Node, Node]:
    parent = Node(parent=None, indentation=0)
    child1 = Node(parent=parent, indentation=1, key="key1", value="val1")
    child2 = Node(parent=parent, indentation=1, key="key2", value="val2")
    return parent, child1, child2


def test_init(sample_nodes):
    parent, child1, child2 = sample_nodes
    assert parent.child_by_key["key1"] is child1
    assert parent.child_by_key["key2"] is child2
    assert len(parent.children) == 2
    assert len(parent.child_by_key) == 2


def test_dict(sample_nodes):
    parent, child1, child2 = sample_nodes
    dict_tree = parent.to_dict()
    assert dict_tree == {
        "key": "",
        "value": "",
        "indentation": 0,
        "children": [
            {"key": "key1", "value": "val1", "indentation": 1, "children": []},
            {"key": "key2", "value": "val2", "indentation": 1, "children": []},
        ],
    }


def test_parse_indented_text_basic():
    with open("fixtures/basic/indented.txt") as file:
        lines = file.read().split("\n")
    node = Node.parse_indented_text(lines).to_dict()

    assert node == {
        "key": "",
        "value": "",
        "indentation": -1,
        "children": [
            {
                "key": "Root 1",
                "value": "",
                "indentation": 0,
                "children": [
                    {
                        "key": "Level 1a",
                        "value": "value 1a",
                        "indentation": 1,
                        "children": [
                            {
                                "key": "Level 2a",
                                "value": "value 2a",
                                "indentation": 2,
                                "children": [
                                    {
                                        "key": "Level 3a",
                                        "value": "value 3a",
                                        "indentation": 3,
                                        "children": [],
                                    },
                                    {
                                        "key": "Level 3b",
                                        "value": "value 3b",
                                        "indentation": 3,
                                        "children": [],
                                    },
                                ],
                            }
                        ],
                    },
                    {
                        "key": "Level 1b",
                        "value": "value 1b",
                        "indentation": 1,
                        "children": [
                            {
                                "key": "Level 2b",
                                "value": "value 2b",
                                "indentation": 2,
                                "children": [],
                            }
                        ],
                    },
                ],
            },
            {"key": "Root 2", "value": "", "indentation": 0, "children": []},
        ],
    }
