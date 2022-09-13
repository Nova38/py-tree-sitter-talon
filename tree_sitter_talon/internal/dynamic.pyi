import collections.abc
import dataclasses
import pathlib
import typing

import dataclasses_json
import parsec
import tree_sitter

from .parsec import AnyListValue, AnyTalonRule

################################################################################
# Extended node types (from tree-sitter-type-provider)
################################################################################

class NodeTypeError(Exception):
    pass

@dataclasses.dataclass
class Point:
    line: int
    column: int

    @staticmethod
    def from_tree_sitter(tspoint: tuple[int, int]) -> "Point":
        return Point(line=tspoint[0], column=tspoint[1])

NodeTypeName = str

NodeFieldName = str

@dataclasses.dataclass
class Node(dataclasses_json.DataClassJsonMixin):
    text: str
    type_name: NodeTypeName = dataclasses.field(
        metadata=dataclasses_json.config(field_name="type")
    )
    start_position: Point
    end_position: Point

    def is_extra(self) -> bool: ...
    def is_equivalent(self, other: "Node") -> bool: ...
    def assert_equivalent(self, other: "Node") -> None: ...

@dataclasses.dataclass
class Leaf(Node):
    pass

@dataclasses.dataclass
class Branch(Node):
    children: typing.Union[None, Node, collections.abc.Sequence[Node]]

@dataclasses.dataclass
class ParseError(Exception, Branch):
    children: list[Node]
    contents: typing.Optional[str] = None
    filename: typing.Optional[str] = None

parser: tree_sitter.Parser

language: tree_sitter.Language

def parse(
    contents: typing.Union[str, bytes],
    *,
    encoding: str = "utf-8",
    filename: typing.Optional[str] = None,
    raise_parse_error: bool = False,
) -> Node: ...
def parse_file(
    path: typing.Union[str, pathlib.Path],
    *,
    encoding: str = "utf-8",
    raise_parse_error: bool = False,
) -> Node: ...
def from_tree_sitter(
    tsvalue: typing.Union[tree_sitter.Tree, tree_sitter.Node, tree_sitter.TreeCursor],
    *,
    encoding: str = "utf-8",
    filename: typing.Optional[str] = None,
    raise_parse_error: bool = False,
) -> Node: ...

# AST node classes.

@dataclasses.dataclass
class TalonSourceFile(Branch):
    children: collections.abc.Sequence[
        typing.Union[TalonDeclaration, TalonMatches, TalonComment]
    ]
    def get_docstring(self) -> typing.Optional[str]: ...
    def find_command(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> typing.Optional["TalonCommandDeclaration"]: ...
    def to_parser(
        self,
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ],
    ) -> parsec.Parser: ...

class TalonComment(Leaf):
    def get_docstring(self) -> typing.Optional[str]: ...

@dataclasses.dataclass
class TalonError(Exception, Branch):
    children: collections.abc.Sequence[Node]
    contents: typing.Optional[str] = None
    filename: typing.Optional[str] = None

# Matches.

@dataclasses.dataclass
class TalonMatches(Branch):
    children: collections.abc.Sequence[typing.Union[TalonMatch, TalonComment]]

@dataclasses.dataclass
class TalonMatch(Branch):
    children: collections.abc.Sequence[TalonComment]
    key: TalonIdentifier
    modifier: collections.abc.Sequence[TalonMatchModifier]
    pattern: TalonImplicitString

class TalonMatchModifier(Leaf):
    pass

# Declarations.

class TalonDeclaration(Node):
    pass

@dataclasses.dataclass
class TalonCommandDeclaration(Branch, TalonDeclaration):
    children: collections.abc.Sequence[TalonComment]
    rule: TalonRule
    script: TalonBlock
    def get_docstring(self) -> typing.Optional[str]: ...
    def match(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> bool: ...
    def to_parser(
        self,
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ],
    ) -> parsec.Parser: ...

@dataclasses.dataclass
class TalonKeyBindingDeclaration(Branch, TalonDeclaration):
    children: collections.abc.Sequence[TalonComment]
    key: TalonKeyAction
    script: TalonBlock

@dataclasses.dataclass
class TalonSettingsDeclaration(Branch, TalonDeclaration):
    children: collections.abc.Sequence[typing.Union[TalonBlock, TalonComment]]

    def get_child(self) -> TalonBlock: ...

@dataclasses.dataclass
class TalonTagImportDeclaration(Branch, TalonDeclaration):
    children: collections.abc.Sequence[TalonComment]
    tag: TalonIdentifier

