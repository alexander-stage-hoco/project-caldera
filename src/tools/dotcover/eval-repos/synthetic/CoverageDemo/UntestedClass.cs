namespace CoverageDemo;

public class UntestedClass
{
    public void DoSomething() { Console.WriteLine("Untested"); }
    public int GetValue() => 42;
    public bool Check(int x) => x > 0;
}
