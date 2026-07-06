namespace NarrativeForge.Core.DTOs;

public class GenerateRequestDto
{
    public Guid ProjectId { get; set; }
    public string Request { get; set; } = string.Empty;
    public float Temperature { get; set; } = 0.7f;
}

public class GenerateResponseDto
{
    public object? Content { get; set; }
    public List<string> Stages { get; set; } = [];
    public GenerationMetadata Metadata { get; set; } = new();
}

public class GenerationMetadata
{
    public string Model { get; set; } = string.Empty;
    public float Temperature { get; set; }
    public int TokensUsed { get; set; }
    public int ProcessingTimeMs { get; set; }
    public List<ConsistencyIssue> Issues { get; set; } = [];
}

public class ConsistencyIssue
{
    public Guid ElementId { get; set; }
    public string ElementName { get; set; } = string.Empty;
    public string IssueType { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Severity { get; set; } = string.Empty;
    public string? Suggestion { get; set; }
}
