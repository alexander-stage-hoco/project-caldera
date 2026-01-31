namespace ComplexCode;

// This file intentionally contains code smells for testing
public class GodClass
{
    private string _name;
    private int _age;
    private string _address;
    private string _phone;
    private string _email;
    private double _salary;
    private DateTime _hireDate;
    private string _department;
    private string _manager;
    private List<string> _projects;
    private Dictionary<string, int> _skills;

    // Long method with high complexity
    public string ProcessData(string input, int mode, bool validate, string format, int timeout)
    {
        string result = "";

        if (input == null)
        {
            if (mode == 1)
            {
                result = "null-mode1";
            }
            else if (mode == 2)
            {
                result = "null-mode2";
            }
            else if (mode == 3)
            {
                result = "null-mode3";
            }
            else
            {
                result = "null-default";
            }
        }
        else if (input.Length == 0)
        {
            if (validate)
            {
                if (format == "json")
                {
                    result = "{}";
                }
                else if (format == "xml")
                {
                    result = "<empty/>";
                }
                else if (format == "csv")
                {
                    result = "";
                }
                else
                {
                    result = "empty";
                }
            }
            else
            {
                result = "";
            }
        }
        else if (input.Length < 10)
        {
            if (mode == 1)
            {
                if (validate)
                {
                    if (timeout > 0)
                    {
                        result = ProcessSmallData(input);
                    }
                    else
                    {
                        result = input;
                    }
                }
                else
                {
                    result = input.ToUpper();
                }
            }
            else if (mode == 2)
            {
                result = input.ToLower();
            }
            else
            {
                result = input;
            }
        }
        else if (input.Length < 100)
        {
            // Medium data
            for (int i = 0; i < input.Length; i++)
            {
                if (char.IsLetter(input[i]))
                {
                    if (char.IsUpper(input[i]))
                    {
                        result += char.ToLower(input[i]);
                    }
                    else
                    {
                        result += char.ToUpper(input[i]);
                    }
                }
                else if (char.IsDigit(input[i]))
                {
                    result += input[i];
                }
                else
                {
                    result += "_";
                }
            }
        }
        else
        {
            // Large data
            result = ProcessLargeData(input, mode, validate, format, timeout);
        }

        return result;
    }

    private string ProcessSmallData(string input)
    {
        return input.Trim();
    }

    private string ProcessLargeData(string input, int mode, bool validate, string format, int timeout)
    {
        // Simplified for this example
        return input.Substring(0, 100);
    }

    // Duplicated code block 1
    public void SaveToFile(string path)
    {
        try
        {
            using var writer = new StreamWriter(path);
            writer.WriteLine(_name);
            writer.WriteLine(_age);
            writer.WriteLine(_address);
            writer.WriteLine(_phone);
            writer.WriteLine(_email);
            writer.WriteLine(_salary);
            writer.WriteLine(_hireDate);
            writer.WriteLine(_department);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
            throw;
        }
    }

    // Duplicated code block 2 - similar structure
    public void SaveToBackup(string path)
    {
        try
        {
            using var writer = new StreamWriter(path);
            writer.WriteLine(_name);
            writer.WriteLine(_age);
            writer.WriteLine(_address);
            writer.WriteLine(_phone);
            writer.WriteLine(_email);
            writer.WriteLine(_salary);
            writer.WriteLine(_hireDate);
            writer.WriteLine(_department);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
            throw;
        }
    }

    // Duplicated code block 3 - similar structure
    public void ExportData(string path)
    {
        try
        {
            using var writer = new StreamWriter(path);
            writer.WriteLine(_name);
            writer.WriteLine(_age);
            writer.WriteLine(_address);
            writer.WriteLine(_phone);
            writer.WriteLine(_email);
            writer.WriteLine(_salary);
            writer.WriteLine(_hireDate);
            writer.WriteLine(_department);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
            throw;
        }
    }
}
