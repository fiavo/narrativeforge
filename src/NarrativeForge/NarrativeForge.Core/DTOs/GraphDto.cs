namespace NarrativeForge.Core.DTOs;

public class GraphNodeDto
{
    public Guid Id { get; set; }
    public string Type { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public double X { get; set; }
    public double Y { get; set; }
    public List<GraphChoiceDto> Choices { get; set; } = [];
    public List<GraphObjectiveDto> Objectives { get; set; } = [];
    public List<GraphVariableSetDto> VariablesSet { get; set; } = [];
}

public class GraphChoiceDto
{
    public Guid Id { get; set; }
    public string Text { get; set; } = string.Empty;
    public Guid NextNodeId { get; set; }
    public string Condition { get; set; } = string.Empty;
}

public class GraphObjectiveDto
{
    public Guid Id { get; set; }
    public string Description { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public string Target { get; set; } = string.Empty;
}

public class GraphVariableSetDto
{
    public string Key { get; set; } = string.Empty;
    public string Value { get; set; } = string.Empty;
}

public class GraphEdgeDto
{
    public Guid Id { get; set; }
    public Guid SourceId { get; set; }
    public Guid TargetId { get; set; }
    public string Condition { get; set; } = string.Empty;
}

public class DialogueTreeDto
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public Guid StartNodeId { get; set; }
    public List<GraphNodeDto> Nodes { get; set; } = [];
    public List<GraphEdgeDto> Edges { get; set; } = [];
}

public class QuestGraphDto
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public Guid StartNodeId { get; set; }
    public List<GraphNodeDto> Nodes { get; set; } = [];
    public List<GraphEdgeDto> Edges { get; set; } = [];
}

public class CreateDialogueTreeRequest
{
    public string Name { get; set; } = string.Empty;
    public Guid StartNodeId { get; set; }
    public List<GraphNodeDto> Nodes { get; set; } = [];
    public List<GraphEdgeDto> Edges { get; set; } = [];
}

public class CreateQuestGraphRequest
{
    public string Name { get; set; } = string.Empty;
    public Guid StartNodeId { get; set; }
    public List<GraphNodeDto> Nodes { get; set; } = [];
    public List<GraphEdgeDto> Edges { get; set; } = [];
}
