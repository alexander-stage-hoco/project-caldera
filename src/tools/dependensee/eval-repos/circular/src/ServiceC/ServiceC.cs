namespace ServiceC;

public class ServiceCClass
{
    private readonly ServiceA.ServiceAClass _serviceA;

    public ServiceCClass(ServiceA.ServiceAClass serviceA)
    {
        _serviceA = serviceA;
    }

    public void DoWork()
    {
        Console.WriteLine("ServiceC doing work");
        // Note: This creates a circular dependency back to ServiceA
    }
}
