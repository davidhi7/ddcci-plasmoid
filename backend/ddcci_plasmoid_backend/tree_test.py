from typing import Tuple

import pytest as pytest

from ddcci_plasmoid_backend.tree import Node


@pytest.fixture
def sample_nodes_1() -> Tuple[Node, Node, Node]:
    parent = Node(parent=None, indentation=0)
    child1 = Node(parent=parent, indentation=1, key='key1', value='val1')
    child2 = Node(parent=parent, indentation=1, key='key2', value='val2')
    return parent, child1, child2


@pytest.fixture
def sample_nodes_2() -> Node:
    with open('fixtures/nodes/node.txt', 'r') as file:
        lines = file.read().split('\n')
    return Node.parse_indented_text(lines)


def test_init(sample_nodes_1):
    parent, child1, child2 = sample_nodes_1
    assert parent.child_by_key['key1'] is child1
    assert parent.child_by_key['key2'] is child2
    assert len(parent.children) == 2
    assert len(parent.child_by_key) == 2


def test_dict(sample_nodes_1):
    parent, child1, child2 = sample_nodes_1
    dict_tree = parent.to_dict()
    assert dict_tree == {
        'key': '',
        'value': '',
        'indentation': 0,
        'children': [
            {
                'key': 'key1',
                'value': 'val1',
                'indentation': 1,
                'children': []
            },
            {
                'key': 'key2',
                'value': 'val2',
                'indentation': 1,
                'children': []
            }
        ]
    }


def test_walk(sample_nodes_2):
    assert sample_nodes_2.walk('Root 1', 'Level 1a') == 'value 1a'
    assert sample_nodes_2.walk('Root 1', 'Level 1a', 'Level 2a', 'Level 3b') == 'value 3b'


def test_walk_error(sample_nodes_2):
    with pytest.raises(ValueError):
        assert sample_nodes_2.walk('Root 1', 'invalid child key') == 'value 1a'


def test_parse_indented_text_basic(sample_nodes_2):
    assert sample_nodes_2.to_dict() == {
        'key': '',
        'value': '',
        'indentation': -1,
        'children': [
            {
                'key': 'Root 1',
                'value': '',
                'indentation': 0,
                'children': [
                    {
                        'key': 'Level 1a',
                        'value': 'value 1a',
                        'indentation': 1,
                        'children': [
                            {
                                'key': 'Level 2a',
                                'value': 'value 2a',
                                'indentation': 2,
                                'children': [
                                    {
                                        'key': 'Level 3a',
                                        'value': 'value 3a',
                                        'indentation': 3,
                                        'children': []
                                    }, {
                                        'key': 'Level 3b',
                                        'value': 'value 3b',
                                        'indentation': 3,
                                        'children': []
                                    }
                                ]
                            }
                        ]
                    }, {
                        'key': 'Level 1b',
                        'value': 'value 1b',
                        'indentation': 1,
                        'children': [
                            {
                                'key': 'Level 2b',
                                'value': 'value 2b',
                                'indentation': 2,
                                'children': []
                            }
                        ]
                    }
                ]
            }, {
                'key': 'Root 2',
                'value': '',
                'indentation': 0,
                'children': []
            }
        ]
    }
