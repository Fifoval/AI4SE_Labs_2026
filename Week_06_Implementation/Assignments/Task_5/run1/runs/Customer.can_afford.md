# Customer.can_afford

Model: gpt-5-mini

## Prompt

## Task
Implement the method can_afford of class Customer in playground/playground/models.py. """Return True if ``balance + total`` does not exceed the credit limit."""

## Stub to replace
```python
    def can_afford(self, total: Money) -> bool:
        pass
```

## Relevant code from the repository (retrieved)
### Context 1: playground/playground/models.py::Customer.charge (lines 264-268, similarity 0.823)
```python
    def charge(self, total: Money) -> None:
        """Increase the balance by ``total``, raising if the limit would be exceeded."""
        if not self.can_afford(total):
            raise ValueError("credit limit exceeded")
        self._balance = self._balance + total
```

### Context 2: playground/playground/models.py::Customer (lines 221-268, similarity 0.821)
```python
class Customer(Entity):
    """Buyer with a credit limit. Balance is the amount owed."""
    def __init__(self, customer_id: str, name: str, credit_limit: Money = Money(0)) -> None:  ...  # Create a customer with the given identity, name, and credit limit.
    @property def customer_id(self) -> str:  ...  # Return the customer identity.
    @property def name(self) -> str:  ...  # Return the customer name.
    @property def credit_limit(self) -> Money:  ...  # Return the credit limit.
    @property def balance(self) -> Money:  ...  # Return the current outstanding balance.
    def identity(self) -> str:  ...  # Return the customer_id as the entity identity.
    def can_afford(self, total: Money) -> bool:  ...
    def charge(self, total: Money) -> None:  ...  # Increase the balance by ``total``, raising if the limit would be exceeded.
```

### Context 3: playground/tests/test_models.py::CustomerTests.test_can_afford_true_within_limit (lines 449-451, similarity 0.813)
```python
    def test_can_afford_true_within_limit(self) -> None:
        c = Customer("C-1", "A", Money(1000))
        self.assertTrue(c.can_afford(Money(1000)))
```

### Context 4: playground/playground/models.py::Customer.can_afford (lines 261-262, similarity 0.809)
```python
    def can_afford(self, total: Money) -> bool:
        pass
```

### Context 5: playground/tests/test_models.py::CustomerTests.test_can_afford_false_over_limit (lines 453-455, similarity 0.809)
```python
    def test_can_afford_false_over_limit(self) -> None:
        c = Customer("C-1", "A", Money(1000))
        self.assertFalse(c.can_afford(Money(1001)))
```

Write the implementation of the method now.

## Answer (attempt 1)

```python
def can_afford(self, total: Money) -> bool:
    """Return True if ``balance + total`` does not exceed the credit limit."""
    return (self._balance + total) <= self._credit_limit
```
