using MyApp.Core;
using MyApp.Data;
using FluentAssertions;
using Xunit;

namespace MyApp.Tests;

public class UserTests
{
    [Fact]
    public void User_ShouldHaveCorrectProperties()
    {
        var user = new User(1, "Test", "test@example.com");
        user.Id.Should().Be(1);
        user.Name.Should().Be("Test");
    }
}
