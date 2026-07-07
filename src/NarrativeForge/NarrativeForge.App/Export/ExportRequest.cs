using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Export;

public class ExportRequest
{
    public string ProjectName { get; set; } = string.Empty;
    public DialogueTreeDto? DialogueTree { get; set; }
    public QuestGraphDto? QuestGraph { get; set; }
    public List<GraphNodeDto> Nodes { get; set; } = [];
    public List<GraphEdgeDto> Edges { get; set; } = [];
    public Dictionary<string, string> Metadata { get; set; } = [];
}
