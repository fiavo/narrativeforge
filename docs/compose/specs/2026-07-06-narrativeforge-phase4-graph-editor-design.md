# NarrativeForge Phase 4: Visual Graph Editor — Design Spec

## [S1] Problem Statement

Phase 3 delivered branching dialogue trees and quest graphs with Ink parsing, but no visual way to create or edit them. Game developers need a visual node editor to design dialogue flows and quest chains — seeing the full graph structure, dragging nodes into place, connecting them with edges, and editing properties in real-time. Without this, developers must write Ink scripts manually or use external tools.

## [S2] Solution Overview

Build a generic visual graph editor as a custom WPF `GraphCanvas` control using pure WPF Canvas with attached behaviors. The editor works for both dialogue trees and quest graphs. Nodes render as styled UserControls with connection ports. Edges render as Bezier curves with arrows. A side panel shows editable properties for the selected node. The editor integrates with the existing Python backend API for loading and saving.

## [S3] Architecture Approach

**Custom Canvas with Attached Behaviors.** A `GraphCanvas` control extends WPF's `Canvas`. Attached behaviors handle drag, connect, zoom, pan, and select. Nodes and edges render via `ItemsControl` with `DataTemplate`. A `GraphEditorViewModel` manages state and coordinates with the API. No external graph libraries — full control over rendering and interaction.

## [S4] GraphCanvas Control

### Core API

```csharp
public class GraphCanvas : Canvas
{
    public static readonly DependencyProperty NodesProperty;
    public static readonly DependencyProperty EdgesProperty;
    public static readonly DependencyProperty SelectedNodeProperty;
    public static readonly DependencyProperty ZoomProperty;
    public static readonly DependencyProperty PanOffsetProperty;

    public event EventHandler<NodeEventArgs> NodeSelected;
    public event EventHandler<NodeEventArgs> NodeMoved;
    public event EventHandler<EdgeEventArgs> EdgeCreated;
    public event EventHandler<NodeEventArgs> NodeDoubleClick;

    public void ZoomToFit();
    public void CenterOnNode(string nodeId);
    public Point GetNodePosition(string nodeId);
    public void SetNodePosition(string nodeId, Point position);
}
```

### Node Rendering

Each node is a UserControl with:
- Header bar colored by node type (green=TEXT, blue=CHOICE, orange=CONDITION, purple=JUMP, red=END)
- Title text
- Connection ports (input top, output bottom)
- Selection highlight border (blue glow)

### Edge Rendering

Edges are Polyline elements with:
- Bezier curve path between node ports
- Arrow head at target end
- Color: gray (default), green (true branch), red (false branch)
- Thickness: 2px normal, 4px selected

### Attached Behaviors

| Behavior | Input | Action |
|----------|-------|--------|
| DragBehavior | LeftMouseDown + Move | Translates node position on canvas |
| ConnectBehavior | DragFromOutputPort | Draws temporary edge, snaps to input port on release |
| ZoomBehavior | MouseWheel | Scales canvas via RenderTransform |
| PanBehavior | MiddleMouse + Move | Translates canvas offset |
| SelectBehavior | LeftClick on node | Sets SelectedNode, highlights node |

## [S5] ViewModel Design

### GraphEditorViewModel

```csharp
public partial class GraphEditorViewModel : ObservableObject
{
    [ObservableProperty] private string _currentGraphId;
    [ObservableProperty] private string _currentGraphType; // "dialogue" or "quest"
    [ObservableProperty] private string _graphName;
    [ObservableProperty] private object? _selectedNode;
    [ObservableProperty] private ObservableCollection<GraphNodeViewModel> _nodes;
    [ObservableProperty] private ObservableCollection<GraphEdgeViewModel> _edges;
    [ObservableProperty] private bool _isDirty;

    [RelayCommand] private async Task LoadGraphAsync(string graphId, string type);
    [RelayCommand] private async Task SaveGraphAsync();
    [RelayCommand] private async Task AddNodeAsync(string nodeType);
    [RelayCommand] private async Task DeleteSelectedAsync();
    [RelayCommand] private async Task ConnectNodesAsync(string sourceId, string targetId);
    [RelayCommand] private void ZoomToFit();
}
```

### GraphNodeViewModel

```csharp
public partial class GraphNodeViewModel : ObservableObject
{
    public string Id { get; set; }
    public string NodeType { get; set; }      // "text", "choice", "condition", etc.
    public string Title { get; set; }
    public string Content { get; set; }
    public double X { get; set; }
    public double Y { get; set; }
    public bool IsSelected { get; set; }
    public Brush HeaderColor { get; set; }
    public List<ChoiceViewModel> Choices { get; set; }     // dialogue only
    public List<ObjectiveViewModel> Objectives { get; set; } // quest only
    public Dictionary<string, string> VariablesSet { get; set; }
}
```

### GraphEdgeViewModel

```csharp
public partial class GraphEdgeViewModel : ObservableObject
{
    public string Id { get; set; }
    public string SourceId { get; set; }
    public string TargetId { get; set; }
    public string Condition { get; set; }
    public Brush EdgeColor { get; set; }
}
```

