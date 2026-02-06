namespace App.Infrastructure;

public class AppDbContext
{
    public void SaveChanges()
    {
        Console.WriteLine("Saving changes to database");
    }
}
