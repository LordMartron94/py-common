from itertools import chain, pairwise
from typing import Any, Callable, Generator, Iterable, List


class CollectionExtensions:
    @staticmethod
    def split_between(predicate: Callable[[Any, Any], bool], items: Iterable) -> Generator[List[Any], None, None]:
        """Split an iterable into groups based on a predicate function.

        Args:
            predicate (callable): A predicate function that takes two arguments (before and after)
                and returns a boolean value indicating whether to split the group at that point.
            items (iterable): The iterable to split into groups.

        Yields:
            list: A list containing consecutive elements from the input iterable 'items'
                where the predicate function 'pred' returns False for each consecutive pair
                of elements in the yielded list.

        Example:
            Consider an iterable of integers 'numbers' and a predicate function 'is_even'
            that returns True if the current number and the next number are both even.
            We can use split_between to group consecutive even numbers:

            >>> numbers = [2, 4, 6, 3, 8, 10, 7, 9, 12]
            >>> def is_even(before, after):
            ...     return before % 2 == 0 and after % 2 == 0
            ...
            >>> list(split_between(is_even, numbers))
            [[2, 4, 6], [8, 10], [12]]

        Credits:
            Dale from ArjanCodes Python community (server on Discord).
        """
        group = []

        sentinel = object()
        paired_items = chain(items, [sentinel])
        paired_items = pairwise(paired_items)

        for before, after in paired_items:
            if after is sentinel:
                group.append(before)
                yield group
                group = [] # shouldn't loop again
            elif predicate(before, after):
                group.append(before)
                yield group
                group = []
            else:
                group.append(before)

        assert len(group) == 0

    @staticmethod
    def any_match(predicate: Callable[[Any], bool], items: Iterable) -> bool:
        """Return True if any element in 'items' satisfies 'predicate'.

        Args:
            predicate (callable): A function that takes one argument and returns True/False.
            items (iterable): The iterable to test.

        Returns:
            bool: True if predicate(item) is True for at least one item, else False.

        Example:
            >>> numbers = [1, 3, 5, 8, 11]
            >>> CollectionExtensions.any_match(lambda x: x % 2 == 0, numbers)
            True
        """
        for item in items:
            if predicate(item):
                return True
        return False

    @staticmethod
    def more_than(predicate: Callable[[Any], bool], items: Iterable, count: int) -> bool:
        """Return True if predicate(item) is True for more than `count` items in `items`.

        Args:
            predicate (callable): A function taking one argument, returning True/False.
            items (iterable): The iterable to scan.
            count (int): The threshold number of matches.

        Returns:
            bool: True as soon as more than `count` items satisfy the predicate.
        """
        _matches = 0
        for _item in items:
            if predicate(_item):
                _matches += 1
                if _matches > count:
                    return True
        return False
