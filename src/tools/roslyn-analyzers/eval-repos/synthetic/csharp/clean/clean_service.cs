using System;
using System.Threading;
using System.Threading.Tasks;

namespace SyntheticSmells.Clean
{
    /// <summary>
    /// Clean service implementation for false positive testing.
    /// Expected violations: 0
    /// All patterns follow best practices.
    /// </summary>
    public class CleanService : ICleanService
    {
        private readonly ILogger _logger;
        private readonly IDataRepository _repository;

        public CleanService(ILogger logger, IDataRepository repository)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _repository = repository ?? throw new ArgumentNullException(nameof(repository));
        }

        public async Task<ServiceResult> ProcessAsync(
            ProcessRequest request,
            CancellationToken cancellationToken = default)
        {
            if (request == null)
                throw new ArgumentNullException(nameof(request));

            _logger.Log($"Processing request: {request.Id}");

            try
            {
                var data = await _repository.GetDataAsync(request.Id, cancellationToken).ConfigureAwait(false);

                if (data == null)
                {
                    return ServiceResult.NotFound(request.Id);
                }

                var processed = Transform(data);
                await _repository.SaveDataAsync(processed, cancellationToken).ConfigureAwait(false);

                _logger.Log($"Successfully processed: {request.Id}");
                return ServiceResult.Success(processed);
            }
            catch (OperationCanceledException)
            {
                _logger.Log($"Operation cancelled: {request.Id}");
                throw;
            }
            catch (Exception ex)
            {
                _logger.Log($"Error processing {request.Id}: {ex.Message}");
                return ServiceResult.Error(ex.Message);
            }
        }

        private static ProcessedData Transform(RawData data)
        {
            return new ProcessedData
            {
                Id = data.Id,
                Value = data.Value.ToUpperInvariant(),
                ProcessedAt = DateTime.UtcNow
            };
        }
    }

    public interface ICleanService
    {
        Task<ServiceResult> ProcessAsync(ProcessRequest request, CancellationToken cancellationToken = default);
    }

    public interface ILogger
    {
        void Log(string message);
    }

    public interface IDataRepository
    {
        Task<RawData> GetDataAsync(string id, CancellationToken cancellationToken);
        Task SaveDataAsync(ProcessedData data, CancellationToken cancellationToken);
    }

    public class ProcessRequest
    {
        public string Id { get; set; }
    }

    public class RawData
    {
        public string Id { get; set; }
        public string Value { get; set; }
    }

    public class ProcessedData
    {
        public string Id { get; set; }
        public string Value { get; set; }
        public DateTime ProcessedAt { get; set; }
    }

    public class ServiceResult
    {
        public bool IsSuccess { get; private set; }
        public string ErrorMessage { get; private set; }
        public ProcessedData Data { get; private set; }

        public static ServiceResult Success(ProcessedData data) =>
            new ServiceResult { IsSuccess = true, Data = data };

        public static ServiceResult NotFound(string id) =>
            new ServiceResult { IsSuccess = false, ErrorMessage = $"Not found: {id}" };

        public static ServiceResult Error(string message) =>
            new ServiceResult { IsSuccess = false, ErrorMessage = message };
    }
}
