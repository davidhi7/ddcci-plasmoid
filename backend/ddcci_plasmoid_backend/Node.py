from __future__ import annotations

from dataclasses import field


class Node:
    parent: Node | None
    indentation: int
    key: str
    value: str
    children: list[Node] = field(default_factory=list)

    child_by_key: dict[str, Node]

    def __init__(
        self, parent: Node | None, indentation: int, key: str = "", value: str = ""
    ):
        """
        Create a new node and set it as the child of the parent.
        """
        self.parent = parent
        self.key = key
        self.value = value
        self.indentation = indentation

        self.children = []
        self.child_by_key = {}

        if parent is not None:
            self.parent._register_child(self)

    def to_dict(self) -> dict[str | list[dict]]:
        """
        Return a representation of this node as a recursive dictionary, removing the `parent` attribute in the process.
        This dict can be used for serialization or testing.
        """
        return {
            "key": self.key,
            "value": self.value,
            "indentation": self.indentation,
            "children": [child.to_dict() for child in self.children],
        }

    def _register_child(self, child: Node) -> None:
        """
        Register a new child
        """
        self.children.append(child)
        self.child_by_key[child.key] = child

    @staticmethod
    def parse_indented_text(text: list[str]) -> Node:
        """
        Parse indented output from for example `ddcutil` into nested nodes
        """
        root = Node(parent=None, indentation=-1)
        previous = root

        for line in text:
            if len(line.lstrip()) == 0:
                continue

            # ddcutil output is indented by a multiple of 3 whitespaces
            indentation_characters = len(line) - len(line.lstrip())
            if indentation_characters % 3 != 0:
                raise ValueError(
                    f'Indentation whitespace count of line "{line.strip()}" is not a multiple of 3'
                )

            tokens = line.split(":")
            key = tokens[0].strip()
            value = tokens[1].strip() if len(tokens) > 1 else ""

            indentation = indentation_characters // 3
            if indentation == previous.indentation:
                # this line is at the same level as `previous`
                new_node = Node(
                    parent=previous.parent,
                    key=key,
                    value=value,
                    indentation=indentation,
                )
                previous = new_node
            elif indentation > previous.indentation:
                # this line is a child of `previous`
                new_node = Node(
                    parent=previous, key=key, value=value, indentation=indentation
                )
                previous = new_node
            elif indentation < previous.indentation:
                # this line is a parent of `previous`, either a direct or a deeper parent

                parent = previous.parent
                while parent.indentation >= indentation:
                    parent = parent.parent

                new_node = Node(
                    parent=parent, key=key, value=value, indentation=indentation
                )
                previous = new_node

        return root
