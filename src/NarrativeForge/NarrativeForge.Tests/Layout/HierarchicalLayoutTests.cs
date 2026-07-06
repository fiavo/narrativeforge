using NarrativeForge.App.Layout;

namespace NarrativeForge.Tests.Layout;

public class HierarchicalLayoutTests
{
    [Fact]
    public void EmptyGraph_RemainsUnchanged()
    {
        var layout = new HierarchicalLayout();
        var nodes = new List<GraphNode>();
        var edges = new List<GraphEdge>();

        layout.ComputeLayout(nodes, edges);

        Assert.Empty(nodes);
    }

    [Fact]
    public void SingleNode_PositionedAtOrigin()
    {
        var layout = new HierarchicalLayout();
        var nodes = new List<GraphNode>
        {
            new("n1", "Start", 0, 0)
        };
        var edges = new List<GraphEdge>();

        layout.ComputeLayout(nodes, edges);

        Assert.Single(nodes);
        Assert.Equal(0, nodes[0].X);
        Assert.Equal(0, nodes[0].Y);
    }

    [Fact]
    public void LinearChain_AssignsLayersByDepth()
    {
        var layout = new HierarchicalLayout { LayerSpacing = 120, NodeSpacing = 200 };
        var nodes = new List<GraphNode>
        {
            new("a", "Start", 0, 0),
            new("b", "Choice", 0, 0),
            new("c", "End", 0, 0)
        };
        var edges = new List<GraphEdge>
        {
            new("a", "b", ""),
            new("b", "c", "")
        };

        layout.ComputeLayout(nodes, edges);

        var byId = nodes.ToDictionary(n => n.Id);
        Assert.Equal(0, byId["a"].Y);
        Assert.Equal(120, byId["b"].Y);
        Assert.Equal(240, byId["c"].Y);
    }

    [Fact]
    public void BranchingGraph_CentersNodesInLayer()
    {
        var layout = new HierarchicalLayout { LayerSpacing = 120, NodeSpacing = 200 };
        var nodes = new List<GraphNode>
        {
            new("root", "Start", 0, 0),
            new("l1a", "Choice", 0, 0),
            new("l1b", "Choice", 0, 0),
            new("leaf", "End", 0, 0)
        };
        var edges = new List<GraphEdge>
        {
            new("root", "l1a", ""),
            new("root", "l1b", ""),
            new("l1a", "leaf", ""),
            new("l1b", "leaf", "")
        };

        layout.ComputeLayout(nodes, edges);

        var byId = nodes.ToDictionary(n => n.Id);
        Assert.Equal(0, byId["root"].X);
        Assert.Equal(0, byId["root"].Y);
        Assert.Equal(byId["l1a"].Y, byId["l1b"].Y);
        Assert.Equal(120, byId["l1a"].Y);
        Assert.Equal(240, byId["leaf"].Y);
    }

    [Fact]
    public void BarycenterOrdering_MinimizesCrossings()
    {
        var layout = new HierarchicalLayout { LayerSpacing = 120, NodeSpacing = 200 };
        var nodes = new List<GraphNode>
        {
            new("a", "Start", 0, 0),
            new("b", "Start", 0, 0),
            new("c", "Choice", 0, 0),
            new("d", "Choice", 0, 0)
        };
        var edges = new List<GraphEdge>
        {
            new("a", "c", ""),
            new("b", "d", "")
        };

        layout.ComputeLayout(nodes, edges);

        var byId = nodes.ToDictionary(n => n.Id);
        var layer0 = nodes.Where(n => n.Y == 0).OrderBy(n => n.X).ToList();
        var layer1 = nodes.Where(n => n.Y == 120).OrderBy(n => n.X).ToList();
        Assert.Equal("a", layer0[0].Id);
        Assert.Equal("b", layer0[1].Id);
        Assert.Equal("c", layer1[0].Id);
        Assert.Equal("d", layer1[1].Id);
    }
}
