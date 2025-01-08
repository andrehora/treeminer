// JavaScript calculator
class Calculator {
    
    constructor() {}

    add(a, b) {
        return a + b;
    }

    subtract(a, b) {
        return a - b;
    }

    multiply(a, b) {
        return a * b;
    }

    divide(a, b) {
        if (b === 0) {
            throw new Error("Cannot divide by zero");
        }
        return a / b;
    }
}

// Usage example
const calc = new Calculator();
calc.add(10, 5);
calc.subtract(10, 5);
calc.multiply(10, 5);
calc.divide(10, 5);
