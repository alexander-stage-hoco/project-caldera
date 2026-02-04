namespace NestedTypes;

public class Container
{
    public class PublicNested { public int Value { get; set; } }
    private class PrivateNested { public string Name { get; set; } }
    protected class ProtectedNested { public void Process() { } }

    public interface INestedInterface { void Execute(); }
    public struct NestedStruct { public int X, Y; }
    public enum NestedEnum { None, Active }

    public class Level1
    {
        public class Level2
        {
            public class Level3 { public void Deep() { } }
        }
    }
}