## [S6] Property Panel

### Layout

Right-side panel showing editable properties for the selected node. Different sections appear based on node type:

**Common fields:** Node Type (dropdown), Title, Content

**TEXT node:** Content text area
**CHOICE node:** List of choices — each with text, condition expression, next node dropdown
**CONDITION node:** Expression input, true-branch node dropdown, false-branch node dropdown
**VARIABLE node:** Key-value pair list
**JUMP node:** Target node dropdown
**END node:** No additional fields

**Quest-specific additions:**
- OBJECTIVE: description, type dropdown (kill/collect/explore/talk/solve), target
- REWARD: XP number, gold number, items list
- FAIL: failure message

### Node Type Colors

| Type | Color |
|------|-------|
| TEXT | Green (#A6E3A1) |
| CHOICE | Blue (#89B4FA) |
| CONDITION | Orange (#FAB387) |
| VARIABLE | Yellow (#F9E2AF) |
| JUMP | Purple (#CBA6F7) |
| END | Red (#F38BA8) |
| OBJECTIVE | Teal (#94E2D5) |
| REWARD | Gold (#E6AF6E) |
| FAIL | Dark Red (#E06070) |

## [S7] API Integration

### ApiClient Extensions

```csharp
// Dialogue Trees
Task<DialogueTreeDto?> GetDialogueTreeAsync(string treeId);
Task<List<DialogueTreeDto>> GetDialogueTreesAsync(Guid projectId);
Task<DialogueTreeDto?> CreateDialogueTreeAsync(Guid projectId, string name);
Task<bool> DeleteDialogueTreeAsync(string treeId);
Task<DialogueTreeDto?> SaveDialogueTreeAsync(string treeId, object graphData);

// Quest Graphs
Task<QuestGraphDto?> GetQuestGraphAsync(string graphId);
Task<List<QuestGraphDto>> GetQuestGraphsAsync(Guid projectId);
Task<QuestGraphDto?> CreateQuestGraphAsync(Guid projectId, string name);
Task<bool> DeleteQuestGraphAsync(string graphId);
Task<QuestGraphDto?> SaveQuestGraphAsync(string graphId, object graphData);
```

### DTOs

```csharp
public class GraphNodeDto
{
    public string Id { get; set; }
    public string Type { get; set; }
    public string Title { get; set; }
    public string Content { get; set; }
    public double X { get; set; }
    public double Y { get; set; }
    public List<GraphChoiceDto> Choices { get; set; }
    public List<GraphObjectiveDto> Objectives { get; set; }
    public Dictionary<string, string> VariablesSet { get; set; }
}

public class GraphEdgeDto
{
    public string Id { get; set; }
    public string SourceId { get; set; }
    public string TargetId { get; set; }
    public string Condition { get; set; }
}

public class DialogueTreeDto
{
    public string Id { get; set; }
    public string Name { get; set; }
    public string StartNodeId { get; set; }
    public List<GraphNodeDto> Nodes { get; set; }
    public List<GraphEdgeDto> Edges { get; set; }
}

public class QuestGraphDto
{
    public string Id { get; set; }
    public string Name { get; set; }
    public string StartNodeId { get; set; }
    public List<GraphNodeDto> Nodes { get; set; }
    public List<GraphEdgeDto> Edges { get; set; }
}
```

## [S8] MainWindow Integration

### Updated Layout

```
┌──────────┬──────────────────────────┬──────────────┐
│ Project  │     Graph Canvas         │  Properties  │
│ Explorer │     (zoomable, pannable) │    Panel     │
│          │                          │              │
│          │                          │  [Node       │
│          │                          │   Editor]    │
├──────────┤                          ├──────────────┤
│ Graph    │                          │  Node Type   │
│ List     │                          │  Title       │
│          │                          │  Content     │
│          │                          │  Choices/    │
│          │                          │  Conditions  │
└──────────┴──────────────────────────┴──────────────┘
```

### Navigation

- Left panel: Project list → Graph list (dialogue trees + quest graphs)
- Center: GraphCanvas with selected graph
- Right: Property panel for selected node
- Double-click canvas: Add node at cursor position
- Right-click node: Context menu (Delete, Set as Start, Duplicate)

## [S9] Scope Boundaries

### Included
- GraphCanvas custom control with zoom/pan
- Node rendering with type-colored headers
- Edge rendering with Bezier curves and arrows
- Drag-to-connect node creation
- Property panel with type-specific fields
- GraphEditorViewModel with load/save/add/delete/connect
- ApiClient extensions for dialogue tree and quest graph CRUD
- DTOs for graph data transfer
- Integration with existing MainWindow layout
- Undo/redo for node operations (add, move, delete, connect)

### Deferred to Phase 5+
- Auto-layout algorithms (force-directed, hierarchical)
- Graph minimap
- Multiple selection and batch operations
- Copy/paste nodes
- Import/export to other formats (Yarn Spinner, Twine)
- Real-time collaboration
- Node grouping/subgraphs
- Animation and transitions
