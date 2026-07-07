using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Export;

public interface IExporter
{
    string Name { get; }
    string FileExtension { get; }
    string Description { get; }
    string Category { get; }
    bool CanExport(ExportRequest request);
    Task<ExportResult> ExportAsync(ExportRequest request, CancellationToken cancellationToken = default);
}
