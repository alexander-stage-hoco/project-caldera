namespace LatestWorker;

public class Worker
{
    private readonly ModernApi.ApiController _api;

    public Worker(ModernApi.ApiController api)
    {
        _api = api;
    }

    public void Execute()
    {
        Console.WriteLine("Latest worker executing");
        _api.HandleRequest();
    }
}
