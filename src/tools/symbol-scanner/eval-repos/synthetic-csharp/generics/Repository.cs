using System;
using System.Collections.Generic;

namespace Generics;

/// <summary>
/// Generic repository interface.
/// </summary>
public interface IRepository<T> where T : class
{
    T? GetById(int id);
    IEnumerable<T> GetAll();
    void Add(T entity);
    void Update(T entity);
    void Delete(int id);
}

/// <summary>
/// Generic repository implementation with in-memory storage.
/// </summary>
public class InMemoryRepository<T> : IRepository<T> where T : class, IEntity
{
    private readonly Dictionary<int, T> _storage = new();

    public T? GetById(int id)
    {
        return _storage.TryGetValue(id, out var entity) ? entity : null;
    }

    public IEnumerable<T> GetAll()
    {
        return _storage.Values;
    }

    public void Add(T entity)
    {
        if (_storage.ContainsKey(entity.Id))
        {
            throw new InvalidOperationException($"Entity with ID {entity.Id} already exists");
        }
        _storage[entity.Id] = entity;
    }

    public void Update(T entity)
    {
        if (!_storage.ContainsKey(entity.Id))
        {
            throw new KeyNotFoundException($"Entity with ID {entity.Id} not found");
        }
        _storage[entity.Id] = entity;
    }

    public void Delete(int id)
    {
        _storage.Remove(id);
    }
}

/// <summary>
/// Entity interface.
/// </summary>
public interface IEntity
{
    int Id { get; }
}

/// <summary>
/// Generic service with multiple type parameters.
/// </summary>
public class Mapper<TSource, TDestination>
    where TSource : class
    where TDestination : class, new()
{
    private readonly Func<TSource, TDestination> _mappingFunc;

    public Mapper(Func<TSource, TDestination> mappingFunc)
    {
        _mappingFunc = mappingFunc;
    }

    public TDestination Map(TSource source)
    {
        return _mappingFunc(source);
    }

    public IEnumerable<TDestination> MapAll(IEnumerable<TSource> sources)
    {
        var results = new List<TDestination>();
        foreach (var source in sources)
        {
            results.Add(Map(source));
        }
        return results;
    }
}

/// <summary>
/// Generic method examples.
/// </summary>
public static class GenericMethods
{
    public static T Max<T>(T a, T b) where T : IComparable<T>
    {
        return a.CompareTo(b) > 0 ? a : b;
    }

    public static void Swap<T>(ref T a, ref T b)
    {
        T temp = a;
        a = b;
        b = temp;
    }

    public static TResult Transform<TInput, TResult>(TInput input, Func<TInput, TResult> transformer)
    {
        return transformer(input);
    }
}
