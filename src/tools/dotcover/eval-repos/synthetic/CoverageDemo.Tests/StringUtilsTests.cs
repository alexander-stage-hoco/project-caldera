using Xunit;

namespace CoverageDemo.Tests;

public class StringUtilsTests
{
    private readonly StringUtils _utils = new();

    [Fact]
    public void Reverse_ReturnsReversedString() => Assert.Equal("cba", _utils.Reverse("abc"));

    [Fact]
    public void Reverse_EmptyString_ReturnsEmpty() => Assert.Equal("", _utils.Reverse(""));

    [Fact]
    public void Reverse_Null_ReturnsNull() => Assert.Null(_utils.Reverse(null!));

    // Truncate is intentionally NOT tested

    [Fact]
    public void IsValidEmail_Valid_ReturnsTrue() => Assert.True(_utils.IsValidEmail("test@example.com"));

    [Fact]
    public void IsValidEmail_NoAt_ReturnsFalse() => Assert.False(_utils.IsValidEmail("invalid"));

    // EndsWith(".") branch intentionally NOT tested
}
