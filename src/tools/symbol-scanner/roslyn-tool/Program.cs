using System.Text.Json;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

namespace SymbolExtractor;

/// <summary>
/// Roslyn-based C# symbol extractor for symbol-scanner tool.
/// Outputs JSON matching the Python dataclass format.
/// </summary>
public static class Program
{
    public static int Main(string[] args)
    {
        if (args.Length == 0)
        {
            Console.Error.WriteLine("Usage: SymbolExtractor <directory>");
            Console.Error.WriteLine("  Extracts symbols, calls, and imports from C# files in the directory.");
            return 1;
        }

        var directory = args[0];
        if (!Directory.Exists(directory))
        {
            Console.Error.WriteLine($"Directory not found: {directory}");
            return 1;
        }

        try
        {
            var result = ExtractFromDirectory(directory);
            var json = JsonSerializer.Serialize(result, new JsonSerializerOptions
            {
                WriteIndented = true,
                PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower
            });
            Console.WriteLine(json);
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Error: {ex.Message}");
            return 1;
        }
    }

    private static ExtractionResult ExtractFromDirectory(string directory)
    {
        var result = new ExtractionResult();
        var csFiles = Directory.GetFiles(directory, "*.cs", SearchOption.AllDirectories)
            .Where(f => !f.Contains("obj") && !f.Contains("bin"))
            .ToList();

        if (csFiles.Count == 0)
        {
            return result;
        }

        // Parse all files first
        var syntaxTrees = new List<SyntaxTree>();
        foreach (var file in csFiles)
        {
            try
            {
                var code = File.ReadAllText(file);
                var tree = CSharpSyntaxTree.ParseText(code, path: file);
                syntaxTrees.Add(tree);
            }
            catch (Exception ex)
            {
                result.Errors.Add(new ErrorEntry
                {
                    File = GetRelativePath(file, directory),
                    Message = ex.Message,
                    Code = "PARSE_ERROR",
                    Recoverable = true
                });
            }
        }

        // Create compilation for semantic analysis
        var compilation = CSharpCompilation.Create(
            "Analysis",
            syntaxTrees,
            new[]
            {
                MetadataReference.CreateFromFile(typeof(object).Assembly.Location),
                MetadataReference.CreateFromFile(typeof(Console).Assembly.Location),
                MetadataReference.CreateFromFile(typeof(Enumerable).Assembly.Location)
            },
            new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary)
        );

        // Extract from each file
        foreach (var tree in syntaxTrees)
        {
            var relativePath = GetRelativePath(tree.FilePath, directory);
            var semanticModel = compilation.GetSemanticModel(tree);
            var extractor = new SymbolVisitor(relativePath, semanticModel, result);
            extractor.Visit(tree.GetRoot());
        }

        return result;
    }

    private static string GetRelativePath(string fullPath, string basePath)
    {
        // Normalize paths to absolute
        var fullAbsolute = Path.GetFullPath(fullPath);
        var baseAbsolute = Path.GetFullPath(basePath);

        // Ensure base path ends with separator
        if (!baseAbsolute.EndsWith(Path.DirectorySeparatorChar))
        {
            baseAbsolute += Path.DirectorySeparatorChar;
        }

        if (fullAbsolute.StartsWith(baseAbsolute))
        {
            return fullAbsolute.Substring(baseAbsolute.Length).Replace(Path.DirectorySeparatorChar, '/');
        }

        // Fallback to URI-based approach for edge cases
        try
        {
            var baseUri = new Uri(baseAbsolute);
            var fullUri = new Uri(fullAbsolute);
            var relativeUri = baseUri.MakeRelativeUri(fullUri);
            return Uri.UnescapeDataString(relativeUri.ToString().Replace('/', Path.DirectorySeparatorChar))
                .Replace(Path.DirectorySeparatorChar, '/');
        }
        catch
        {
            // Last resort: return just the filename
            return Path.GetFileName(fullPath);
        }
    }
}

public class SymbolVisitor : CSharpSyntaxWalker
{
    private readonly string _path;
    private readonly SemanticModel _model;
    private readonly ExtractionResult _result;
    private readonly Stack<string> _parentStack = new();

    public SymbolVisitor(string path, SemanticModel model, ExtractionResult result)
        : base(SyntaxWalkerDepth.Node)
    {
        _path = path;
        _model = model;
        _result = result;
    }

