namespace NarrativeForge.App.Layout;

public record GraphNode(string Id, string Type, double X, double Y);

public record GraphEdge(string SourceId, string TargetId, string Condition);