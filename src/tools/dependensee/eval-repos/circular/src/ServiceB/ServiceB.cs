namespace ServiceB;

public class ServiceBClass
{
    private readonly ServiceC.ServiceCClass _serviceC;

    public ServiceBClass(ServiceC.ServiceCClass serviceC)
    {
        _serviceC = serviceC;
    }

    public void DoWork()
    {
        Console.WriteLine("ServiceB doing work");
        _serviceC.DoWork();
    }
}