# Rules.

@dataclasses.dataclass
class TalonCapture(Branch):
    children: collections.abc.Sequence[TalonComment]
    capture_name: TalonIdentifier
    def match(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> bool: ...
    def to_parser(
        self,
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ],
    ) -> parsec.Parser: ...

@dataclasses.dataclass
class TalonChoice(Branch):
    children: collections.abc.Sequence[
        typing.Union[
            TalonCapture,
            TalonEndAnchor,
            TalonList,
            TalonOptional,
            TalonParenthesizedRule,
            TalonRepeat,
            TalonRepeat1,
            TalonSeq,
            TalonStartAnchor,
            TalonWord,
            TalonComment,
        ]
    ]
    def match(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> bool: ...
    def to_parser(
        self,
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ],
    ) -> parsec.Parser: ...

class TalonEndAnchor(Leaf):
    def match(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> bool: ...
    def to_parser(
        self,
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ],
    ) -> parsec.Parser: ...

@dataclasses.dataclass
class TalonList(Branch):
    children: collections.abc.Sequence[TalonComment]
    list_name: TalonIdentifier
    def match(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> bool: ...
    def to_parser(
        self,
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ],
    ) -> parsec.Parser: ...

@dataclasses.dataclass
class TalonOptional(Branch):
    children: collections.abc.Sequence[
        typing.Union[
            TalonCapture,
            TalonChoice,
            TalonEndAnchor,
            TalonList,
            TalonOptional,
            TalonParenthesizedRule,
            TalonRepeat,
            TalonRepeat1,
            TalonSeq,
            TalonStartAnchor,
            TalonWord,
            TalonComment,
        ]
    ]
    def get_child(
        self,
    ) -> typing.Union[
        TalonCapture,
        TalonChoice,
        TalonEndAnchor,
        TalonList,
        TalonOptional,
        TalonParenthesizedRule,
        TalonRepeat,
        TalonRepeat1,
        TalonSeq,
        TalonStartAnchor,
        TalonWord,
    ]: ...
    def match(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> bool: ...
    def to_parser(
        self,
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ],
    ) -> parsec.Parser: ...

@dataclasses.dataclass
class TalonParenthesizedRule(Branch):
    children: collections.abc.Sequence[
        typing.Union[
            TalonCapture,
            TalonChoice,
            TalonEndAnchor,
            TalonList,
            TalonOptional,
            TalonParenthesizedRule,
            TalonRepeat,
            TalonRepeat1,
            TalonSeq,
            TalonStartAnchor,
            TalonWord,
            TalonComment,
        ]
    ]
    def get_child(
        self,
    ) -> typing.Union[
        TalonCapture,
        TalonChoice,
        TalonEndAnchor,
        TalonList,
        TalonOptional,
        TalonParenthesizedRule,
        TalonRepeat,
        TalonRepeat1,
        TalonSeq,
        TalonStartAnchor,
        TalonWord,
    ]: ...
    def match(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> bool: ...
    def to_parser(
        self,
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ],
    ) -> parsec.Parser: ...

@dataclasses.dataclass
class TalonRepeat(Branch):
    children: collections.abc.Sequence[
        typing.Union[
            TalonCapture,
            TalonList,
            TalonOptional,
            TalonParenthesizedRule,
            TalonRepeat,
            TalonRepeat1,
            TalonWord,
            TalonComment,
        ]
    ]
    def get_child(
        self,
    ) -> typing.Union[
        TalonCapture,
        TalonList,
        TalonOptional,
        TalonParenthesizedRule,
        TalonRepeat,
        TalonRepeat1,
        TalonWord,
    ]: ...
    def match(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> bool: ...
    def to_parser(
        self,
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ],
    ) -> parsec.Parser: ...

@dataclasses.dataclass
class TalonRepeat1(Branch):
    children: collections.abc.Sequence[
        typing.Union[
            TalonCapture,
            TalonList,
            TalonOptional,
            TalonParenthesizedRule,
            TalonRepeat,
            TalonRepeat1,
            TalonWord,
            TalonComment,
        ]
    ]
    def get_child(
        self,
    ) -> typing.Union[
        TalonCapture,
        TalonList,
        TalonOptional,
        TalonParenthesizedRule,
        TalonRepeat,
        TalonRepeat1,
        TalonWord,
    ]: ...
    def match(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> bool: ...
    def to_parser(
        self,
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ],
    ) -> parsec.Parser: ...

