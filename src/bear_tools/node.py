"""
A generic tree-node utility for building and traversing hierarchical data.

This module provides a :class:`Node` class for constructing trees of arbitrary
data, along with helpers for traversal (breadth-first and depth-first),
ancestor lookup, and serialization to a nested dictionary.
"""

from __future__ import annotations

from collections import deque
from typing import Generic, Iterator, TypeVar

T = TypeVar('T')


class Node(Generic[T]):
    """
    A node for making trees
    """

    def __init__(
        self,
        data: T | None = None,
        children: list[Node[T]] | None = None,
        parent: Node[T] | None = None,
    ) -> None:
        """
        Initializer

        :param data: Data to save to the node. Can be any type
        :param children: List of Node objects representing the hierarchical children of this node
        :param parent: The direct ancestor of this node in the tree
        """

        if children is None:
            children = []

        if not isinstance(children, list) or not all(isinstance(child, Node) for child in children):
            raise TypeError('children must be a list of Node objects')

        self.data = data
        self.children = children
        self.parent = parent


    @property
    def is_leaf(self) -> bool:
        """
        Determine whether the node is a leaf in the tree (i.e. has no children) or not
        """

        return not self.children


    def __str__(self) -> str:
        """
        Get a formatted string representing the tree starting with this node
        """

        indent = ' ' * 4

        def get_tree_str(node: Node[T], depth: int) -> str:
            s = f'{indent * depth}{node.data}\n'
            for child in node.children:
                s += get_tree_str(child, depth + 1)

            return s

        return get_tree_str(self, 0)


    def get_ancestors(self) -> list[Node[T]]:
        """
        Get the list of this node's ancestors, ordered from the immediate parent up to the root

        :return: A list of ancestors of this node
        """

        ancestors: list[Node[T]] = []
        cursor = self.parent
        while cursor is not None:
            ancestors.append(cursor)
            cursor = cursor.parent

        return ancestors


    def breadth_first_traversal(self) -> Iterator[Node[T]]:
        """
        <Generator method>

        Perform a breadth-first traversal of the tree rooted at this node, yielding each node as it is encountered

        :return: The current node in the breadth-first traversal
        """

        queue: deque[Node[T]] = deque([self])
        while queue:
            current_node = queue.popleft()
            yield current_node
            queue.extend(current_node.children)


    def depth_first_traversal(self) -> Iterator[Node[T]]:
        """
        <Generator method>

        Perform a depth-first (pre-order) traversal of the tree rooted at this node, yielding each node as it is
        encountered

        :return: The current node in the depth-first traversal
        """

        stack: list[Node[T]] = [self]
        while stack:
            current_node = stack.pop(0)
            yield current_node
            stack = current_node.children + stack


    def to_dict(self) -> dict[T | None, list]:
        """
        Create a nested dict from the tree rooted at this node

        :return: A dict that mirrors the data in the tree starting at this node
        """

        if self.is_leaf:
            return {self.data: []}

        return {self.data: [child.to_dict() for child in self.children]}