    public override void VisitClassDeclaration(ClassDeclarationSyntax node)
    {
        AddTypeSymbol(node, node.Identifier.Text, node.Modifiers);
        _parentStack.Push(node.Identifier.Text);
        base.VisitClassDeclaration(node);
        _parentStack.Pop();
    }

    public override void VisitStructDeclaration(StructDeclarationSyntax node)
    {
        AddTypeSymbol(node, node.Identifier.Text, node.Modifiers);
        _parentStack.Push(node.Identifier.Text);
        base.VisitStructDeclaration(node);
        _parentStack.Pop();
    }

    public override void VisitInterfaceDeclaration(InterfaceDeclarationSyntax node)
    {
        AddTypeSymbol(node, node.Identifier.Text, node.Modifiers);
        _parentStack.Push(node.Identifier.Text);
        base.VisitInterfaceDeclaration(node);
        _parentStack.Pop();
    }

    public override void VisitRecordDeclaration(RecordDeclarationSyntax node)
    {
        AddTypeSymbol(node, node.Identifier.Text, node.Modifiers);
        _parentStack.Push(node.Identifier.Text);
        base.VisitRecordDeclaration(node);
        _parentStack.Pop();
    }

    public override void VisitEnumDeclaration(EnumDeclarationSyntax node)
    {
        AddTypeSymbol(node, node.Identifier.Text, node.Modifiers);
    }

    public override void VisitMethodDeclaration(MethodDeclarationSyntax node)
    {
        var isExported = IsExported(node.Modifiers);
        var parentSymbol = _parentStack.Count > 0 ? _parentStack.Peek() : null;
        var docstring = GetXmlDocComment(node);
        var isAsync = node.Modifiers.Any(m => m.IsKind(SyntaxKind.AsyncKeyword));

        _result.Symbols.Add(new SymbolEntry
        {
            Path = _path,
            SymbolName = node.Identifier.Text,
            SymbolType = "method",
            LineStart = node.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
            LineEnd = node.GetLocation().GetLineSpan().EndLinePosition.Line + 1,
            IsExported = isExported,
            Parameters = node.ParameterList.Parameters.Count,
            ParentSymbol = parentSymbol,
            Docstring = docstring
        });

        _parentStack.Push(node.Identifier.Text);
        base.VisitMethodDeclaration(node);
        _parentStack.Pop();
    }

    public override void VisitConstructorDeclaration(ConstructorDeclarationSyntax node)
    {
        var isExported = IsExported(node.Modifiers);
        var parentSymbol = _parentStack.Count > 0 ? _parentStack.Peek() : null;
        var docstring = GetXmlDocComment(node);

        _result.Symbols.Add(new SymbolEntry
        {
            Path = _path,
            SymbolName = node.Identifier.Text,
            SymbolType = "method",
            LineStart = node.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
            LineEnd = node.GetLocation().GetLineSpan().EndLinePosition.Line + 1,
            IsExported = isExported,
            Parameters = node.ParameterList.Parameters.Count,
            ParentSymbol = parentSymbol,
            Docstring = docstring
        });

        _parentStack.Push(node.Identifier.Text);
        base.VisitConstructorDeclaration(node);
        _parentStack.Pop();
    }

    public override void VisitPropertyDeclaration(PropertyDeclarationSyntax node)
    {
        var isExported = IsExported(node.Modifiers);
        var parentSymbol = _parentStack.Count > 0 ? _parentStack.Peek() : null;
        var docstring = GetXmlDocComment(node);

        _result.Symbols.Add(new SymbolEntry
        {
            Path = _path,
            SymbolName = node.Identifier.Text,
            SymbolType = "property",
            LineStart = node.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
            LineEnd = node.GetLocation().GetLineSpan().EndLinePosition.Line + 1,
            IsExported = isExported,
            Parameters = null,
            ParentSymbol = parentSymbol,
            Docstring = docstring
        });

        base.VisitPropertyDeclaration(node);
    }

    public override void VisitFieldDeclaration(FieldDeclarationSyntax node)
    {
        var isExported = IsExported(node.Modifiers);
        var parentSymbol = _parentStack.Count > 0 ? _parentStack.Peek() : null;
        var docstring = GetXmlDocComment(node);

        foreach (var variable in node.Declaration.Variables)
        {
            _result.Symbols.Add(new SymbolEntry
            {
                Path = _path,
                SymbolName = variable.Identifier.Text,
                SymbolType = "field",
                LineStart = node.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
                LineEnd = node.GetLocation().GetLineSpan().EndLinePosition.Line + 1,
                IsExported = isExported,
                Parameters = null,
                ParentSymbol = parentSymbol,
                Docstring = docstring
            });
        }

        base.VisitFieldDeclaration(node);
    }