@dataclasses.dataclass
class TalonRule(Branch):
    children: collections.abc.Sequence[
        typing.Union[
            TalonCapture,
            TalonChoice,
            TalonEndAnchor,
            TalonList,
            TalonOptional,
            TalonParenthesizedRule,
            TalonRepeat,
            TalonRepeat1,
            TalonSeq,
            TalonStartAnchor,
            TalonWord,
            TalonComment,
        ]
    ]
    def match(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> bool: ...
    def to_parser(
        self,
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ],
    ) -> parsec.Parser: ...

@dataclasses.dataclass
class TalonSeq(Branch):
    children: collections.abc.Sequence[
        typing.Union[
            TalonCapture,
            TalonList,
            TalonOptional,
            TalonParenthesizedRule,
            TalonRepeat,
            TalonRepeat1,
            TalonWord,
            TalonComment,
        ]
    ]
    def match(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> bool: ...
    def to_parser(
        self,
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ],
    ) -> parsec.Parser: ...

class TalonStartAnchor(Leaf):
    def match(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> bool: ...
    def to_parser(
        self,
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ],
    ) -> parsec.Parser: ...

class TalonWord(Leaf):
    def match(
        self,
        text: collections.abc.Sequence[str],
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ] = None,
    ) -> bool: ...
    def to_parser(
        self,
        *,
        fullmatch: bool = False,
        get_capture: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyTalonRule]]
        ] = None,
        get_list: typing.Optional[
            collections.abc.Callable[[str], typing.Optional[AnyListValue]]
        ],
    ) -> parsec.Parser: ...

# Statements.

class TalonStatement(Node):
    pass

@dataclasses.dataclass
class TalonAssignmentStatement(Branch, TalonStatement):
    children: collections.abc.Sequence[TalonComment]
    left: TalonIdentifier
    right: TalonExpression

@dataclasses.dataclass
class TalonExpressionStatement(Branch, TalonStatement):
    children: collections.abc.Sequence[TalonComment]
    expression: TalonExpression

@dataclasses.dataclass
class TalonBlock(Branch):
    children: collections.abc.Sequence[typing.Union[TalonStatement, TalonComment]]

# Expressions.

class TalonExpression(Node):
    pass

@dataclasses.dataclass
class TalonAction(Branch, TalonExpression):
    children: collections.abc.Sequence[TalonComment]
    action_name: TalonIdentifier
    arguments: TalonArgumentList

@dataclasses.dataclass
class TalonArgumentList(Branch):
    children: collections.abc.Sequence[typing.Union[TalonExpression, TalonComment]]

@dataclasses.dataclass
class TalonBinaryOperator(Branch, TalonExpression):
    children: collections.abc.Sequence[TalonComment]
    left: TalonExpression
    operator: TalonOperator
    right: TalonExpression

@dataclasses.dataclass
class TalonKeyAction(Branch, TalonExpression):
    children: collections.abc.Sequence[TalonComment]
    arguments: TalonImplicitString

@dataclasses.dataclass
class TalonParenthesizedExpression(Branch, TalonExpression):
    children: collections.abc.Sequence[typing.Union[TalonExpression, TalonComment]]

    def get_child(self) -> TalonExpression: ...

@dataclasses.dataclass
class TalonSleepAction(Branch, TalonExpression):
    children: collections.abc.Sequence[TalonComment]
    arguments: TalonImplicitString

@dataclasses.dataclass
class TalonVariable(Branch, TalonExpression):
    children: collections.abc.Sequence[TalonComment]
    variable_name: TalonIdentifier

# Identifiers.

class TalonIdentifier(Leaf):
    pass

class TalonOperator(Leaf):
    pass

# Strings.

class TalonImplicitString(Leaf):
    pass

@dataclasses.dataclass
class TalonInterpolation(Branch):
    children: collections.abc.Sequence[typing.Union[TalonExpression, TalonComment]]

    def get_child(self) -> TalonExpression: ...

@dataclasses.dataclass
class TalonString(Branch):
    children: collections.abc.Sequence[
        typing.Union[
            TalonInterpolation,
            TalonStringContent,
            TalonStringEscapeSequence,
            TalonComment,
        ]
    ]

class TalonStringContent(Leaf):
    pass

class TalonStringEscapeSequence(Leaf):
    pass

# Numbers.

class TalonFloat(Leaf, TalonNumber):
    pass

class TalonInteger(Leaf, TalonNumber):
    pass

class TalonNumber(Node):
    pass
