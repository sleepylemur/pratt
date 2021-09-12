from dataclasses import dataclass
import re
from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    Literal,
    Union,
)
from peekable import Peekable

Token = str

Assoc = Union[Literal["left"], Literal["right"]]


@dataclass
class Binary:
    token: str
    assoc: Assoc
    prec: int
    eval: Callable[[Any, Any], Any]


@dataclass
class UnaryPrefix:
    token: str
    prec: int
    eval: Callable[[Any], Any]


@dataclass
class UnaryPostfix:
    token: str
    prec: int
    eval: Callable[[Any], Any]


@dataclass
class Group:
    open: str
    close: str


Op = Union[Binary, UnaryPrefix, UnaryPostfix, Group]


class Parser:
    def __init__(self, literal_regex: str, operators: Iterable[Op]):
        self.prec = {}
        self.binary = set()
        self.unary_prefix = set()
        self.unary_postfix = set()
        self.assoc_left = set()
        self.groups = {}
        self.eval: dict[str, Callable] = {}
        regexes = [literal_regex]
        for operator in operators:
            if isinstance(operator, Binary):
                regexes.append(f"({re.escape(operator.token)})")
                self.eval[operator.token] = operator.eval
                self.prec[operator.token] = operator.prec
                self.binary.add(operator.token)
                if operator.assoc == "left":
                    self.assoc_left.add(operator.token)
            elif isinstance(operator, UnaryPrefix):
                self.eval[operator.token] = operator.eval
                regexes.append(f"({re.escape(operator.token)})")
                self.prec[operator.token] = operator.prec
                self.unary_prefix.add(operator.token)
            elif isinstance(operator, UnaryPostfix):
                self.eval[operator.token] = operator.eval
                regexes.append(f"({re.escape(operator.token)})")
                self.prec[operator.token] = operator.prec
                self.unary_postfix.add(operator.token)
            elif isinstance(operator, Group):
                regexes.append(f"({re.escape(operator.open)})")
                regexes.append(f"({re.escape(operator.close)})")
                self.groups[operator.open] = operator.close
        self.token_regex = re.compile("|".join(regexes))

    def tokenize(self, s: str) -> Iterator[Token]:
        return (m.group() for m in self.token_regex.finditer(s))

    def to_ast(self, tokens: Iterator[Token]):
        return self._parse(Peekable(tokens))

    def _no_left(self, p):
        if p.peek in self.groups:
            end = self.groups[p.peek]
            next(p)
            res = self._parse(p, 0)
            assert next(p) == end
            return res
        if p.peek in self.unary_prefix:
            return [next(p), self._no_left(p)]
        return next(p)

    def _parse(self, p, precedence=0):
        res = self._no_left(p)
        while not p.at_end:
            if p.peek in self.binary:
                if p.peek in self.assoc_left:
                    if self.prec[p.peek] <= precedence:
                        break
                else:
                    if self.prec[p.peek] < precedence:
                        break
                op = next(p)
                res = [op, res, self._parse(p, self.prec[op])]
            elif p.peek in self.unary_postfix:
                op = next(p)
                res = [op, res]
            else:
                break
        return res

    def eval_ast(self, ast):
        if isinstance(ast, list):
            return self.eval[ast[0]](*map(self.eval_ast, ast[1:]))
        return float(ast)


if __name__ == "__main__":
    p = Parser(
        literal_regex=r"[0-9]+",
        operators=[
            Binary(token="+", assoc="left", prec=1, eval=lambda a, b: a + b),
            Binary(token="*", assoc="left", prec=2, eval=lambda a, b: a * b),
            UnaryPrefix(token="~", prec=3, eval=lambda a: a * -1),
            Group(open="(", close=")"),
        ],
    )
    ast = p.to_ast(p.tokenize("1 + ~(2 + 3) * 4 + 5"))
    print(ast)
    print(p.eval_ast(ast))
