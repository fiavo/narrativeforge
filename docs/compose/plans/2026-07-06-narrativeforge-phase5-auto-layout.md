# NarrativeForge Phase 5: Auto-Layout Algorithms — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add hierarchical and force-directed auto-layout algorithms with smooth WPF animation to the graph editor.

**Architecture:** Pure C# layout engine (no WPF dependency) with IGraphLayout interface. Two algorithms: HierarchicalLayout (Sugiyama-style) and ForceDirectedLayout (spring physics). WPF LayoutAnimator uses Storyboard for smooth node transitions. Toolbar button + Ctrl+L shortcut trigger layout.

**Tech Stack:** C# .NET 9, WPF, CommunityToolkit.Mvvm, existing GraphCanvas control

## Global Constraints

- Layout engine must be pure C# (no WPF dependency) for testability
- All layout algorithms implement IGraphLayout interface
- Animation uses WPF Storyboard with ExponentialEase
- Every task ends with a commit
- Unit tests for layout algorithms (pure C#, no WPF)

---

## Task 1: Layout Engine Interface & Models

**Covers:** [S4]

**Files:**
- Create: `src/NarrativeForge/NarrativeForge.App/Layout/IGraphLayout.cs`
- Create: `src/NarrativeForge/NarrativeForge.App/Layout/GraphModels.cs`

**Interfaces:**
- Produces: IGraphLayout interface, GraphNode record, GraphEdge record

- [ ] **Step 1: Create IGraphLayout.cs**

```csharp
using System.Windows;

namespace NarrativeForge.App.Layout;

public interface IGraphLayout
{
    string Name { get; }
    string Description { get; }
    
    Dictionary<string, Point> ComputeLayout(
        IReadOnlyList<GraphNode> nodes,
        IReadOnlyList<GraphEdge> edges,
        double canvasWidth,
        double canvasHeight);
}
```

- [ ] **Step 2: Create GraphModels.cs**

```csharp
using System.Windows;

namespace NarrativeForge.App.Layout;

public record GraphNode(string Id, string Type, double X, double Y);
public record GraphEdge(string SourceId, string TargetId, string Condition);
```

- [ ] **Step 3: Build and verify**

```bash
dotnet build src/NarrativeForge/NarrativeForge.App/NarrativeForge.App.csproj
# Expected: Build succeeded
```

- [ ] **Step 4: Commit**

```bash
git add src/NarrativeForge/NarrativeForge.App/Layout/
git commit -m "feat: add layout engine interface and graph models"
```

---

## Task 2: Hierarchical Layout Algorithm

**Covers:** [S5]

**Files:**
- Create: `src/NarrativeForge/NarrativeForge.App/Layout/HierarchicalLayout.cs`
- Create: `src/NarrativeForge/NarrativeForge.Tests/Layout/HierarchicalLayoutTests.cs`

**Interfaces:**
- Consumes: IGraphLayout, GraphNode, GraphEdge from Task 1
- Produces: HierarchicalLayout class

- [ ] **Step 1: Write failing tests**

```csharp
// HierarchicalLayoutTests.cs
using NarrativeForge.App.Layout;
using System.Windows;

namespace NarrativeForge.Tests.Layout;

[TestClass]
public class HierarchicalLayoutTests
{
    private readonly HierarchicalLayout _layout = new();

    [TestMethod]
    public void SingleRootWithChildren_LayersAssignedCorrectly()
    {
        var nodes = new List<GraphNode>
        {
            new("root", "start", 0, 0),
            new("child1", "text", 0, 0),
            new("child2", "text", 0, 0),
        };
        var edges = new List<GraphEdge>
        {
            new("root", "child1", ""),
            new("root", "child2", ""),
        };

        var result = _layout.ComputeLayout(nodes, edges, 800, 600);

        Assert.AreEqual(0, result["root"].Y);
        Assert.AreEqual(120, result["child1"].Y);
        Assert.AreEqual(120, result["child2"].Y);
    }

    [TestMethod]
    public void LinearChain_EachNodeInSeparateLayer()
    {
        var nodes = new List<GraphNode>
        {
            new("n1", "start", 0, 0),
            new("n2", "text", 0, 0),
            new("n3", "text", 0, 0),
            new("n4", "end", 0, 0),
        };
        var edges = new List<GraphEdge>
        {
            new("n1", "n2", ""),
            new("n2", "n3", ""),
            new("n3", "n4", ""),
        };

        var result = _layout.ComputeLayout(nodes, edges, 800, 600);

        Assert.AreEqual(0, result["n1"].Y);
        Assert.AreEqual(120, result["n2"].Y);
        Assert.AreEqual(240, result["n3"].Y);
        Assert.AreEqual(360, result["n4"].Y);
    }

    [TestMethod]
    public void DiamondGraph_ProperLayerAssignment()
    {
        var nodes = new List<GraphNode>
        {
            new("top", "start", 0, 0),
            new("left", "text", 0, 0),
            new("right", "text", 0, 0),
            new("bottom", "end", 0, 0),
        };
        var edges = new List<GraphEdge>
        {
            new("top", "left", ""),
            new("top", "right", ""),
            new("left", "bottom", ""),
            new("right", "bottom", ""),
        };

        var result = _layout.ComputeLayout(nodes, edges, 800, 600);

        Assert.AreEqual(0, result["top"].Y);
        Assert.AreEqual(120, result["left"].Y);
        Assert.AreEqual(120, result["right"].Y);
        Assert.AreEqual(240, result["bottom"].Y);
    }

    [TestMethod]
    public void EmptyGraph_ReturnsEmptyDictionary()
    {
        var result = _layout.ComputeLayout(new List<GraphNode>(), new List<GraphEdge>(), 800, 600);
        Assert.AreEqual(0, result.Count);
    }

    [TestMethod]
    public void OrphanNodes_PlacedAtBottom()
    {
        var nodes = new List<GraphNode>
        {
            new("root", "start", 0, 0),
            new("orphan", "text", 0, 0),
        };
        var edges = new List<GraphEdge>();

        var result = _layout.ComputeLayout(nodes, edges, 800, 600);

        Assert.AreEqual(0, result["root"].Y);
        Assert.IsTrue(result["orphan"].Y > result["root"].Y);
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
dotnet test src/NarrativeForge/NarrativeForge.Tests/
# Expected: FAIL — HierarchicalLayout not found
```

- [ ] **Step 3: Implement HierarchicalLayout.cs**

```csharp
using System.Windows;

namespace NarrativeForge.App.Layout;

public class HierarchicalLayout : IGraphLayout
{
    public string Name => "Hierarchical";
    public string Description => "Top-to-bottom tree layout (Sugiyama-style)";
    
    public double LayerSpacing { get; set; } = 120;
    public double NodeSpacing { get; set; } = 200;

    public Dictionary<string, Point> ComputeLayout(
        IReadOnlyList<GraphNode> nodes,
        IReadOnlyList<GraphEdge> edges,
        double canvasWidth,
        double canvasHeight)
    {
        if (nodes.Count == 0) return new Dictionary<string, Point>();

        var layers = AssignLayers(nodes, edges);
        var orderedLayers = OrderNodes(layers, edges);
        return PositionNodes(orderedLayers, canvasWidth);
    }

    private List<List<string>> AssignLayers(
        IReadOnlyList<GraphNode> nodes,
        IReadOnlyList<GraphEdge> edges)
    {
        var inDegree = nodes.ToDictionary(n => n.Id, _ => 0);
        var children = nodes.ToDictionary(n => n.Id, _ => new List<string>());

        foreach (var edge in edges)
        {
            if (inDegree.ContainsKey(edge.TargetId))
                inDegree[edge.TargetId]++;
            if (children.ContainsKey(edge.SourceId))
                children[edge.SourceId].Add(edge.TargetId);
        }

        var layers = new List<List<string>>();
        var assigned = new HashSet<string>();

        var roots = inDegree.Where(kv => kv.Value == 0).Select(kv => kv.Key).ToList();
        if (roots.Count == 0)
            roots = nodes.Select(n => n.Id).Take(1).ToList();

        var currentLayer = new List<string>(roots);
        while (currentLayer.Count > 0)
        {
            layers.Add(currentLayer.ToList());
            foreach (var id in currentLayer)
                assigned.Add(id);

            var nextLayer = new List<string>();
            foreach (var id in currentLayer)
            {
                foreach (var child in children[id])
                {
                    if (!assigned.Contains(child) && !nextLayer.Contains(child))
                        nextLayer.Add(child);
                }
            }
            currentLayer = nextLayer;
        }

        var orphans = nodes.Where(n => !assigned.Contains(n.Id)).Select(n => n.Id).ToList();
        if (orphans.Count > 0)
            layers.Add(orphans);

        return layers;
    }

    private List<List<string>> OrderNodes(
        List<List<string>> layers,
        IReadOnlyList<GraphEdge> edges)
    {
        var nodeToLayer = new Dictionary<string, int>();
        for (int i = 0; i < layers.Count; i++)
            foreach (var id in layers[i])
                nodeToLayer[id] = i;

        for (int i = 1; i < layers.Count; i++)
        {
            var layer = layers[i];
            var positions = new Dictionary<string, double>();

            foreach (var id in layer)
            {
                var parents = edges.Where(e => e.TargetId == id && nodeToLayer.ContainsKey(e.SourceId))
                    .Select(e => e.SourceId)
                    .Where(p => layers[nodeToLayer[p]].IndexOf(p) >= 0)
                    .ToList();

                if (parents.Count > 0)
                {
                    positions[id] = parents.Average(p => layers[nodeToLayer[p]].IndexOf(p));
                }
                else
                {
                    positions[id] = layer.IndexOf(id);
                }
            }

            layers[i] = layer.OrderBy(id => positions.GetValueOrDefault(id, 0)).ToList();
        }

        return layers;
    }

    private Dictionary<string, Point> PositionNodes(
        List<List<string>> layers,
        double canvasWidth)
    {
        var result = new Dictionary<string, Point>();
        double startX = canvasWidth / 2;

        for (int i = 0; i < layers.Count; i++)
        {
            var layer = layers[i];
            double totalWidth = (layer.Count - 1) * NodeSpacing;
            double offsetX = startX - totalWidth / 2;

            for (int j = 0; j < layer.Count; j++)
            {
                result[layer[j]] = new Point(offsetX + j * NodeSpacing, i * LayerSpacing);
            }
        }

        return result;
    }
}
```

- [ ] **Step 4: Create test project and run tests**

```bash
dotnet new xunit -n NarrativeForge.Tests -o src/NarrativeForge/NarrativeForge.Tests
dotnet add src/NarrativeForge/NarrativeForge.Tests/NarrativeForge.Tests.csproj reference src/NarrativeForge/NarrativeForge.App/NarrativeForge.App.csproj
dotnet test src/NarrativeForge/NarrativeForge.Tests/
# Expected: 5 passed
```

- [ ] **Step 5: Commit**

```bash
git add src/NarrativeForge/NarrativeForge.App/Layout/HierarchicalLayout.cs src/NarrativeForge/NarrativeForge.Tests/
git commit -m "feat: add hierarchical layout algorithm with Sugiyama-style layering"
```

---

## Task 3: Force-Directed Layout Algorithm

**Covers:** [S6]

**Files:**
- Create: `src/NarrativeForge/NarrativeForge.App/Layout/ForceDirectedLayout.cs`
- Create: `src/NarrativeForge/NarrativeForge.Tests/Layout/ForceDirectedLayoutTests.cs`

**Interfaces:**
- Consumes: IGraphLayout, GraphNode, GraphEdge from Task 1
- Produces: ForceDirectedLayout class

- [ ] **Step 1: Write failing tests**

```csharp
// ForceDirectedLayoutTests.cs
using NarrativeForge.App.Layout;
using System.Windows;

namespace NarrativeForge.Tests.Layout;

[TestClass]
public class ForceDirectedLayoutTests
{
    private readonly ForceDirectedLayout _layout = new();

    [TestMethod]
    public void TwoConnectedNodes_AdjacentPositions()
    {
        var nodes = new List<GraphNode>
        {
            new("a", "text", 0, 0),
            new("b", "text", 100, 100),
        };
        var edges = new List<GraphEdge> { new("a", "b", "") };

        var result = _layout.ComputeLayout(nodes, edges, 800, 600);

        var dist = Distance(result["a"], result["b"]);
        Assert.IsTrue(dist < 300, $"Nodes too far apart: {dist}");
        Assert.IsTrue(dist > 10, $"Nodes too close: {dist}");
    }

    [TestMethod]
    public void TriangleGraph_RoughlyEquilateralSpacing()
    {
        var nodes = new List<GraphNode>
        {
            new("a", "text", 0, 0),
            new("b", "text", 100, 0),
            new("c", "text", 50, 100),
        };
        var edges = new List<GraphEdge>
        {
            new("a", "b", ""),
            new("b", "c", ""),
            new("c", "a", ""),
        };

        var result = _layout.ComputeLayout(nodes, edges, 800, 600);

        var dAB = Distance(result["a"], result["b"]);
        var dBC = Distance(result["b"], result["c"]);
        var dCA = Distance(result["c"], result["a"]);

        Assert.IsTrue(Math.Abs(dAB - dBC) < 100, $"AB={dAB}, BC={dBC}");
        Assert.IsTrue(Math.Abs(dBC - dCA) < 100, $"BC={dBC}, CA={dCA}");
    }

    [TestMethod]
    public void IsolatedNode_NearCenter()
    {
        var nodes = new List<GraphNode>
        {
            new("lonely", "text", 0, 0),
        };
        var edges = new List<GraphEdge>();

        var result = _layout.ComputeLayout(nodes, edges, 800, 600);

        Assert.IsTrue(result["lonely"].X > 300 && result["lonely"].X < 500);
        Assert.IsTrue(result["lonely"].Y > 200 && result["lonely"].Y < 400);
    }

    [TestMethod]
    public void EmptyGraph_ReturnsEmptyDictionary()
    {
        var result = _layout.ComputeLayout(new List<GraphNode>(), new List<GraphEdge>(), 800, 600);
        Assert.AreEqual(0, result.Count);
    }

    private static double Distance(Point a, Point b)
    {
        return Math.Sqrt(Math.Pow(a.X - b.X, 2) + Math.Pow(a.Y - b.Y, 2));
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
dotnet test src/NarrativeForge/NarrativeForge.Tests/
# Expected: FAIL — ForceDirectedLayout not found
```

- [ ] **Step 3: Implement ForceDirectedLayout.cs**

```csharp
using System.Windows;

namespace NarrativeForge.App.Layout;

public class ForceDirectedLayout : IGraphLayout
{
    public string Name => "Force-Directed";
    public string Description => "Spring physics layout with repulsion and attraction";
    
    public int MaxIterations { get; set; } = 200;
    public double RepulsionStrength { get; set; } = 5000;
    public double AttractionStrength { get; set; } = 0.01;
    public double Gravity { get; set; } = 0.1;
    public double Damping { get; set; } = 0.9;
    public double MinDistance { get; set; } = 50;
    public double IdealEdgeLength { get; set; } = 150;

    public Dictionary<string, Point> ComputeLayout(
        IReadOnlyList<GraphNode> nodes,
        IReadOnlyList<GraphEdge> edges,
        double canvasWidth,
        double canvasHeight)
    {
        if (nodes.Count == 0) return new Dictionary<string, Point>();

        var positions = nodes.ToDictionary(n => n.Id, n => new Vector(n.X, n.Y));
        var velocities = nodes.ToDictionary(n => n.Id, _ => new Vector(0, 0));
        var center = new Vector(canvasWidth / 2, canvasHeight / 2);

        var edgeSet = edges.ToHashSet();

        for (int iter = 0; iter < MaxIterations; iter++)
        {
            var forces = positions.ToDictionary(kv => kv.Key, _ => new Vector(0, 0));

            foreach (var a in positions)
            {
                foreach (var b in positions)
                {
                    if (a.Key == b.Key) continue;

                    var delta = a.Value - b.Value;
                    var dist = Math.Max(delta.Length, MinDistance);
                    var force = delta / dist * (RepulsionStrength / (dist * dist));
                    forces[a.Key] += force;
                }
            }

            foreach (var edge in edges)
            {
                if (!positions.ContainsKey(edge.SourceId) || !positions.ContainsKey(edge.TargetId))
                    continue;

                var delta = positions[edge.TargetId] - positions[edge.SourceId];
                var dist = delta.Length;
                var displacement = dist - IdealEdgeLength;
                var force = delta / Math.Max(dist, MinDistance) * (displacement * AttractionStrength);
                forces[edge.SourceId] += force;
                forces[edge.TargetId] -= force;
            }

            foreach (var kv in positions)
            {
                var toCenter = center - kv.Value;
                forces[kv.Key] += toCenter * Gravity;
            }

            double totalMovement = 0;
            foreach (var kv in positions.ToList())
            {
                velocities[kv.Key] = (velocities[kv.Key] + forces[kv.Key]) * Damping;
                positions[kv.Key] += velocities[kv.Key];
                totalMovement += velocities[kv.Key].Length;
            }

            if (totalMovement < 0.1) break;
        }

        return positions.ToDictionary(kv => kv.Key, kv => new Point(kv.Value.X, kv.Value.Y));
    }
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
dotnet test src/NarrativeForge/NarrativeForge.Tests/
# Expected: 9 passed (5 hierarchical + 4 force-directed)
```

- [ ] **Step 5: Commit**

```bash
git add src/NarrativeForge/NarrativeForge.App/Layout/ForceDirectedLayout.cs src/NarrativeForge/NarrativeForge.Tests/Layout/ForceDirectedLayoutTests.cs
git commit -m "feat: add force-directed layout algorithm with spring physics"
```

---

## Task 4: Layout Animator

**Covers:** [S7]

**Files:**
- Create: `src/NarrativeForge/NarrativeForge.App/Controls/LayoutAnimator.cs`

**Interfaces:**
- Consumes: GraphNodeViewModel from existing code
- Produces: LayoutAnimator static class with AnimateLayout method

- [ ] **Step 1: Create LayoutAnimator.cs**

```csharp
using System.Windows;
using System.Windows.Media.Animation;
using NarrativeForge.App.ViewModels;

namespace NarrativeForge.App.Controls;

public static class LayoutAnimator
{
    public static Task AnimateLayout(
        IEnumerable<GraphNodeViewModel> nodes,
        Dictionary<string, Point> targetPositions,
        TimeSpan? duration = null)
    {
        var tcs = new TaskCompletionSource();
        var storyboard = new Storyboard();

        var nodeCount = nodes.Count();
        var animDuration = duration ?? TimeSpan.FromMilliseconds(Math.Min(500, 200 + nodeCount * 10));

        foreach (var node in nodes)
        {
            if (!targetPositions.TryGetValue(node.Id, out var target)) continue;

            var xAnim = new DoubleAnimation(target.X, animDuration)
            {
                EasingFunction = new ExponentialEase { EasingMode = EasingMode.EaseOut },
            };
            Storyboard.SetTarget(xAnim, new ObjectTarget(node));
            Storyboard.SetTargetProperty(xAnim, new PropertyPath(nameof(GraphNodeViewModel.X)));
            storyboard.Children.Add(xAnim);

            var yAnim = new DoubleAnimation(target.Y, animDuration)
            {
                EasingFunction = new ExponentialEase { EasingMode = EasingMode.EaseOut },
            };
            Storyboard.SetTarget(yAnim, new ObjectTarget(node));
            Storyboard.SetTargetProperty(yAnim, new PropertyPath(nameof(GraphNodeViewModel.Y)));
            storyboard.Children.Add(yAnim);
        }

        storyboard.Completed += (_, _) => tcs.TrySetResult();
        storyboard.Begin();

        return tcs.Task;
    }
}
```

- [ ] **Step 2: Build and verify**

```bash
dotnet build src/NarrativeForge/NarrativeForge.App/NarrativeForge.App.csproj
# Expected: Build succeeded
```

- [ ] **Step 3: Commit**

```bash
git add src/NarrativeForge/NarrativeForge.App/Controls/LayoutAnimator.cs
git commit -m "feat: add LayoutAnimator with smooth WPF Storyboard transitions"
```

---

## Task 5: Layout Commands in GraphEditorViewModel

**Covers:** [S8]

**Files:**
- Modify: `src/NarrativeForge/NarrativeForge.App/ViewModels/GraphEditorViewModel.cs`

**Interfaces:**
- Consumes: IGraphLayout, LayoutAnimator from Tasks 1-4
- Produces: LayoutHierarchicalCommand, LayoutForceDirectedCommand

- [ ] **Step 1: Add layout commands to GraphEditorViewModel**

```csharp
// Add to GraphEditorViewModel.cs

[ObservableProperty] private bool _isLayouting;
[ObservableProperty] private string _lastLayoutAlgorithm = "Hierarchical";

private readonly HierarchicalLayout _hierarchicalLayout = new();
private readonly ForceDirectedLayout _forceDirectedLayout = new();

[RelayCommand]
private async Task LayoutHierarchicalAsync()
{
    if (Nodes.Count == 0) return;
    IsLayouting = true;
    LastLayoutAlgorithm = "Hierarchical";

    var graphNodes = Nodes.Select(n => new GraphNode(n.Id, n.NodeType, n.X, n.Y)).ToList();
    var graphEdges = Edges.Select(e => new GraphEdge(e.SourceId, e.TargetId, e.Condition)).ToList();

    var positions = _hierarchicalLayout.ComputeLayout(graphNodes, graphEdges, 1200, 800);
    await LayoutAnimator.AnimateLayout(Nodes, positions);

    foreach (var node in Nodes)
    {
        if (positions.TryGetValue(node.Id, out var pos))
        {
            node.X = pos.X;
            node.Y = pos.Y;
        }
    }

    IsLayouting = false;
    IsDirty = true;
}

[RelayCommand]
private async Task LayoutForceDirectedAsync()
{
    if (Nodes.Count == 0) return;
    IsLayouting = true;
    LastLayoutAlgorithm = "Force-Directed";

    var graphNodes = Nodes.Select(n => new GraphNode(n.Id, n.NodeType, n.X, n.Y)).ToList();
    var graphEdges = Edges.Select(e => new GraphEdge(e.SourceId, e.TargetId, e.Condition)).ToList();

    var positions = _forceDirectedLayout.ComputeLayout(graphNodes, graphEdges, 1200, 800);
    await LayoutAnimator.AnimateLayout(Nodes, positions);

    foreach (var node in Nodes)
    {
        if (positions.TryGetValue(node.Id, out var pos))
        {
            node.X = pos.X;
            node.Y = pos.Y;
        }
    }

    IsLayouting = false;
    IsDirty = true;
}

[RelayCommand]
private async Task LayoutLastUsedAsync()
{
    if (LastLayoutAlgorithm == "Force-Directed")
        await LayoutForceDirectedAsync();
    else
        await LayoutHierarchicalAsync();
}
```

- [ ] **Step 2: Build and verify**

```bash
dotnet build src/NarrativeForge/NarrativeForge.App/NarrativeForge.App.csproj
# Expected: Build succeeded
```

- [ ] **Step 3: Commit**

```bash
git add src/NarrativeForge/NarrativeForge.App/ViewModels/GraphEditorViewModel.cs
git commit -m "feat: add layout commands to GraphEditorViewModel"
```

---

## Task 6: Toolbar Button & Keyboard Shortcut

**Covers:** [S8]

**Files:**
- Modify: `src/NarrativeForge/NarrativeForge.App/MainWindow.xaml`

**Interfaces:**
- Consumes: Layout commands from Task 5
- Produces: Auto Layout toolbar button with dropdown

- [ ] **Step 1: Add toolbar button to MainWindow.xaml**

Add to the graph editor toolbar section:

```xml
<!-- Auto Layout -->
<MenuItem Header="_Auto Layout">
    <MenuItem Header="_Hierarchical" 
              Command="{Binding GraphEditor.LayoutHierarchicalCommand}"
              InputGestureText="Ctrl+L"/>
    <MenuItem Header="_Force-Directed" 
              Command="{Binding GraphEditor.LayoutForceDirectedCommand}"/>
    <Separator/>
    <MenuItem Header="_Last Used" 
              Command="{Binding GraphEditor.LayoutLastUsedCommand}"
              InputGestureText="Ctrl+L"/>
</MenuItem>
```

Add InputBindings for Ctrl+L:

```xml
<Window.InputBindings>
    <KeyBinding Key="L" Modifiers="Ctrl" 
                Command="{Binding GraphEditor.LayoutLastUsedCommand}"/>
</Window.InputBindings>
```

- [ ] **Step 2: Build and verify**

```bash
dotnet build src/NarrativeForge/NarrativeForge.App/NarrativeForge.App.csproj
# Expected: Build succeeded
```

- [ ] **Step 3: Commit**

```bash
git add src/NarrativeForge/NarrativeForge.App/MainWindow.xaml
git commit -m "feat: add auto layout toolbar button and Ctrl+L keyboard shortcut"
```

---

## Task 7: End-to-End Build Verification

**Covers:** [S9, S10]

**Files:**
- Verify all previous tasks

**Interfaces:**
- Consumes: All previous tasks
- Produces: Verified build and clean compile

- [ ] **Step 1: Full build**

```bash
dotnet build src/NarrativeForge/NarrativeForge.sln
# Expected: Build succeeded, 0 errors
```

- [ ] **Step 2: Run all tests**

```bash
dotnet test src/NarrativeForge/NarrativeForge.Tests/
python -m pytest tests/ -q
# Expected: All tests pass
```

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "feat: Phase 5 complete — auto-layout algorithms for graph editor"
```
