# Dockerfile for dotCover analysis
# Runs dotCover in Linux x64 container to bypass macOS ARM64 report generation bug
#
# Usage:
#   docker build -t dotcover-runner .
#   docker run --rm -v /path/to/repo:/repo -v /path/to/output:/output dotcover-runner \
#       cover --snapshot-output /output/coverage.dcvr -- dotnet test /repo --no-build

# Force x64 architecture to bypass ARM64 dotCover bug
# Use SDK 10.0 to support net10.0 target framework
FROM --platform=linux/amd64 mcr.microsoft.com/dotnet/sdk:10.0

# Install dotCover CLI tool globally
RUN dotnet tool install --global JetBrains.dotCover.CommandLineTools

# Add dotnet tools to PATH
ENV PATH="$PATH:/root/.dotnet/tools"

# Set working directory for repo mount
WORKDIR /repo

# Default entrypoint is dotCover
ENTRYPOINT ["dotCover"]
