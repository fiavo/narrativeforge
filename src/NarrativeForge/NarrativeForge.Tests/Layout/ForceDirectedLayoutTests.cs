using NarrativeForge.App.Layout;

namespace NarrativeForge.Tests.Layout;

public class ForceDirectedLayoutTests
{
    [Fact]
    public void EmptyGraph_RemainsUnchanged()
    {
        var layout = new ForceDirectedLayout();
        var nodes = new List<GraphNode>();
        var edges = new List<GraphEdge>();

        layout.ComputeLayout(nodes, edges);

        Assert.Empty(nodes);
    }

    [Fact]
    public void SingleNode_PositionedAtOrigin()
    {
        var layout = new ForceDirectedLayout();
        var nodes = new List<GraphNode>
        {
            new("n1", "Start", 10, 20)
        };
        var edges = new List<GraphEdge>();

        layout.ComputeLayout(nodes, edges);

        Assert.Single(nodes);
        Assert.Equal(0, nodes[0].X);
        Assert.Equal(0, nodes[0].Y);
    }

    [Fact]
    public void ConnectedNodes_DriftApart()
    {
        var layout = new ForceDirectedLayout { MaxIterations = 200 };
        var nodes = new List<GraphNode>
        {
            new("a", "Start", 0, 0),
            new("b", "End", 0, 0)
        };
        var edges = new List<GraphEdge>
        {
            new("a", "b", "")
        };

        layout.ComputeLayout(nodes, edges);

        var byId = nodes.ToDictionary(n => n.Id);
        double dx = byId["b"].X - byId["a"].X;
        double dy = byId["b"].Y - byId["a"].Y;
        double dist = Math.Sqrt(dx * dx + dy * dy);
        Assert.True(dist > 0.5, $"Connected nodes should be separated, distance={dist}");
    }

    [Fact]
    public void ConvergesWithinMaxIterations()
    {
        var layout = new ForceDirectedLayout { MaxIterations = 200 };
        var nodes = new List<GraphNode>
        {
            new("a", "Start", 0, 0),
            new("b", "Choice", 10, 10),
            new("c", "End", 20, 20)
        };
        var edges = new List<GraphEdge>
        {
            new("a", "b", ""),
            new("b", "c", "")
        };

        layout.ComputeLayout(nodes, edges);

        Assert.Equal(3, nodes.Count);
        foreach (var node in nodes)
        {
            Assert.False(double.IsNaN(node.X), $"Node {node.Id} X is NaN");
            Assert.False(double.IsNaN(node.Y), $"Node {node.Id} Y is NaN");
            Assert.False(double.IsInfinity(node.X), $"Node {node.Id} X is infinite");
            Assert.False(double.IsInfinity(node.Y), $"Node {node.Id} Y is infinite");
        }
    }
}
