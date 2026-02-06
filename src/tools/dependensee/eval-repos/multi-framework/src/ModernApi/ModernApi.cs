namespace ModernApi;

public class ApiController
{
    private readonly LegacyService.LegacyDataAccess _legacyService;

    public ApiController(LegacyService.LegacyDataAccess legacyService)
    {
        _legacyService = legacyService;
    }

    public void HandleRequest()
    {
        Console.WriteLine("Modern API handling request");
        _legacyService.Query();
    }
}
