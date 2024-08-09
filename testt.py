class A:
    def __iter__(self):
        return iter([])
    
from collections.abc import Iterable

print(isinstance(A(), Iterable))
