using System;
using System.Threading;
using System.Threading.Tasks;

namespace SyntheticSmells.Clean
{
    /// <summary>
    /// Clean controller demonstrating proper code practices.
    /// Expected violations: 0
    /// All patterns follow best practices for resource management and security.
    /// </summary>
    public class CleanController
    {
        private readonly ICleanService _service;

        public CleanController(ICleanService service)
        {
            _service = service ?? throw new ArgumentNullException(nameof(service));
        }

        public async Task<ServiceResult> GetAsync(
            string id,
            CancellationToken cancellationToken)
        {
            if (string.IsNullOrWhiteSpace(id))
                return ServiceResult.Error("Id is required");

            var result = await _service.ProcessAsync(
                new ProcessRequest { Id = id },
                cancellationToken).ConfigureAwait(false);

            return result;
        }

        public async Task<ServiceResult> CreateAsync(
            CreateRequest request,
            CancellationToken cancellationToken)
        {
            if (request == null)
                return ServiceResult.Error("Request is required");

            if (string.IsNullOrWhiteSpace(request.Name))
                return ServiceResult.Error("Name is required");

            var result = await _service.ProcessAsync(
                new ProcessRequest { Id = request.Name },
                cancellationToken).ConfigureAwait(false);

            return result;
        }

        public async Task<ServiceResult> UpdateAsync(
            string id,
            UpdateRequest request,
            CancellationToken cancellationToken)
        {
            if (string.IsNullOrWhiteSpace(id))
                return ServiceResult.Error("Id is required");

            if (request == null)
                return ServiceResult.Error("Request is required");

            if (!string.Equals(id, request.Id, StringComparison.OrdinalIgnoreCase))
                return ServiceResult.Error("Id mismatch");

            var result = await _service.ProcessAsync(
                new ProcessRequest { Id = id },
                cancellationToken).ConfigureAwait(false);

            return result;
        }

        public async Task<ServiceResult> DeleteAsync(
            string id,
            CancellationToken cancellationToken)
        {
            if (string.IsNullOrWhiteSpace(id))
                return ServiceResult.Error("Id is required");

            var result = await _service.ProcessAsync(
                new ProcessRequest { Id = id },
                cancellationToken).ConfigureAwait(false);

            return result;
        }
    }

    // These types are defined in clean_service.cs:
    // - ICleanService
    // - ProcessRequest
    // - ServiceResult

    public class CreateRequest
    {
        public string Name { get; set; }
    }

    public class UpdateRequest
    {
        public string Id { get; set; }
        public string Name { get; set; }
    }
}
