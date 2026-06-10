# flake8: noqa: E501
# pylint: disable=C0301,C0116

"""
Unit tests for the Node tree utility: construction, traversal, ancestry, and serialization.
"""

from typing import Any

import pytest

from bear_tools.node import Node

# -------------------------
# Helpers
# -------------------------

def _build_linear_chain() -> tuple[Node[str], Node[str], Node[str], Node[str]]:
    """Build a linear chain root -> a -> b -> c and return all four nodes."""
    root: Node[str] = Node('root')
    a: Node[str] = Node('a', parent=root)
    b: Node[str] = Node('b', parent=a)
    c: Node[str] = Node('c', parent=b)
    root.children = [a]
    a.children = [b]
    b.children = [c]
    return root, a, b, c


def _build_balanced_tree() -> dict[str, Node[str]]:
    """
    Build a small tree::

            root
           /    \\
          a      b
         / \\
        c   d

    and return a mapping of label -> node.
    """
    root: Node[str] = Node('root')
    a: Node[str] = Node('a', parent=root)
    b: Node[str] = Node('b', parent=root)
    c: Node[str] = Node('c', parent=a)
    d: Node[str] = Node('d', parent=a)
    root.children = [a, b]
    a.children = [c, d]
    return {'root': root, 'a': a, 'b': b, 'c': c, 'd': d}


# -------------------------
# Tests for __init__()
# -------------------------

def test_init_defaults() -> None:
    node: Node[Any] = Node()
    assert node.data is None
    assert node.children == []
    assert node.parent is None


def test_init_with_data() -> None:
    node: Node[int] = Node(42)
    assert node.data == 42
    assert node.children == []
    assert node.parent is None


def test_init_with_children() -> None:
    child1: Node[str] = Node('child1')
    child2: Node[str] = Node('child2')
    parent: Node[str] = Node('parent', children=[child1, child2])
    assert parent.children == [child1, child2]


def test_init_with_parent() -> None:
    root: Node[str] = Node('root')
    child: Node[str] = Node('child', parent=root)
    assert child.parent is root


def test_init_children_default_is_independent() -> None:
    # The mutable default must not be shared between instances
    node1: Node[Any] = Node()
    node2: Node[Any] = Node()
    node1.children.append(Node('x'))
    assert node2.children == []


def test_init_children_not_a_list_raises() -> None:
    with pytest.raises(TypeError, match='children must be a list of Node objects'):
        Node('root', children='not a list')  # type: ignore[arg-type]


def test_init_children_contains_non_node_raises() -> None:
    with pytest.raises(TypeError, match='children must be a list of Node objects'):
        Node('root', children=[Node('ok'), 'not a node'])  # type: ignore[list-item]


def test_init_data_can_be_falsy() -> None:
    values: list[Any] = [0, '', False, []]
    for value in values:
        node: Node[Any] = Node(value)
        assert node.data == value


# -------------------------
# Tests for is_leaf
# -------------------------

def test_is_leaf_true_for_childless_node() -> None:
    node: Node[str] = Node('leaf')
    assert node.is_leaf is True


def test_is_leaf_false_for_node_with_children() -> None:
    parent: Node[str] = Node('parent', children=[Node('child')])
    assert parent.is_leaf is False


# -------------------------
# Tests for __str__()
# -------------------------

def test_str_single_node() -> None:
    node: Node[str] = Node('root')
    assert str(node) == 'root\n'


def test_str_nested_tree_indentation() -> None:
    tree = _build_balanced_tree()
    expected = (
        'root\n'
        '    a\n'
        '        c\n'
        '        d\n'
        '    b\n'
    )
    assert str(tree['root']) == expected


def test_str_uses_data_repr_via_fstring() -> None:
    node: Node[int] = Node(123)
    assert str(node) == '123\n'


# -------------------------
# Tests for get_ancestors()
# -------------------------

def test_get_ancestors_root_has_none() -> None:
    root, _a, _b, _c = _build_linear_chain()
    assert not root.get_ancestors()


def test_get_ancestors_orders_nearest_first() -> None:
    root, a, b, c = _build_linear_chain()
    assert c.get_ancestors() == [b, a, root]


def test_get_ancestors_middle_node() -> None:
    root, a, b, _c = _build_linear_chain()
    assert b.get_ancestors() == [a, root]


# -------------------------
# Tests for breadth_first_traversal()
# -------------------------

def test_bft_single_node() -> None:
    node: Node[str] = Node('root')
    assert [n.data for n in node.breadth_first_traversal()] == ['root']


def test_bft_visits_level_by_level() -> None:
    tree = _build_balanced_tree()
    order = [n.data for n in tree['root'].breadth_first_traversal()]
    assert order == ['root', 'a', 'b', 'c', 'd']


def test_bft_yields_node_instances() -> None:
    tree = _build_balanced_tree()
    nodes = list(tree['root'].breadth_first_traversal())
    assert all(isinstance(n, Node) for n in nodes)
    assert nodes[0] is tree['root']


# -------------------------
# Tests for depth_first_traversal()
# -------------------------

def test_dft_single_node() -> None:
    node: Node[str] = Node('root')
    assert [n.data for n in node.depth_first_traversal()] == ['root']


def test_dft_preorder() -> None:
    tree = _build_balanced_tree()
    order = [n.data for n in tree['root'].depth_first_traversal()]
    assert order == ['root', 'a', 'c', 'd', 'b']


def test_dft_linear_chain() -> None:
    root, _a, _b, _c = _build_linear_chain()
    order = [n.data for n in root.depth_first_traversal()]
    assert order == ['root', 'a', 'b', 'c']


# -------------------------
# Tests for to_dict()
# -------------------------

def test_to_dict_leaf() -> None:
    node: Node[str] = Node('leaf')
    assert node.to_dict() == {'leaf': []}


def test_to_dict_nested() -> None:
    tree = _build_balanced_tree()
    assert tree['root'].to_dict() == {
        'root': [
            {'a': [{'c': []}, {'d': []}]},
            {'b': []},
        ]
    }


def test_to_dict_none_data() -> None:
    node: Node[Any] = Node()
    assert node.to_dict() == {None: []}


# -------------------------
# Generic typing smoke test
# -------------------------

def test_supports_arbitrary_data_types() -> None:
    payload = {'key': 'value'}
    node: Node[dict[str, str]] = Node(payload)
    assert node.data == payload
    assert node.is_leaf is True


def test_to_dict_requires_hashable_data() -> None:
    # to_dict() uses node data as a dict key, so unhashable data raises
    node: Node[Any] = Node(['unhashable'])
    with pytest.raises(TypeError):
        node.to_dict()
