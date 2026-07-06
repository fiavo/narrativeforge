namespace NarrativeForge.App.Layout;

public interface IGraphLayout
{
    string Name { get; }
    string Description { get; }
    void ComputeLayout(IList<GraphNode> nodes, IList<GraphEdge> edges);
}