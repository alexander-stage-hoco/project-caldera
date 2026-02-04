using System;
using System.Collections.Generic;
using System.Linq;

namespace LinqPatterns;

/// <summary>
/// Sample data class.
/// </summary>
public class Product
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public decimal Price { get; set; }
    public string Category { get; set; } = "";
    public int Stock { get; set; }
}

/// <summary>
/// Sample order class.
/// </summary>
public class Order
{
    public int Id { get; set; }
    public int ProductId { get; set; }
    public int Quantity { get; set; }
    public DateTime OrderDate { get; set; }
}

/// <summary>
/// Demonstrates LINQ query patterns.
/// </summary>
public class LinqExamples
{
    private readonly List<Product> _products;
    private readonly List<Order> _orders;

    public LinqExamples(List<Product> products, List<Order> orders)
    {
        _products = products;
        _orders = orders;
    }

    /// <summary>
    /// Basic filtering with Where.
    /// </summary>
    public IEnumerable<Product> GetExpensiveProducts(decimal minPrice)
    {
        return _products.Where(p => p.Price > minPrice);
    }

    /// <summary>
    /// Projection with Select.
    /// </summary>
    public IEnumerable<string> GetProductNames()
    {
        return _products.Select(p => p.Name);
    }

    /// <summary>
    /// Ordering with OrderBy.
    /// </summary>
    public IEnumerable<Product> GetProductsByPrice()
    {
        return _products.OrderBy(p => p.Price).ThenBy(p => p.Name);
    }

    /// <summary>
    /// Grouping with GroupBy.
    /// </summary>
    public IEnumerable<IGrouping<string, Product>> GetProductsByCategory()
    {
        return _products.GroupBy(p => p.Category);
    }

    /// <summary>
    /// Aggregation with Sum, Average, etc.
    /// </summary>
    public (decimal total, decimal avg, decimal max) GetPriceStats()
    {
        var total = _products.Sum(p => p.Price);
        var avg = _products.Average(p => p.Price);
        var max = _products.Max(p => p.Price);
        return (total, avg, max);
    }

    /// <summary>
    /// Join operations.
    /// </summary>
    public IEnumerable<(string ProductName, int Quantity)> GetOrderDetails()
    {
        return _orders
            .Join(
                _products,
                order => order.ProductId,
                product => product.Id,
                (order, product) => (product.Name, order.Quantity)
            );
    }

    /// <summary>
    /// Query syntax example.
    /// </summary>
    public IEnumerable<string> GetLowStockProductNames()
    {
        return from p in _products
               where p.Stock < 10
               orderby p.Name
               select p.Name;
    }

    /// <summary>
    /// Complex query with multiple operations.
    /// </summary>
    public Dictionary<string, decimal> GetCategoryTotals()
    {
        return _products
            .GroupBy(p => p.Category)
            .ToDictionary(
                g => g.Key,
                g => g.Sum(p => p.Price * p.Stock)
            );
    }

    /// <summary>
    /// First, Single, and Default variations.
    /// </summary>
    public Product? FindProduct(int id)
    {
        return _products.FirstOrDefault(p => p.Id == id);
    }

    /// <summary>
    /// Any and All checks.
    /// </summary>
    public (bool hasExpensive, bool allInStock) CheckInventory()
    {
        var hasExpensive = _products.Any(p => p.Price > 100);
        var allInStock = _products.All(p => p.Stock > 0);
        return (hasExpensive, allInStock);
    }

    /// <summary>
    /// SelectMany for flattening.
    /// </summary>
    public IEnumerable<char> GetAllNameCharacters()
    {
        return _products.SelectMany(p => p.Name);
    }

    /// <summary>
    /// Distinct and set operations.
    /// </summary>
    public IEnumerable<string> GetUniqueCategories()
    {
        return _products.Select(p => p.Category).Distinct();
    }

    /// <summary>
    /// Take and Skip for pagination.
    /// </summary>
    public IEnumerable<Product> GetPage(int pageNumber, int pageSize)
    {
        return _products
            .Skip((pageNumber - 1) * pageSize)
            .Take(pageSize);
    }
}

/// <summary>
/// Extension method examples.
/// </summary>
public static class ProductExtensions
{
    /// <summary>
    /// Custom extension method for filtering.
    /// </summary>
    public static IEnumerable<Product> InCategory(this IEnumerable<Product> products, string category)
    {
        return products.Where(p => p.Category == category);
    }

    /// <summary>
    /// Custom extension method for transformation.
    /// </summary>
    public static IEnumerable<Product> WithDiscount(this IEnumerable<Product> products, decimal discountPercent)
    {
        return products.Select(p => new Product
        {
            Id = p.Id,
            Name = p.Name,
            Price = p.Price * (1 - discountPercent / 100),
            Category = p.Category,
            Stock = p.Stock
        });
    }
}