    public override void VisitEventFieldDeclaration(EventFieldDeclarationSyntax node)
    {
        var isExported = IsExported(node.Modifiers);
        var parentSymbol = _parentStack.Count > 0 ? _parentStack.Peek() : null;
        var docstring = GetXmlDocComment(node);

        foreach (var variable in node.Declaration.Variables)
        {
            _result.Symbols.Add(new SymbolEntry
            {
                Path = _path,
                SymbolName = variable.Identifier.Text,
                SymbolType = "event",
                LineStart = node.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
                LineEnd = node.GetLocation().GetLineSpan().EndLinePosition.Line + 1,
                IsExported = isExported,
                Parameters = null,
                ParentSymbol = parentSymbol,
                Docstring = docstring
            });
        }

        base.VisitEventFieldDeclaration(node);
    }

    public override void VisitInvocationExpression(InvocationExpressionSyntax node)
    {
        var callerSymbol = GetEnclosingMemberName() ?? "<module>";
        var callType = "direct";
        string? calleeObject = null;
        string callee;

        switch (node.Expression)
        {
            case IdentifierNameSyntax id:
                callee = id.Identifier.Text;
                break;
            case MemberAccessExpressionSyntax memberAccess:
                callee = memberAccess.Name.Identifier.Text;
                calleeObject = GetRootObject(memberAccess.Expression);
                callType = "dynamic";
                break;
            case GenericNameSyntax generic:
                callee = generic.Identifier.Text;
                break;
            default:
                base.VisitInvocationExpression(node);
                return;
        }

        // Check for async calls
        var isAsync = node.Ancestors().OfType<AwaitExpressionSyntax>().Any();
        if (isAsync)
        {
            callType = "async";
        }

        _result.Calls.Add(new CallEntry
        {
            CallerFile = _path,
            CallerSymbol = callerSymbol,
            CalleeSymbol = callee,
            CalleeFile = null,
            LineNumber = node.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
            CallType = callType,
            IsDynamicCodeExecution = false,
            CalleeObject = calleeObject
        });

        base.VisitInvocationExpression(node);
    }

    public override void VisitObjectCreationExpression(ObjectCreationExpressionSyntax node)
    {
        var callerSymbol = GetEnclosingMemberName() ?? "<module>";
        var typeName = node.Type switch
        {
            IdentifierNameSyntax id => id.Identifier.Text,
            GenericNameSyntax generic => generic.Identifier.Text,
            QualifiedNameSyntax qualified => qualified.Right.Identifier.Text,
            _ => null
        };

        if (typeName != null)
        {
            _result.Calls.Add(new CallEntry
            {
                CallerFile = _path,
                CallerSymbol = callerSymbol,
                CalleeSymbol = typeName,
                CalleeFile = null,
                LineNumber = node.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
                CallType = "direct",
                IsDynamicCodeExecution = false,
                CalleeObject = null
            });
        }

        base.VisitObjectCreationExpression(node);
    }

    public override void VisitUsingDirective(UsingDirectiveSyntax node)
    {
        var isStatic = node.StaticKeyword.IsKind(SyntaxKind.StaticKeyword);
        var isGlobal = node.GlobalKeyword.IsKind(SyntaxKind.GlobalKeyword);
        var importType = isGlobal ? "global" : "static";

        string? alias = null;
        if (node.Alias != null)
        {
            alias = node.Alias.Name.Identifier.Text;
        }

        var importedPath = node.NamespaceOrType?.ToString() ?? node.Name?.ToString() ?? "";

        _result.Imports.Add(new ImportEntry
        {
            File = _path,
            ImportedPath = importedPath,
            ImportedSymbols = null,
            ImportType = importType,
            LineNumber = node.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
            ModuleAlias = alias
        });

        base.VisitUsingDirective(node);
    }

