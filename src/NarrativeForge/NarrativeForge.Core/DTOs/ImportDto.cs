namespace NarrativeForge.Core.DTOs;

public class ImportRequestDto
{
    public string Filename { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public string Format { get; set; } = string.Empty;
}

public class ImportResponseDto
{
    public Guid TreeId { get; set; }
    public string Name { get; set; } = string.Empty;
    public List<GraphNodeDto> Nodes { get; set; } = [];
    public List<GraphEdgeDto> Edges { get; set; } = [];
    public List<GraphChoiceDto> Choices { get; set; } = [];
}
