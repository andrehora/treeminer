# Python calculator
class Calculator:
    
    def __init__(self):
        pass

    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

# Usage example
calc = Calculator()
calc.add(10, 5)
calc.subtract(10, 5)
calc.multiply(10, 5)
calc.divide(10, 5)