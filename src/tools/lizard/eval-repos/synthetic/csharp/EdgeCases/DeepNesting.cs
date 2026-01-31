namespace Synthetic.EdgeCases;

/// <summary>
/// Deep nesting test - 10+ levels of indentation.
/// </summary>
public class DeepNestingTest
{
    public string ProcessDeeply(Dictionary<string, object>? data)
    {
        var result = "";

        if (data != null)  // Level 1
        {
            if (data.TryGetValue("level1", out var level1))  // Level 2
            {
                if (level1 is List<Dictionary<string, object>> items)  // Level 3
                {
                    foreach (var item in items)  // Level 4
                    {
                        foreach (var (key, value) in item)  // Level 5
                        {
                            if (value != null)  // Level 6
                            {
                                try  // Level 7
                                {
                                    if (value is List<int> numbers)  // Level 8
                                    {
                                        foreach (var n in numbers)  // Level 9
                                        {
                                            if (n > 0)  // Level 10
                                            {
                                                var temp = n;
                                                while (temp > 0)  // Level 11
                                                {
                                                    if (temp % 2 == 0)  // Level 12
                                                    {
                                                        result += temp.ToString();
                                                    }
                                                    temp--;
                                                }
                                            }
                                        }
                                    }
                                }
                                catch
                                {
                                    // Ignored
                                }
                            }
                        }
                    }
                }
            }
        }

        return result;
    }

    public int ProcessMatrix(List<List<Dictionary<string, object>>>? matrix)
    {
        var total = 0;

        if (matrix != null)  // 1
        {
            foreach (var row in matrix)  // 2
            {
                if (row != null)  // 3
                {
                    foreach (var cell in row)  // 4
                    {
                        if (cell != null)  // 5
                        {
                            foreach (var (k, v) in cell)  // 6
                            {
                                if (v != null)  // 7
                                {
                                    switch (v)  // 8
                                    {
                                        case int num:
                                            if (num > 0)  // 9
                                            {
                                                for (var i = 0; i < num; i++)  // 10
                                                {
                                                    if (i % 2 == 1)  // 11
                                                    {
                                                        total += i;
                                                    }
                                                }
                                            }
                                            break;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        return total;
    }
}
