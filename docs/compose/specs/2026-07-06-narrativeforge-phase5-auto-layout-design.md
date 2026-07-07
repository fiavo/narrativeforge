# NarrativeForge Phase 5: Auto-Layout Algorithms — Design Spec

## [S1] Problem Statement

Phase 4 delivered a visual graph editor with manual node positioning. When users create dialogue trees or quest graphs, nodes are placed at naive diagonal offsets. For complex graphs with many nodes, this produces cluttered, unreadable layouts. Game developers need automatic layout algorithms to organize their graphs into clean, hierarchical structures or physics-based arrangements.

## [S2] Solution Overview

Build a pure C# layout engine with two algorithms (hierarchical and force-directed) that compute optimal node positions. An WPF animation system moves nodes smoothly from old to new positions. Users trigger layout via toolbar button or Ctrl+L shortcut. The layout engine is testable without WPF; animations are WPF-specific.

## [S3] Architecture Approach

**Hybrid — C# Engine + WPF Animations.** Layout algorithms live in a pure C# `LayoutEngine` namespace with no WPF dependency. The `GraphEditorViewModel` calls the engine to compute positions. A `LayoutAnimator` WPF class uses `Storyboard` and `DoubleAnimation` to smoothly move nodes. Clean separation: engine is testable, animation is UI-specific.

## [S4] Layout Engine Interface

```csharp
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

public record GraphNode(string Id, string Type, double X, double Y);
public record GraphEdge(string SourceId, string TargetId, string Condition);
```

## [S5] Hierarchical Layout (Sugiyama-style)

### Algorithm

1. **Layer assignment** — Assign each node to a layer based on longest path from root (BFS/DFS)
2. **Ordering** — Minimize edge crossings within each layer (barycenter heuristic)
3. **Positioning** — Place nodes within layers, centering children under parents
4. **Coordinates** — Map layer indices to Y coordinates, node indices to X coordinates

### Parameters

```csharp
public class HierarchicalLayout : IGraphLayout
{
    public double LayerSpacing { get; set; } = 120;  // vertical gap between layers
    public double NodeSpacing { get; set; } = 200;   // horizontal gap between nodes
    public bool Direction { get; set; } = false;      // false=top-to-bottom, true=left-to-right
}
```

### Behavior

- Nodes with no incoming edges become roots (top layer)
- Nodes with no outgoing edges become leaves (bottom layer)
- Cycles are broken by treating the last edge in the cycle as a back-edge
- Orphan nodes (no connections) are placed in a separate row at the bottom

## [S6] Force-Directed Layout (Spring Physics)

### Algorithm

1. **Repulsion** — All nodes repel each other (Coulomb's law: F = k/d²)
2. **Attraction** — Connected nodes attract (Hooke's law: F = k*d)
3. **Gravity** — Weak central gravity prevents drift
4. **Iteration** — Repeat for N steps or until equilibrium

### Parameters

```csharp
public class ForceDirectedLayout : IGraphLayout
{
    public int MaxIterations { get; set; } = 200;
    public double RepulsionStrength { get; set; } = 5000;
    public double AttractionStrength { get; set; } = 0.01;
    public double Gravity { get; set; } = 0.1;
    public double Damping { get; set; } = 0.9;
    public double MinDistance { get; set; } = 50;
    public double IdealEdgeLength { get; set; } = 150;
}
```

### Behavior

- Starts with random positions (or current positions if available)
- Iterates until total movement < threshold or max iterations reached
- Produces organic, spring-physics-based layouts
- Good for undirected or complex graphs

## [S7] Layout Animator

### WPF Animation System

```csharp
namespace NarrativeForge.App.Controls;

public static class LayoutAnimator
{
    public static Task AnimateLayout(
        GraphCanvas canvas,
        Dictionary<string, Point> targetPositions,
        TimeSpan duration);
}
```

### Implementation

- Creates `DoubleAnimation` for each node's X and Y
- Groups animations in `Storyboard`
- Uses `ExponentialEase` easing for smooth deceleration
- Runs asynchronously, returns Task that completes when animation finishes
- During animation, node drag is disabled

### Duration

- Default: 500ms
- Scales with node count: min(500, 200 + nodes * 10) ms

## [S8] UI Integration

### Toolbar Button

Add "Auto Layout" button to graph editor toolbar:
- Icon: grid/layout icon
- Dropdown with: Hierarchical, Force-Directed
- Tooltip: "Automatically arrange nodes (Ctrl+L)"

### Keyboard Shortcut

- Ctrl+L: Trigger last-used layout algorithm
- Ctrl+Shift+L: Open layout algorithm selector

### Layout Settings Panel

Small collapsible panel below toolbar:
- Algorithm selector dropdown
- Hierarchical: Layer Spacing slider, Node Spacing slider
- Force-Directed: Iterations slider, Repulsion slider
- "Apply" button

### Status Bar

Show layout status during computation:
- "Computing hierarchical layout..."
- "Animating 24 nodes..."
- "Layout complete"

## [S9] Scope Boundaries

### Included
- IGraphLayout interface
- HierarchicalLayout (Sugiyama-style layer assignment, ordering, positioning)
- ForceDirectedLayout (spring physics with repulsion, attraction, gravity)
- LayoutAnimator with smooth WPF Storyboard animation
- Toolbar button with algorithm selector dropdown
- Keyboard shortcut Ctrl+L
- Layout settings panel with algorithm-specific parameters
- Status bar feedback during layout
- Unit tests for layout algorithms (pure C#, no WPF)

### Deferred to Phase 6+
- Circular layout
- Tree layout (strict parent-child)
- Minimap with layout preview
- Layout history (undo/redo layout changes)
- Custom layout constraints (pin node position, fix node layer)
- Layout export/import

## [S10] Testing Strategy

### Unit Tests (Layout Engine)

Pure C# tests, no WPF dependency:

- `HierarchicalLayoutTests`:
  - Single root with children → children in layer 1
  - Linear chain → layers 1,2,3,4
  - Diamond graph → proper layer assignment
  - Cycle handling → no infinite loop
  - Orphan nodes → placed at bottom

- `ForceDirectedLayoutTests`:
  - Two connected nodes → adjacent positions
  - Triangle graph → roughly equilateral spacing
  - Isolated node → near center
  - Convergence → movement < threshold after iterations

### Integration Tests

- Load graph → apply layout → verify all nodes have new X/Y coordinates
- Animation completes → verify final positions match computed positions

### Target: ~30 new tests
