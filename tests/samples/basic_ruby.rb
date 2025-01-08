# Ruby calculator
class Calculator
    def initialize
    end
  
    def add(a, b)
      a + b
    end
  
    def subtract(a, b)
      a - b
    end
  
    def multiply(a, b)
      a * b
    end
  
    def divide(a, b)
      if b == 0
        raise 'Cannot divide by zero'
      end
      a / b
    end
  end
  
# Usage example
calc = Calculator.new
calc.add(10, 5)
calc.subtract(10, 5)
calc.multiply(10, 5)
calc.divide(10, 5)
  