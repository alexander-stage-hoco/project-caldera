namespace ServiceA;

public class ServiceAClass
{
    private readonly ServiceB.ServiceBClass _serviceB;

    public ServiceAClass(ServiceB.ServiceBClass serviceB)
    {
        _serviceB = serviceB;
    }

    public void DoWork()
    {
        Console.WriteLine("ServiceA doing work");
        _serviceB.DoWork();
    }
}
