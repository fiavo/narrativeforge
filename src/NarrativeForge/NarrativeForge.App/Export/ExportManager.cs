namespace NarrativeForge.App.Export;

public class ExportManager
{
    private readonly List<IExporter> _exporters = [];

    public void RegisterExporter(IExporter exporter)
    {
        ArgumentNullException.ThrowIfNull(exporter);

        if (_exporters.Any(e => e.Name == exporter.Name))
            return;

        _exporters.Add(exporter);
    }

    public IReadOnlyList<IExporter> GetExporters(string? category = null)
    {
        if (string.IsNullOrWhiteSpace(category))
            return _exporters.AsReadOnly();

        return _exporters
            .Where(e => e.Category.Equals(category, StringComparison.OrdinalIgnoreCase))
            .ToList()
            .AsReadOnly();
    }

    public IReadOnlyList<string> GetCategories()
    {
        return _exporters
            .Select(e => e.Category)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList()
            .AsReadOnly();
    }

    public async Task<ExportResult> ExportAsync(IExporter exporter, ExportRequest request, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(exporter);
        ArgumentNullException.ThrowIfNull(request);

        if (!_exporters.Contains(exporter))
            return new ExportResult { Success = false, Error = "Exporter is not registered." };

        if (!exporter.CanExport(request))
            return new ExportResult { Success = false, Error = $"Exporter '{exporter.Name}' cannot handle this request." };

        return await exporter.ExportAsync(request, cancellationToken);
    }
}
