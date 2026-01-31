# Lizard Deep Dive: Technical Analysis

This document provides a technical deep dive into [Lizard](https://github.com/terryyin/lizard), the function-level complexity analyzer used in PoC #2.

## Tool Overview

**Lizard** is an extensible cyclomatic complexity analyzer that calculates:

| Metric | Description |
|--------|-------------|
| `cyclomatic_complexity` (CCN) | McCabe complexity - number of linearly independent paths |
| `nloc` | Non-commenting lines of code |
| `token_count` | Number of tokens in function body |
| `parameter_count` | Number of function parameters |
| `length` | Total lines (including comments/blanks) |
| `start_line` / `end_line` | Function location in file |
| `function_name` | Short function name |
| `long_name` | Fully qualified name with parameters |

### Supported Languages

Lizard supports 27+ languages out of the box:

| Language | Extension | Notes |
|----------|-----------|-------|
| Python | .py | Full support including nested functions |
| C# | .cs | Classes, methods, properties, LINQ |
| Java | .java | Classes, methods, lambdas, streams |
| JavaScript | .js | ES6+, arrow functions, classes |
| TypeScript | .ts, .tsx | Full TypeScript support |
| Go | .go | Methods with receivers, goroutines |
| Rust | .rs | impl blocks, closures, traits |
| C/C++ | .c, .cpp, .h | Preprocessor macros handled |
| Ruby | .rb | Classes, modules, blocks |
| Swift | .swift | Protocols, extensions |
| PHP | .php | Classes, traits, closures |
| Scala | .scala | Objects, traits, case classes |
| Kotlin | .kt | Data classes, lambdas |
| Objective-C | .m | Categories, blocks |
| Lua | .lua | Functions, metatables |
| And more... | | See lizard --help |

---

## CCN Calculation Algorithm

### Decision Points

Lizard calculates CCN by counting decision points:

```
CCN = 1 + D
```

Where D is the number of decision points:

| Construct | Count | Example |
|-----------|-------|---------|
| if | +1 | `if (x)` |
| else if | +1 | `else if (y)` |
| else | 0 | `else` (no decision) |
| for | +1 | `for (i = 0; ...)` |
| while | +1 | `while (x)` |
| do-while | +1 | `do {...} while (x)` |
| switch case | +1 per case | `case 1:` |
| catch | +1 | `catch (e)` |
| && | +1 | `if (a && b)` |
| \|\| | +1 | `if (a \|\| b)` |
| ternary | +1 | `a ? b : c` |

### Examples

**Simple Function (CCN=1)**
```python
def greet(name):
    return f"Hello, {name}"  # No decision points
# CCN = 1 + 0 = 1
```

**Medium Function (CCN=4)**
```python
def validate(user):
    if not user:              # +1
        return False
    if user.age < 0:          # +1
        return False
    if user.age > 150:        # +1
        return False
    return True
# CCN = 1 + 3 = 4
```

**Complex Function (CCN=12)**
```python
def process(data, mode):
    if not data:              # +1
        return None

    for item in data:         # +1
        if mode == 'A':       # +1
            if item.valid:    # +1
                pass
        elif mode == 'B':     # +1
            if item.x > 0 and item.y > 0:  # +1 (if) + 1 (and) = +2
                pass
        else:
            for sub in item:  # +1
                if sub.ok:    # +1
                    pass
                elif sub.retry:  # +1
                    pass

    return True
# CCN = 1 + 11 = 12
```

---

## Output Formats

### XML Output (Default)

```bash
python -m lizard --xml > output.xml
```

```xml
<?xml version="1.0"?>
<cppncss>
  <measure type="Function">
    <labels>
      <label>Nr.</label>
      <label>NCSS</label>
      <label>CCN</label>
    </labels>
    <item name="greet(name)@1-2@simple.py">
      <value>1</value>
      <value>2</value>
      <value>1</value>
    </item>
  </measure>
</cppncss>
```

### CSV Output

```bash
python -m lizard --csv > output.csv
```

```csv
NLOC,CCN,token,PARAM,length,location,file,function,long_name,start,end
2,1,8,1,2,1-2,simple.py,greet,greet( name ),1,2
```

### JSON Output (via wrapper)

Lizard doesn't natively output JSON, so we use a wrapper:

```python
import lizard

result = lizard.analyze_file("simple.py")
functions = [
    {
        "name": f.name,
        "long_name": f.long_name,
        "ccn": f.cyclomatic_complexity,
        "nloc": f.nloc,
        "token_count": f.token_count,
        "parameter_count": len(f.parameters),
        "start_line": f.start_line,
        "end_line": f.end_line,
    }
    for f in result.function_list
]
```

---

## Language-Specific Behavior

### Python

**Strengths**:
- Nested functions detected with qualified names: `outer._inner`
- Decorators don't affect CCN
- Comprehensions counted correctly (each `if` adds +1)
- Type hints don't affect parsing

**Quirks**:
- `self` parameter counted in parameter_count
- Default parameter values not parsed
- Lambda expressions detected as anonymous

```python
# Detected as: outer._inner
def outer():
    def _inner():
        pass
    return _inner

# List comprehension: CCN=2 (base + if)
filtered = [x for x in items if x.valid]
```

### C#

**Strengths**:
- Properties detected as methods (getter/setter)
- LINQ expressions parsed
- Expression-bodied members work
- Local functions detected

**Quirks**:
- Properties may show as multiple functions
- Pattern matching `switch` adds per-case
- Nullable annotations don't affect parsing

```csharp
// Detected as: Person::Name
public string Name { get; set; }

// Detected as: Person::Validate
public bool Validate() => Age > 0 && Name != null;
// CCN = 1 + 1 (&&) = 2
```

### Java

**Strengths**:
- Constructors: `ClassName::ClassName`
- Anonymous classes parsed
- Streams/lambdas detected
- Switch expressions counted correctly

**Quirks**:
- One function may contain inner anonymous classes
- Record constructors may have odd naming
- Annotation processing not reflected

```java
// Detected as: User::User
public User(String name) { this.name = name; }

// Lambda detected as anonymous
list.stream()
    .filter(x -> x.isValid())  // CCN=2 for lambda
    .map(x -> x.name);         // CCN=1 for lambda
```

### JavaScript / TypeScript

**Strengths**:
- Arrow functions detected
- Class methods with qualified names
- Generators (`function*`) parsed
- Async functions work

**Quirks**:
- Arrow functions often named `(anonymous)`
- Object method shorthand detection varies
- JSX expressions may add complexity

```typescript
// Detected as: Counter::increment
class Counter {
    increment(): void { this.count++; }
}

// Detected as: (anonymous)
const add = (a: number, b: number) => a + b;

// Detected as: processItems::>(anonymous)
function processItems<T>(items: T[]): T[] {
    return items.filter(item => item.valid);
}
```

### Go

**Strengths**:
- Methods with receivers: `(r *Repo) Find`
- Multiple return values don't confuse
- Goroutines parsed correctly
- Defer/panic/recover handled

**Quirks**:
- Empty function name for some constructs
- Interface method declarations not counted
- Build tags don't affect parsing

```go
// Detected as: (r*InMemoryRepository)Find
func (r *InMemoryRepository) Find(id int) (*User, error) {
    if id <= 0 {
        return nil, ErrInvalidID
    }
    return r.data[id], nil
}
// CCN = 1 + 1 = 2
```

### Rust

**Strengths**:
- impl blocks parsed correctly
- Closures detected as anonymous
- Pattern matching counted per arm
- Trait methods detected

**Quirks**:
- Lifetime annotations don't affect parsing
- Macros may cause parsing issues
- Associated functions vs methods

```rust
// Detected as: User::new
impl User {
    fn new(name: String) -> Self {
        Self { name }
    }
}

// Pattern matching: CCN = 1 + 3 (3 arms)
match status {
    Status::Active => handle_active(),
    Status::Inactive => handle_inactive(),
    _ => handle_default(),
}
```

---

## Known Limitations

### 1. Fan-In/Fan-Out Always 0

Lizard doesn't track call relationships:

```python
result.function_list[0].fan_in   # Always 0
result.function_list[0].fan_out  # Always 0
```

**Workaround**: Use dedicated dependency analysis tools.

### 2. Duplicate Function Names

Multiple functions can have the same short name:

```typescript
// massive.ts
const a = { ">": (x) => x + 1 };  // CCN=1
const b = (a, b, c, d, e, f, g, h, i) => { ... };  // CCN=26, also named ">"
```

**Workaround**: Use `long_name` or match by expected CCN.

### 3. Anonymous Function Identification

All anonymous functions named `(anonymous)`:

```javascript
[1, 2, 3].map(x => x * 2);     // (anonymous)
[4, 5, 6].filter(x => x > 4);  // (anonymous)
```

**Workaround**: Use line number for identification.

### 4. Preprocessor Macros

C/C++ macros may cause parsing issues:

```c
#define CHECK(x) if (x) return
// Macro usage doesn't add to CCN
CHECK(error);  // Not counted
```

### 5. NLOC Definition Variance

NLOC may differ from expectations:

| Situation | Lizard Behavior |
|-----------|-----------------|
| Blank lines in body | Sometimes included |
| Closing brace | Sometimes excluded |
| Multi-line statements | Counted as multiple |

Typical accuracy: 90-95% within 10% tolerance.

---

## Performance Characteristics

### Speed Benchmarks

| Codebase | Files | Functions | Time |
|----------|-------|-----------|------|
| Synthetic (7 langs) | 63 | 524 | 0.29s |
| click (Python) | ~40 | ~400 | 0.35s |
| picocli/src (Java) | ~50 | ~2000 | 1.63s |

### Memory Usage

Lizard is memory-efficient:

| Analysis | Memory |
|----------|--------|
| 524 functions | 45 MB |
| ~2000 functions | ~100 MB |

### Scaling

Lizard scales linearly with codebase size:
- ~1000 functions/second on modern hardware
- Memory grows with function count, not file size

---

## Integration Tips

### 1. Use as Python Library

```python
import lizard

# Analyze single file
result = lizard.analyze_file("app.py")

# Analyze directory
results = lizard.analyze(["./src"], threads=4)

# Access results
for file_result in results:
    for func in file_result.function_list:
        if func.cyclomatic_complexity > 10:
            print(f"Complex: {func.name} (CCN={func.cyclomatic_complexity})")
```

### 2. Combine with scc

```python
def analyze_codebase(path):
    # File-level metrics (LOC, language detection)
    scc_results = run_scc(path)

    # Function-level metrics (CCN, hotspots)
    lizard_results = run_lizard(path)

    # Merge by file path
    for file in scc_results["files"]:
        file["functions"] = lizard_results.get(file["path"], [])
```

### 3. CCN Thresholds for CI/CD

```bash
# Fail if any function has CCN > 15
python -m lizard --CCN 15 --warning ./src

# Exit code:
# 0 = All functions under threshold
# 1 = Some functions over threshold
```

### 4. Watch for Hotspots

```python
def find_hotspots(results, threshold=10):
    hotspots = []
    for file in results:
        for func in file.function_list:
            if func.cyclomatic_complexity >= threshold:
                hotspots.append({
                    "file": file.filename,
                    "function": func.name,
                    "ccn": func.cyclomatic_complexity,
                    "nloc": func.nloc,
                })
    return sorted(hotspots, key=lambda x: -x["ccn"])
```

### 5. Multi-Threaded Analysis

```python
import lizard

# Use all available cores
results = lizard.analyze(
    ["./src"],
    threads=os.cpu_count()
)
```

---

## Configuration Options

### Command Line

```bash
# Output format
lizard --xml          # XML format
lizard --csv          # CSV format
lizard -H             # HTML report

# Thresholds
lizard --CCN 15       # Warning threshold
lizard -T nloc=100    # NLOC threshold

# Filtering
lizard -x "*/test/*"  # Exclude paths
lizard -l python      # Only Python files

# Extensions
lizard -E NS          # Nested structure extension
lizard -E io          # Import/output analysis
```

### Python API

```python
lizard.analyze(
    paths=["./src"],
    threads=4,
    exclusions=["*/test/*", "*/vendor/*"],
    extensions=[lizard.CCNExt()],
)
```

---

## Extending Lizard

### Custom Language Support

```python
from lizard_ext import LizardExtension

class MyLanguage(LizardExtension):
    language_names = ['mylang']
    file_extensions = ['.ml']

    def __init__(self):
        # Define token patterns
        pass

    def state_machine(self):
        # Define parsing state machine
        pass
```

### Custom Metrics

```python
from lizard.extensions import LizardExtension

class MyMetric(LizardExtension):
    def visit_function(self, func):
        # Add custom metric
        func.my_metric = calculate_my_metric(func)
```

---

## References

- [Lizard GitHub](https://github.com/terryyin/lizard)
- [Lizard Documentation](https://pypi.org/project/lizard/)
- [McCabe (1976) - Cyclomatic Complexity](https://doi.org/10.1109/TSE.1976.233837)
- [Software Complexity Metrics](https://en.wikipedia.org/wiki/Software_metric)
