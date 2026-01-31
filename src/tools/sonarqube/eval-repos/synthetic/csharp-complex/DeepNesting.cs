namespace ComplexCode;

// Intentionally deeply nested code for testing complexity detection
public class DeepNesting
{
    public int Calculate(int a, int b, int c, int d, int e)
    {
        int result = 0;

        if (a > 0)
        {
            if (b > 0)
            {
                if (c > 0)
                {
                    if (d > 0)
                    {
                        if (e > 0)
                        {
                            for (int i = 0; i < a; i++)
                            {
                                for (int j = 0; j < b; j++)
                                {
                                    if (i == j)
                                    {
                                        result += i * j;
                                    }
                                    else if (i > j)
                                    {
                                        result += i - j;
                                    }
                                    else
                                    {
                                        result += j - i;
                                    }
                                }
                            }
                        }
                        else
                        {
                            result = d * 5;
                        }
                    }
                    else
                    {
                        result = c * 4;
                    }
                }
                else
                {
                    result = b * 3;
                }
            }
            else
            {
                result = a * 2;
            }
        }
        else
        {
            result = -1;
        }

        return result;
    }

    public string ProcessWithManyConditions(string input, Dictionary<string, object> options)
    {
        string result = input;

        if (options.ContainsKey("uppercase"))
        {
            if ((bool)options["uppercase"])
            {
                result = result.ToUpper();
            }
        }

        if (options.ContainsKey("trim"))
        {
            if ((bool)options["trim"])
            {
                if (options.ContainsKey("trimStart"))
                {
                    if ((bool)options["trimStart"])
                    {
                        result = result.TrimStart();
                    }
                }
                if (options.ContainsKey("trimEnd"))
                {
                    if ((bool)options["trimEnd"])
                    {
                        result = result.TrimEnd();
                    }
                }
            }
        }

        if (options.ContainsKey("prefix"))
        {
            if (options["prefix"] is string prefix)
            {
                if (!string.IsNullOrEmpty(prefix))
                {
                    result = prefix + result;
                }
            }
        }

        if (options.ContainsKey("suffix"))
        {
            if (options["suffix"] is string suffix)
            {
                if (!string.IsNullOrEmpty(suffix))
                {
                    result = result + suffix;
                }
            }
        }

        return result;
    }
}
