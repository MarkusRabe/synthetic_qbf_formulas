#!/usr/bin/env python3

from generate_tandems import duplicate

def test_duplicate_universals():
    max_var, clauses, us = duplicate(10, [], [3,5], 3)
    assert max_var == 10 * 3
    assert us.sort() == [3, 5, 13, 15, 23, 25].sort()

def test_duplicate_clauses():
    max_var, clauses, us = duplicate(10, [[1], [2, -1, 3]], [2], 3)
    print(duplicate(10, [[1], [2, -1, 3]], [2], 3))
    assert len(clauses) == 2 * 3

