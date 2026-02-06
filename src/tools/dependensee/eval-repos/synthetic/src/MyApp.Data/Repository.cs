using MyApp.Core;

namespace MyApp.Data;

public interface IRepository<T>
{
    Task<T?> GetByIdAsync(int id);
    Task<IEnumerable<T>> GetAllAsync();
}

public class UserRepository : IRepository<User>
{
    public Task<User?> GetByIdAsync(int id) => Task.FromResult<User?>(null);
    public Task<IEnumerable<User>> GetAllAsync() => Task.FromResult<IEnumerable<User>>([]);
}
