# Money.__bool__

Model: gpt-5-mini

## Prompt

## Task
Implement the method __bool__ of class Money in playground/playground/models.py. """Return True when the amount is non-zero."""

## Stub to replace
```python
    def __bool__(self) -> bool:
        pass
```

## Imports of the target file (the only external names available there)
```python
from __future__ import annotations
from typing import Mapping
from .base import Entity
from .enums import Category
from .util import ensure_positive_int, format_cents, normalize_sku
```

## Relevant code from the repository (retrieved)
### Context 1: playground/playground/models.py::Money (lines 12-91, similarity 0.832)
```python
class Money:
    """Immutable integer-cents amount."""
    def __init__(self, cents: int = 0) -> None:  ...  # Create a monetary amount; cents must be a non-negative ``int``.
    @property def cents(self) -> int:  ...  # Return the stored cents value.
    def __add__(self, other: Money) -> Money:  ...  # Return a new Money equal to ``self + other``.
    def __sub__(self, other: Money) -> Money:  ...  # Return a new Money equal to ``self - other``.
    def __mul__(self, factor: int) -> Money:  ...  # Return ``self`` multiplied by a non-negative integer.
    def __rmul__(self, factor: int) -> Money:  ...  # Support ``factor * Money`` by delegating to :meth:`__mul__`.
    def __eq__(self, other: object) -> bool:  ...  # Return True if ``other`` is Money with equal cents.
    def __lt__(self, other: Money) -> bool:  ...  # Return True if ``self`` is strictly less than ``other``.
    def __le__(self, other: Money) -> bool:  ...  # Return True if ``self`` is less than or equal to ``other``.
    def __hash__(self) -> int:  ...  # Hash by the type name and cents value.
    def __repr__(self) -> str:  ...  # Return a developer-friendly representation.
    def __str__(self) -> str:  ...  # Render the amount as a ``$X.YY`` string.
    def __bool__(self) -> bool:  ...
```

### Context 2: playground/playground/models.py::Money.__mul__ (lines 48-54, similarity 0.806)
```python
    def __mul__(self, factor: int) -> Money:
        """Return ``self`` multiplied by a non-negative integer."""
        if isinstance(factor, bool) or not isinstance(factor, int):
            raise TypeError("factor must be int")
        if factor < 0:
            raise ValueError("factor cannot be negative")
        return Money(self._cents * factor)
```

### Context 3: playground/playground/models.py::Money.__init__ (lines 15-21, similarity 0.797)
```python
    def __init__(self, cents: int = 0) -> None:
        """Create a monetary amount; cents must be a non-negative ``int``."""
        if isinstance(cents, bool) or not isinstance(cents, int):
            raise TypeError("cents must be int")
        if cents < 0:
            raise ValueError("money cannot be negative")
        self._cents = cents
```

### Context 4: playground/playground/models.py::Money.__eq__ (lines 60-64, similarity 0.795)
```python
    def __eq__(self, other: object) -> bool:
        """Return True if ``other`` is Money with equal cents."""
        if not isinstance(other, Money):
            return NotImplemented
        return self._cents == other._cents
```

### Context 5: playground/tests/test_models.py::MoneyMiscTests.test_bool_false_for_zero (lines 171-172, similarity 0.790)
```python
    def test_bool_false_for_zero(self) -> None:
        self.assertFalse(bool(Money(0)))
```

Write the implementation of the method now.

## Answer (attempt 1)

```python
def __bool__(self) -> bool:
    """Return True when the amount is non-zero."""
    return self._cents != 0
```
