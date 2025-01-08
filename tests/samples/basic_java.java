// Java calculator
public class Calculator {

    public Calculator() {
    }

    public double add(double a, double b) {
        return a + b;
    }

    public double subtract(double a, double b) {
        return a - b;
    }

    public double multiply(double a, double b) {
        return a * b;
    }

    public double divide(double a, double b) throws IllegalArgumentException {
        if (b == 0) {
            throw new IllegalArgumentException("Cannot divide by zero");
        }
        return a / b;
    }
    // Usage example
    public static void main(String[] args) {
        Calculator calc = new Calculator();
        calc.add(10, 5);
        calc.subtract(10, 5);
        calc.multiply(10, 5);
        try {
            calc.divide(10, 5);
        } catch (IllegalArgumentException e) {
        }
    }
}
