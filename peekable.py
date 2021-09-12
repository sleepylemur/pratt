from typing import Any, Generic, Iterator, TypeVar


T = TypeVar("T")


class Peekable(Generic[T]):
    def __init__(self, items: Iterator[T]) -> None:
        self.items = items
        self.at_end = False
        try:
            self.peek = next(items)
        except StopIteration:
            self.at_end = True

    def __iter__(self) -> "Peekable":
        return self

    def __next__(self) -> T:
        if self.at_end:
            raise StopIteration

        cur = self.peek
        try:
            self.peek = next(self.items)
        except StopIteration:
            self.at_end = True
        return cur

    def eat(self, tok: T) -> bool:
        if self.peek == tok:
            next(self)
            return True
        return False