    public override void VisitExternAliasDirective(ExternAliasDirectiveSyntax node)
    {
        _result.Imports.Add(new ImportEntry
        {
            File = _path,
            ImportedPath = node.Identifier.Text,
            ImportedSymbols = null,
            ImportType = "extern",
            LineNumber = node.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
            ModuleAlias = null
        });

        base.VisitExternAliasDirective(node);
    }

    private void AddTypeSymbol(SyntaxNode node, string name, SyntaxTokenList modifiers)
    {
        var isExported = IsExported(modifiers);
        var parentSymbol = _parentStack.Count > 0 ? _parentStack.Peek() : null;
        var docstring = GetXmlDocComment(node);

        _result.Symbols.Add(new SymbolEntry
        {
            Path = _path,
            SymbolName = name,
            SymbolType = "class",
            LineStart = node.GetLocation().GetLineSpan().StartLinePosition.Line + 1,
            LineEnd = node.GetLocation().GetLineSpan().EndLinePosition.Line + 1,
            IsExported = isExported,
            Parameters = null,
            ParentSymbol = parentSymbol,
            Docstring = docstring
        });
    }

    private static bool IsExported(SyntaxTokenList modifiers)
    {
        foreach (var modifier in modifiers)
        {
            if (modifier.IsKind(SyntaxKind.PrivateKeyword))
                return false;
        }
        // Default in C# is internal for top-level, private for nested
        // We treat no explicit modifier as exported for top-level types
        return true;
    }

    private static string? GetXmlDocComment(SyntaxNode node)
    {
        var trivia = node.GetLeadingTrivia();
        foreach (var t in trivia)
        {
            if (t.IsKind(SyntaxKind.SingleLineDocumentationCommentTrivia) ||
                t.IsKind(SyntaxKind.MultiLineDocumentationCommentTrivia))
            {
                var xml = t.GetStructure();
                if (xml is DocumentationCommentTriviaSyntax doc)
                {
                    var summary = doc.DescendantNodes()
                        .OfType<XmlElementSyntax>()
                        .FirstOrDefault(e => e.StartTag.Name.ToString() == "summary");

                    if (summary != null)
                    {
                        var text = string.Join(" ", summary.Content
                            .OfType<XmlTextSyntax>()
                            .SelectMany(t => t.TextTokens)
                            .Select(t => t.Text.Trim())
                            .Where(s => !string.IsNullOrWhiteSpace(s)));
                        return string.IsNullOrWhiteSpace(text) ? null : text;
                    }
                }
            }
        }
        return null;
    }

    private string? GetEnclosingMemberName()
    {
        return _parentStack.Count > 0 ? _parentStack.Peek() : null;
    }

    private static string? GetRootObject(ExpressionSyntax expression)
    {
        return expression switch
        {
            IdentifierNameSyntax id => id.Identifier.Text,
            MemberAccessExpressionSyntax ma => GetRootObject(ma.Expression),
            ThisExpressionSyntax => "this",
            BaseExpressionSyntax => "base",
            _ => null
        };
    }
}

public class ExtractionResult
{
    public List<SymbolEntry> Symbols { get; } = [];
    public List<CallEntry> Calls { get; } = [];
    public List<ImportEntry> Imports { get; } = [];
    public List<ErrorEntry> Errors { get; } = [];
}

public class SymbolEntry
{
    public required string Path { get; set; }
    public required string SymbolName { get; set; }
    public required string SymbolType { get; set; }
    public required int LineStart { get; set; }
    public required int LineEnd { get; set; }
    public required bool IsExported { get; set; }
    public int? Parameters { get; set; }
    public string? ParentSymbol { get; set; }
    public string? Docstring { get; set; }
}

public class CallEntry
{
    public required string CallerFile { get; set; }
    public required string CallerSymbol { get; set; }
    public required string CalleeSymbol { get; set; }
    public string? CalleeFile { get; set; }
    public required int LineNumber { get; set; }
    public required string CallType { get; set; }
    public bool IsDynamicCodeExecution { get; set; }
    public string? CalleeObject { get; set; }
}

public class ImportEntry
{
    public required string File { get; set; }
    public required string ImportedPath { get; set; }
    public string? ImportedSymbols { get; set; }
    public required string ImportType { get; set; }
    public required int LineNumber { get; set; }
    public string? ModuleAlias { get; set; }
}

public class ErrorEntry
{
    public required string File { get; set; }
    public required string Message { get; set; }
    public required string Code { get; set; }
    public required bool Recoverable { get; set; }
}
