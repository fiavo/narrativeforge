namespace NarrativeForge.App.Export;

public class ExportResult
{
    public bool Success { get; set; }
    public string Content { get; set; } = string.Empty;
    public string Filename { get; set; } = string.Empty;
    public string Error { get; set; } = string.Empty;
}
