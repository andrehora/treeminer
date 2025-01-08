// TypeScript calculator
class Calculator {

    constructor() {}

    add(a: number, b: number): number {
        return a + b;
    }

    subtract(a: number, b: number): number {
        return a - b;
    }

    multiply(a: number, b: number): number {
        return a * b;
    }

    divide(a: number, b: number): number {
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
