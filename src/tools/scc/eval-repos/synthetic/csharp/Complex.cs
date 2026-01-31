// Calculator service with various operations
using System;
using System.Collections.Generic;
using System.Linq;

namespace SampleApp
{
    /// <summary>
    /// Provides mathematical calculation services.
    /// </summary>
    public class CalculatorService
    {
        private readonly List<CalculationRecord> _history;

        public CalculatorService()
        {
            _history = new List<CalculationRecord>();
        }

        /// <summary>
        /// Add two numbers.
        /// </summary>
        public int Add(int a, int b)
        {
            var result = a + b;
            RecordCalculation("Add", a, b, result);
            return result;
        }

        /// <summary>
        /// Subtract b from a.
        /// </summary>
        public int Subtract(int a, int b)
        {
            var result = a - b;
            RecordCalculation("Subtract", a, b, result);
            return result;
        }

        /// <summary>
        /// Multiply two numbers.
        /// </summary>
        public int Multiply(int a, int b)
        {
            var result = a * b;
            RecordCalculation("Multiply", a, b, result);
            return result;
        }

        /// <summary>
        /// Divide a by b.
        /// </summary>
        /// <exception cref="DivideByZeroException">Thrown when b is zero.</exception>
        public double Divide(int a, int b)
        {
            if (b == 0)
            {
                throw new DivideByZeroException("Cannot divide by zero");
            }
            var result = (double)a / b;
            RecordCalculation("Divide", a, b, result);
            return result;
        }

        /// <summary>
        /// Calculate the power of a number.
        /// </summary>
        public double Power(double baseNum, int exponent)
        {
            if (exponent < 0)
            {
                return 1.0 / Power(baseNum, -exponent);
            }
            if (exponent == 0)
            {
                return 1;
            }
            var result = baseNum;
            for (int i = 1; i < exponent; i++)
            {
                result *= baseNum;
            }
            RecordCalculation("Power", baseNum, exponent, result);
            return result;
        }

        /// <summary>
        /// Calculate factorial of a number.
        /// </summary>
        public long Factorial(int n)
        {
            if (n < 0)
            {
                throw new ArgumentException("Factorial not defined for negative numbers");
            }
            if (n <= 1)
            {
                return 1;
            }
            long result = 1;
            for (int i = 2; i <= n; i++)
            {
                result *= i;
            }
            RecordCalculation("Factorial", n, 0, result);
            return result;
        }

        /// <summary>
        /// Get calculation history.
        /// </summary>
        public IReadOnlyList<CalculationRecord> GetHistory()
        {
            return _history.AsReadOnly();
        }

        /// <summary>
        /// Get statistics about calculations.
        /// </summary>
        public CalculationStats GetStatistics()
        {
            if (_history.Count == 0)
            {
                return new CalculationStats();
            }

            var grouped = _history.GroupBy(r => r.Operation)
                .ToDictionary(g => g.Key, g => g.Count());

            return new CalculationStats
            {
                TotalCalculations = _history.Count,
                OperationCounts = grouped,
                LastCalculation = _history.Last().Timestamp
            };
        }

        private void RecordCalculation(string operation, double a, double b, double result)
        {
            _history.Add(new CalculationRecord
            {
                Operation = operation,
                OperandA = a,
                OperandB = b,
                Result = result,
                Timestamp = DateTime.UtcNow
            });
        }
    }

    /// <summary>
    /// Record of a calculation.
    /// </summary>
    public class CalculationRecord
    {
        public string Operation { get; set; }
        public double OperandA { get; set; }
        public double OperandB { get; set; }
        public double Result { get; set; }
        public DateTime Timestamp { get; set; }
    }

    /// <summary>
    /// Statistics about calculations.
    /// </summary>
    public class CalculationStats
    {
        public int TotalCalculations { get; set; }
        public Dictionary<string, int> OperationCounts { get; set; } = new();
        public DateTime? LastCalculation { get; set; }
    }
}
