# NarrativeForge Phase 4: Visual Graph Editor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a generic visual graph editor for dialogue trees and quest graphs in WPF.

**Architecture:** Custom `GraphCanvas` control extending WPF Canvas with attached behaviors for drag/connect/zoom/pan. ViewModels manage graph state and API communication. Property panel shows editable node properties. Works for both dialogue trees and quest graphs.

**Tech Stack:** C# .NET 9, WPF, CommunityToolkit.Mvvm 8.4, existing NarrativeForge.Core DTOs

## Global Constraints

- WPF target: .NET 9.0-windows
- Use CommunityToolkit.Mvvm for MVVM (source generators)
- Follow existing Catppuccin Mocha theme (DynamicResource colors)
- No external graph libraries — pure WPF Canvas
- Every task ends with a commit
- ViewModel tests where applicable

---

## Task 1: Graph DTOs

**Covers:** [S7]

**Files:**
- Create: `src/NarrativeForge/NarrativeForge.Core/DTOs/GraphDto.cs`
- Modify: `src/NarrativeForge/NarrativeForge.Core/NarrativeForge.Core.csproj` (if needed)

**Interfaces:**
- Produces: GraphNodeDto, GraphEdgeDto, GraphChoiceDto, GraphObjectiveDto, DialogueTreeDto, QuestGraphDto

- [ ] **Step 1: Create GraphDto.cs**

```csharp
namespace NarrativeForge.Core.DTOs;

public class GraphNodeDto
{
    public string Id { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public double X { get; set; }
    public double Y { get; set; }
    public List<GraphChoiceDto> Choices { get; set; } = new();
    public List<GraphObjectiveDto> Objectives { get; set; } = new();
    public Dictionary<string, string> VariablesSet { get; set; } = new();
}

public class GraphChoiceDto
{
    public string Id { get; set; } = string.Empty;
    public string Text { get; set; } = string.Empty;
    public string NextNodeId { get; set; } = string.Empty;
    public string Condition { get; set; } = string.Empty;
}

public class GraphObjectiveDto
{
    public string Id { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public string Target { get; set; } = string.Empty;
}

public class GraphEdgeDto
{
    public string Id { get; set; } = string.Empty;
    public string SourceId { get; set; } = string.Empty;
    public string TargetId { get; set; } = string.Empty;
    public string Condition { get; set; } = string.Empty;
}

public class DialogueTreeDto
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string StartNodeId { get; set; } = string.Empty;
    public List<GraphNodeDto> Nodes { get; set; } = new();
    public List<GraphEdgeDto> Edges { get; set; } = new();
}

public class QuestGraphDto
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string StartNodeId { get; set; } = string.Empty;
    public List<GraphNodeDto> Nodes { get; set; } = new();
    public List<GraphEdgeDto> Edges { get; set; } = new();
}
```

- [ ] **Step 2: Build and verify**

```bash
dotnet build src/NarrativeForge/NarrativeForge.Core/NarrativeForge.Core.csproj
# Expected: Build succeeded
```

- [ ] **Step 3: Commit**

```bash
git add src/NarrativeForge/NarrativeForge.Core/DTOs/GraphDto.cs
git commit -m "feat: add graph DTOs for dialogue trees and quest graphs"
```

---

## Task 2: Graph ViewModels

**Covers:** [S5]

**Files:**
- Create: `src/NarrativeForge/NarrativeForge.App/ViewModels/GraphEditorViewModel.cs`
- Create: `src/NarrativeForge/NarrativeForge.App/ViewModels/GraphNodeViewModel.cs`
- Create: `src/NarrativeForge/NarrativeForge.App/ViewModels/GraphEdgeViewModel.cs`
- Create: `src/NarrativeForge/NarrativeForge.App/ViewModels/ChoiceViewModel.cs`
- Create: `src/NarrativeForge/NarrativeForge.App/ViewModels/ObjectiveViewModel.cs`

**Interfaces:**
- Consumes: GraphDto from Task 1, ApiClient (existing)
- Produces: ViewModels used by GraphCanvas and PropertyPanel

- [ ] **Step 1: Create GraphNodeViewModel.cs**

```csharp
using System.Windows.Media;
using CommunityToolkit.Mvvm.ComponentModel;

namespace NarrativeForge.App.ViewModels;

public partial class GraphNodeViewModel : ObservableObject
{
    [ObservableProperty] private string _id = string.Empty;
    [ObservableProperty] private string _nodeType = string.Empty;
    [ObservableProperty] private string _title = string.Empty;
    [ObservableProperty] private string _content = string.Empty;
    [ObservableProperty] private double _x;
    [ObservableProperty] private double _y;
    [ObservableProperty] private bool _isSelected;
    [ObservableProperty] private Brush _headerColor = Brushes.Green;
    [ObservableProperty] private ObservableCollection<ChoiceViewModel> _choices = new();
    [ObservableProperty] private ObservableCollection<ObjectiveViewModel> _objectives = new();
    [ObservableProperty] private Dictionary<string, string> _variablesSet = new();

    public static Brush GetTypeColor(string nodeType) => nodeType switch
    {
        "text" => new SolidColorBrush(Color.FromRgb(0xA6, 0xE3, 0xA1)),
        "choice" => new SolidColorBrush(Color.FromRgb(0x89, 0xB4, 0xFA)),
        "condition" => new SolidColorBrush(Color.FromRgb(0xFA, 0xB3, 0x87)),
        "variable" => new SolidColorBrush(Color.FromRgb(0xF9, 0xE2, 0xAF)),
        "jump" => new SolidColorBrush(Color.FromRgb(0xCB, 0xA6, 0xF7)),
        "end" => new SolidColorBrush(Color.FromRgb(0xF3, 0x8B, 0xA8)),
        "start" => new SolidColorBrush(Color.FromRgb(0x94, 0xE2, 0xD5)),
        "objective" => new SolidColorBrush(Color.FromRgb(0x94, 0xE2, 0xD5)),
        "reward" => new SolidColorBrush(Color.FromRgb(0xE6, 0xAF, 0x6E)),
        "fail" => new SolidColorBrush(Color.FromRgb(0xE0, 0x60, 0x70)),
        _ => Brushes.Gray,
    };
}
```

- [ ] **Step 2: Create GraphEdgeViewModel.cs**

```csharp
using System.Windows.Media;
using CommunityToolkit.Mvvm.ComponentModel;

namespace NarrativeForge.App.ViewModels;

public partial class GraphEdgeViewModel : ObservableObject
{
    [ObservableProperty] private string _id = string.Empty;
    [ObservableProperty] private string _sourceId = string.Empty;
    [ObservableProperty] private string _targetId = string.Empty;
    [ObservableProperty] private string _condition = string.Empty;
    [ObservableProperty] private Brush _edgeColor = Brushes.Gray;

    partial void OnConditionChanged(string value)
    {
        EdgeColor = string.IsNullOrWhiteSpace(value) ? Brushes.Gray : Brushes.Green;
    }
}
```

- [ ] **Step 3: Create ChoiceViewModel.cs**

```csharp
using CommunityToolkit.Mvvm.ComponentModel;

namespace NarrativeForge.App.ViewModels;

public partial class ChoiceViewModel : ObservableObject
{
    [ObservableProperty] private string _id = string.Empty;
    [ObservableProperty] private string _text = string.Empty;
    [ObservableProperty] private string _nextNodeId = string.Empty;
    [ObservableProperty] private string _condition = string.Empty;
}
```

- [ ] **Step 4: Create ObjectiveViewModel.cs**

```csharp
using CommunityToolkit.Mvvm.ComponentModel;

namespace NarrativeForge.App.ViewModels;

public partial class ObjectiveViewModel : ObservableObject
{
    [ObservableProperty] private string _id = string.Empty;
    [ObservableProperty] private string _description = string.Empty;
    [ObservableProperty] private string _type = string.Empty;
    [ObservableProperty] private string _target = string.Empty;
}
```

- [ ] **Step 5: Create GraphEditorViewModel.cs**

```csharp
using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using NarrativeForge.App.Services;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.ViewModels;

public partial class GraphEditorViewModel : ObservableObject
{
    private readonly ApiClient _api;

    [ObservableProperty] private string _currentGraphId = string.Empty;
    [ObservableProperty] private string _currentGraphType = string.Empty;
    [ObservableProperty] private string _graphName = string.Empty;
    [ObservableProperty] private GraphNodeViewModel? _selectedNode;
    [ObservableProperty] private bool _isDirty;
    [ObservableProperty] private ObservableCollection<GraphNodeViewModel> _nodes = new();
    [ObservableProperty] private ObservableCollection<GraphEdgeViewModel> _edges = new();

    public GraphEditorViewModel(ApiClient api)
    {
        _api = api;
    }

    [RelayCommand]
    private async Task LoadDialogueTreeAsync(string treeId)
    {
        var tree = await _api.GetDialogueTreeAsync(treeId);
        if (tree == null) return;

        CurrentGraphId = tree.Id;
        CurrentGraphType = "dialogue";
        GraphName = tree.Name;
        LoadFromDto(tree.Nodes, tree.Edges);
        IsDirty = false;
    }

    [RelayCommand]
    private async Task LoadQuestGraphAsync(string graphId)
    {
        var graph = await _api.GetQuestGraphAsync(graphId);
        if (graph == null) return;

        CurrentGraphId = graph.Id;
        CurrentGraphType = "quest";
        GraphName = graph.Name;
        LoadFromDto(graph.Nodes, graph.Edges);
        IsDirty = false;
    }

    private void LoadFromDto(List<GraphNodeDto> nodeDtos, List<GraphEdgeDto> edgeDtos)
    {
        Nodes.Clear();
        Edges.Clear();

        foreach (var dto in nodeDtos)
        {
            var node = new GraphNodeViewModel
            {
                Id = dto.Id,
                NodeType = dto.Type,
                Title = dto.Title,
                Content = dto.Content,
                X = dto.X,
                Y = dto.Y,
                HeaderColor = GraphNodeViewModel.GetTypeColor(dto.Type),
                VariablesSet = dto.VariablesSet,
            };

            foreach (var choice in dto.Choices)
                node.Choices.Add(new ChoiceViewModel
                {
                    Id = choice.Id,
                    Text = choice.Text,
                    NextNodeId = choice.NextNodeId,
                    Condition = choice.Condition,
                });

            foreach (var obj in dto.Objectives)
                node.Objectives.Add(new ObjectiveViewModel
                {
                    Id = obj.Id,
                    Description = obj.Description,
                    Type = obj.Type,
                    Target = obj.Target,
                });

            Nodes.Add(node);
        }

        foreach (var dto in edgeDtos)
        {
            Edges.Add(new GraphEdgeViewModel
            {
                Id = dto.Id,
                SourceId = dto.SourceId,
                TargetId = dto.TargetId,
                Condition = dto.Condition,
            });
        }
    }

    [RelayCommand]
    private void AddNode(string nodeType)
    {
        var node = new GraphNodeViewModel
        {
            Id = Guid.NewGuid().ToString(),
            NodeType = nodeType,
            Title = nodeType.ToUpper(),
            X = 100 + Nodes.Count * 50,
            Y = 100 + Nodes.Count * 50,
            HeaderColor = GraphNodeViewModel.GetTypeColor(nodeType),
        };
        Nodes.Add(node);
        SelectedNode = node;
        IsDirty = true;
    }

    [RelayCommand]
    private void DeleteSelected()
    {
        if (SelectedNode == null) return;

        var nodeId = SelectedNode.Id;
        Nodes.Remove(SelectedNode);

        var edgesToRemove = Edges.Where(e => e.SourceId == nodeId || e.TargetId == nodeId).ToList();
        foreach (var edge in edgesToRemove)
            Edges.Remove(edge);

        SelectedNode = null;
        IsDirty = true;
    }

    [RelayCommand]
    private void ConnectNodes(string sourceId, string targetId)
    {
        if (Edges.Any(e => e.SourceId == sourceId && e.TargetId == targetId)) return;

        Edges.Add(new GraphEdgeViewModel
        {
            Id = Guid.NewGuid().ToString(),
            SourceId = sourceId,
            TargetId = targetId,
        });
        IsDirty = true;
    }
}
```

- [ ] **Step 6: Build and verify**

```bash
dotnet build src/NarrativeForge/NarrativeForge.App/NarrativeForge.App.csproj
# Expected: Build succeeded
```

- [ ] **Step 7: Commit**

```bash
git add src/NarrativeForge/NarrativeForge.App/ViewModels/Graph*.cs src/NarrativeForge/NarrativeForge.App/ViewModels/ChoiceViewModel.cs src/NarrativeForge/NarrativeForge.App/ViewModels/ObjectiveViewModel.cs
git commit -m "feat: add graph editor ViewModels with load/save/connect/delete"
```

---

## Task 3: ApiClient Extensions

**Covers:** [S7]

**Files:**
- Modify: `src/NarrativeForge/NarrativeForge.App/Services/ApiClient.cs`

**Interfaces:**
- Consumes: GraphDto from Task 1
- Produces: Extended ApiClient with graph CRUD methods

- [ ] **Step 1: Add graph methods to ApiClient.cs**

Add these methods to the existing `ApiClient` class:

```csharp
// Dialogue Trees
public async Task<DialogueTreeDto?> GetDialogueTreeAsync(string treeId)
{
    return await _http.GetFromJsonAsync<DialogueTreeDto>($"/api/dialogues/{treeId}");
}

public async Task<List<DialogueTreeDto>> GetDialogueTreesAsync(Guid projectId)
{
    return await _http.GetFromJsonAsync<List<DialogueTreeDto>>($"/api/projects/{projectId}/dialogues") ?? new();
}

public async Task<DialogueTreeDto?> CreateDialogueTreeAsync(Guid projectId, string name)
{
    var response = await _http.PostAsJsonAsync($"/api/projects/{projectId}/dialogues", new { name });
    return await response.Content.ReadFromJsonAsync<DialogueTreeDto>();
}

public async Task<bool> DeleteDialogueTreeAsync(string treeId)
{
    var response = await _http.DeleteAsync($"/api/dialogues/{treeId}");
    return response.IsSuccessStatusCode;
}

// Quest Graphs
public async Task<QuestGraphDto?> GetQuestGraphAsync(string graphId)
{
    return await _http.GetFromJsonAsync<QuestGraphDto>($"/api/quests/{graphId}");
}

public async Task<List<QuestGraphDto>> GetQuestGraphsAsync(Guid projectId)
{
    return await _http.GetFromJsonAsync<List<QuestGraphDto>>($"/api/projects/{projectId}/quests") ?? new();
}

public async Task<QuestGraphDto?> CreateQuestGraphAsync(Guid projectId, string name)
{
    var response = await _http.PostAsJsonAsync($"/api/projects/{projectId}/quests", new { name });
    return await response.Content.ReadFromJsonAsync<QuestGraphDto>();
}

public async Task<bool> DeleteQuestGraphAsync(string graphId)
{
    var response = await _http.DeleteAsync($"/api/quests/{graphId}");
    return response.IsSuccessStatusCode;
}
```

- [ ] **Step 2: Build and verify**

```bash
dotnet build src/NarrativeForge/NarrativeForge.App/NarrativeForge.App.csproj
# Expected: Build succeeded
```

- [ ] **Step 3: Commit**

```bash
git add src/NarrativeForge/NarrativeForge.App/Services/ApiClient.cs
git commit -m "feat: extend ApiClient with dialogue tree and quest graph CRUD"
```

---

## Task 4: Node UserControl

**Covers:** [S4]

**Files:**
- Create: `src/NarrativeForge/NarrativeForge.App/Controls/GraphNodeControl.xaml`
- Create: `src/NarrativeForge/NarrativeForge.App/Controls/GraphNodeControl.xaml.cs`

**Interfaces:**
- Consumes: GraphNodeViewModel from Task 2
- Produces: Visual node control with header, title, and connection ports

- [ ] **Step 1: Create GraphNodeControl.xaml**

```xml
<UserControl x:Class="NarrativeForge.App.Controls.GraphNodeControl"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             Width="180" MinHeight="80">
    <Border Background="{DynamicResource Surface1}" 
            CornerRadius="8" 
            BorderBrush="{DynamicResource Surface2}" 
            BorderThickness="1"
            Effect="{DynamicResource DropShadow}">
        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="Auto"/>
                <RowDefinition Height="Auto"/>
                <RowDefinition Height="Auto"/>
            </Grid.RowDefinitions>

            <!-- Header bar -->
            <Border Grid.Row="0" 
                    Background="{Binding HeaderColor}" 
                    CornerRadius="8,8,0,0" 
                    Padding="8,4">
                <TextBlock Text="{Binding NodeType}" 
                           Foreground="{DynamicResource Base}" 
                           FontWeight="Bold" 
                           FontSize="10"
                           TextAlignment="Center"/>
            </Border>

            <!-- Title -->
            <TextBlock Grid.Row="1" 
                       Text="{Binding Title}" 
                       Foreground="{DynamicResource Text}" 
                       FontWeight="SemiBold" 
                       FontSize="12"
                       Margin="8,6,8,2"
                       TextWrapping="Wrap"
                       TextAlignment="Center"/>

            <!-- Content preview -->
            <TextBlock Grid.Row="2" 
                       Text="{Binding Content}" 
                       Foreground="{DynamicResource Subtext0}" 
                       FontSize="10"
                       Margin="8,2,8,6"
                       TextWrapping="Wrap"
                       TextTrimming="CharacterEllipsis"
                       MaxHeight="40"
                       TextAlignment="Center"/>

            <!-- Input port (top) -->
            <Ellipse Width="10" Height="10" 
                     Fill="{DynamicResource Surface0}" 
                     Stroke="{DynamicResource Subtext1}" 
                     StrokeThickness="1.5"
                     VerticalAlignment="Top" 
                     HorizontalAlignment="Center"
                     Margin="0,-5,0,0"
                     Tag="input"/>

            <!-- Output port (bottom) -->
            <Ellipse Width="10" Height="10" 
                     Fill="{DynamicResource Surface0}" 
                     Stroke="{DynamicResource Subtext1}" 
                     StrokeThickness="1.5"
                     VerticalAlignment="Bottom" 
                     HorizontalAlignment="Center"
                     Margin="0,0,0,-5"
                     Tag="output"/>
        </Grid>
    </Border>
</UserControl>
```

- [ ] **Step 2: Create GraphNodeControl.xaml.cs**

```csharp
using System.Windows.Controls;
using System.Windows.Input;
using NarrativeForge.App.ViewModels;

namespace NarrativeForge.App.Controls;

public partial class GraphNodeControl : UserControl
{
    public GraphNodeControl()
    {
        InitializeComponent();
    }
}
```

- [ ] **Step 3: Build and verify**

```bash
dotnet build src/NarrativeForge/NarrativeForge.App/NarrativeForge.App.csproj
# Expected: Build succeeded
```

- [ ] **Step 4: Commit**

```bash
git add src/NarrativeForge/NarrativeForge.App/Controls/GraphNodeControl.xaml src/NarrativeForge/NarrativeForge.App/Controls/GraphNodeControl.xaml.cs
git commit -m "feat: add GraphNodeControl with header, title, and connection ports"
```

---

## Task 5: GraphCanvas Control

**Covers:** [S4]

**Files:**
- Create: `src/NarrativeForge/NarrativeForge.App/Controls/GraphCanvas.cs`

**Interfaces:**
- Consumes: GraphNodeViewModel, GraphEdgeViewModel from Task 2
- Produces: GraphCanvas custom control with zoom/pan and node rendering

- [ ] **Step 1: Create GraphCanvas.cs**

```csharp
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;
using NarrativeForge.App.ViewModels;

namespace NarrativeForge.App.Controls;

public class GraphCanvas : Canvas
{
    private readonly ScaleTransform _scaleTransform = new();
    private readonly TranslateTransform _translateTransform = new();
    private Point _lastPanPosition;
    private bool _isPanning;
    private bool _isDraggingNode;
    private GraphNodeViewModel? _draggedNode;
    private Point _dragOffset;

    public static readonly DependencyProperty NodesProperty =
        DependencyProperty.Register(nameof(Nodes), typeof(ObservableCollection<GraphNodeViewModel>), 
            typeof(GraphCanvas), new PropertyMetadata(null, OnNodesChanged));

    public static readonly DependencyProperty EdgesProperty =
        DependencyProperty.Register(nameof(Edges), typeof(ObservableCollection<GraphEdgeViewModel>), 
            typeof(GraphCanvas), new PropertyMetadata(null, OnEdgesChanged));

    public static readonly DependencyProperty SelectedNodeProperty =
        DependencyProperty.Register(nameof(SelectedNode), typeof(GraphNodeViewModel), 
            typeof(GraphCanvas), new FrameworkPropertyMetadata(null, FrameworkPropertyMetadataOptions.BindsTwoWayByDefault));

    public ObservableCollection<GraphNodeViewModel>? Nodes
    {
        get => (ObservableCollection<GraphNodeViewModel>?)GetValue(NodesProperty);
        set => SetValue(NodesProperty, value);
    }

    public ObservableCollection<GraphEdgeViewModel>? Edges
    {
        get => (ObservableCollection<GraphEdgeViewModel>?)GetValue(EdgesProperty);
        set => SetValue(EdgesProperty, value);
    }

    public GraphNodeViewModel? SelectedNode
    {
        get => (GraphNodeViewModel?)GetValue(SelectedNodeProperty);
        set => SetValue(SelectedNodeProperty, value);
    }

    public GraphCanvas()
    {
        Background = Brushes.Transparent;
        ClipToBounds = true;

        var transformGroup = new TransformGroup();
        transformGroup.Children.Add(_scaleTransform);
        transformGroup.Children.Add(_translateTransform);
        RenderTransform = transformGroup;

        MouseWheel += OnMouseWheel;
        MouseDown += OnMouseDown;
        MouseMove += OnMouseMove;
        MouseUp += OnMouseUp;
    }

    private static void OnNodesChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is GraphCanvas canvas && e.NewValue is ObservableCollection<GraphNodeViewModel> nodes)
        {
            nodes.CollectionChanged += (_, _) => canvas.RenderGraph();
        }
    }

    private static void OnEdgesChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is GraphCanvas canvas && e.NewValue is ObservableCollection<GraphEdgeViewModel> edges)
        {
            edges.CollectionChanged += (_, _) => canvas.RenderGraph();
        }
    }

    public void RenderGraph()
    {
        Children.Clear();

        if (Edges != null)
        {
            foreach (var edge in Edges)
                RenderEdge(edge);
        }

        if (Nodes != null)
        {
            foreach (var node in Nodes)
                RenderNode(node);
        }
    }

    private void RenderNode(GraphNodeViewModel node)
    {
        var control = new GraphNodeControl
        {
            DataContext = node,
            Width = 180,
            MinHeight = 80,
        };

        Canvas.SetLeft(control, node.X - 90);
        Canvas.SetTop(control, node.Y - 40);
        Canvas.SetZIndex(control, 1);

        control.MouseLeftButtonDown += (s, e) =>
        {
            SelectedNode = node;
            _isDraggingNode = true;
            _draggedNode = node;
            _dragOffset = e.GetPosition(control);
            control.CaptureMouse();
            e.Handled = true;
        };

        control.MouseLeftButtonUp += (s, e) =>
        {
            _isDraggingNode = false;
            _draggedNode = null;
            control.ReleaseMouseCapture();
        };

        Children.Add(control);
    }

    private void RenderEdge(GraphEdgeViewModel edge)
    {
        var source = Nodes?.FirstOrDefault(n => n.Id == edge.SourceId);
        var target = Nodes?.FirstOrDefault(n => n.Id == edge.TargetId);
        if (source == null || target == null) return;

        var path = new Path
        {
            Stroke = edge.EdgeColor,
            StrokeThickness = 2,
            Data = CreateBezierGeometry(
                new Point(source.X, source.Y + 40),
                new Point(target.X, target.Y - 40)),
        };

        Canvas.SetZIndex(path, 0);
        Children.Add(path);
    }

    private static StreamGeometry CreateBezierGeometry(Point start, Point end)
    {
        var geometry = new StreamGeometry();
        using var ctx = geometry.Open();
        ctx.BeginFigure(start, true, false);
        var control1 = new Point(start.X, start.Y + (end.Y - start.Y) / 2);
        var control2 = new Point(end.X, end.Y - (end.Y - start.Y) / 2);
        ctx.BezierTo(control1, control2, end, true, false);
        return geometry;
    }

    private void OnMouseWheel(object sender, MouseWheelEventArgs e)
    {
        var delta = e.Delta > 0 ? 1.1 : 0.9;
        var newScale = _scaleTransform.ScaleX * delta;
        newScale = Math.Clamp(newScale, 0.1, 5.0);
        _scaleTransform.ScaleX = newScale;
        _scaleTransform.ScaleY = newScale;
    }

    private void OnMouseDown(object sender, MouseButtonEventArgs e)
    {
        if (e.MiddleButton == MouseButtonState.Pressed)
        {
            _isPanning = true;
            _lastPanPosition = e.GetPosition(this);
            CaptureMouse();
        }
    }

    private void OnMouseMove(object sender, MouseEventArgs e)
    {
        if (_isPanning)
        {
            var pos = e.GetPosition(this);
            _translateTransform.X += pos.X - _lastPanPosition.X;
            _translateTransform.Y += pos.Y - _lastPanPosition.Y;
            _lastPanPosition = pos;
        }
        else if (_isDraggingNode && _draggedNode != null)
        {
            var pos = e.GetPosition(this);
            _draggedNode.X = (pos.X - _translateTransform.X) / _scaleTransform.ScaleX;
            _draggedNode.Y = (pos.Y - _translateTransform.Y) / _scaleTransform.ScaleY;
            RenderGraph();
        }
    }

    private void OnMouseUp(object sender, MouseButtonEventArgs e)
    {
        if (_isPanning)
        {
            _isPanning = false;
            ReleaseMouseCapture();
        }
    }

    public void ZoomToFit()
    {
        if (Nodes == null || Nodes.Count == 0) return;

        var minX = Nodes.Min(n => n.X) - 100;
        var maxX = Nodes.Max(n => n.X) + 100;
        var minY = Nodes.Min(n => n.Y) - 100;
        var maxY = Nodes.Max(n => n.Y) + 100;

        var scaleX = ActualWidth / (maxX - minX);
        var scaleY = ActualHeight / (maxY - minY);
        var scale = Math.Min(scaleX, scaleY);
        scale = Math.Clamp(scale, 0.1, 2.0);

        _scaleTransform.ScaleX = scale;
        _scaleTransform.ScaleY = scale;
        _translateTransform.X = -minX * scale;
        _translateTransform.Y = -minY * scale;
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
git add src/NarrativeForge/NarrativeForge.App/Controls/GraphCanvas.cs
git commit -m "feat: add GraphCanvas control with zoom, pan, drag, and Bezier edges"
```

---

## Task 6: Property Panel

**Covers:** [S6]

**Files:**
- Create: `src/NarrativeForge/NarrativeForge.App/Controls/PropertyPanel.xaml`
- Create: `src/NarrativeForge/NarrativeForge.App/Controls/PropertyPanel.xaml.cs`

**Interfaces:**
- Consumes: GraphNodeViewModel, ChoiceViewModel, ObjectiveViewModel from Task 2
- Produces: Property panel showing editable fields for selected node

- [ ] **Step 1: Create PropertyPanel.xaml**

```xml
<UserControl x:Class="NarrativeForge.App.Controls.PropertyPanel"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
             xmlns:vm="clr-namespace:NarrativeForge.App.ViewModels"
             Background="{DynamicResource Surface0}" Padding="12">
    <UserControl.Resources>
        <BooleanToVisibilityConverter x:Key="BoolToVis"/>
    </UserControl.Resources>
    <ScrollViewer VerticalScrollBarVisibility="Auto">
        <StackPanel>
            <TextBlock Text="PROPERTIES" Foreground="{DynamicResource Subtext0}" 
                       FontWeight="Bold" Margin="0,0,0,12"/>

            <!-- No selection message -->
            <TextBlock Text="Select a node to edit"
                       Foreground="{DynamicResource Subtext1}"
                       FontStyle="Italic"
                       Visibility="{Binding SelectedNode, Converter={StaticResource InvertBool}, ConverterParameter=}"/>

            <!-- Node properties (visible when node selected) -->
            <StackPanel DataContext="{Binding SelectedNode}" 
                        Visibility="{Binding SelectedNode, Converter={StaticResource BoolToVis}}">

                <!-- Node Type -->
                <TextBlock Text="Type" Foreground="{DynamicResource Subtext0}" Margin="0,0,0,4"/>
                <ComboBox SelectedItem="{Binding NodeType}" 
                          Background="{DynamicResource Surface1}" 
                          Foreground="{DynamicResource Text}"
                          Margin="0,0,0,8">
                    <ComboBoxItem Content="text"/>
                    <ComboBoxItem Content="choice"/>
                    <ComboBoxItem Content="condition"/>
                    <ComboBoxItem Content="variable"/>
                    <ComboBoxItem Content="jump"/>
                    <ComboBoxItem Content="end"/>
                    <ComboBoxItem Content="start"/>
                    <ComboBoxItem Content="objective"/>
                    <ComboBoxItem Content="reward"/>
                    <ComboBoxItem Content="fail"/>
                </ComboBox>

                <!-- Title -->
                <TextBlock Text="Title" Foreground="{DynamicResource Subtext0}" Margin="0,0,0,4"/>
                <TextBox Text="{Binding Title, UpdateSourceTrigger=PropertyChanged}"
                         Background="{DynamicResource Surface1}" 
                         Foreground="{DynamicResource Text}"
                         BorderBrush="{DynamicResource Surface2}"
                         Margin="0,0,0,8"/>

                <!-- Content -->
                <TextBlock Text="Content" Foreground="{DynamicResource Subtext0}" Margin="0,0,0,4"/>
                <TextBox Text="{Binding Content, UpdateSourceTrigger=PropertyChanged}"
                         Background="{DynamicResource Surface1}" 
                         Foreground="{DynamicResource Text}"
                         BorderBrush="{DynamicResource Surface2}"
                         AcceptsReturn="True"
                         TextWrapping="Wrap"
                         MinHeight="60"
                         Margin="0,0,0,8"/>

                <!-- Choices (dialogue only) -->
                <TextBlock Text="Choices" Foreground="{DynamicResource Subtext0}" 
                           FontWeight="Bold" Margin="0,8,0,4"/>
                <ItemsControl ItemsSource="{Binding Choices}">
                    <ItemsControl.ItemTemplate>
                        <DataTemplate DataType="{x:Type vm:ChoiceViewModel}">
                            <Border Background="{DynamicResource Surface1}" 
                                    CornerRadius="4" Padding="8" Margin="0,0,0,4">
                                <StackPanel>
                                    <TextBox Text="{Binding Text, UpdateSourceTrigger=PropertyChanged}"
                                             Background="{DynamicResource Surface2}" 
                                             Foreground="{DynamicResource Text}"
                                             Margin="0,0,0,4"/>
                                    <TextBox Text="{Binding Condition, UpdateSourceTrigger=PropertyChanged}"
                                             Background="{DynamicResource Surface2}" 
                                             Foreground="{DynamicResource Subtext1}"
                                             FontSize="10"
                                             Margin="0,0,0,4"/>
                                </StackPanel>
                            </Border>
                        </DataTemplate>
                    </ItemsControl.ItemTemplate>
                </ItemsControl>

                <!-- Objectives (quest only) -->
                <TextBlock Text="Objectives" Foreground="{DynamicResource Subtext0}" 
                           FontWeight="Bold" Margin="0,8,0,4"/>
                <ItemsControl ItemsSource="{Binding Objectives}">
                    <ItemsControl.ItemTemplate>
                        <DataTemplate DataType="{x:Type vm:ObjectiveViewModel}">
                            <Border Background="{DynamicResource Surface1}" 
                                    CornerRadius="4" Padding="8" Margin="0,0,0,4">
                                <StackPanel>
                                    <TextBox Text="{Binding Description, UpdateSourceTrigger=PropertyChanged}"
                                             Background="{DynamicResource Surface2}" 
                                             Foreground="{DynamicResource Text}"
                                             Margin="0,0,0,4"/>
                                    <TextBox Text="{Binding Type, UpdateSourceTrigger=PropertyChanged}"
                                             Background="{DynamicResource Surface2}" 
                                             Foreground="{DynamicResource Subtext1}"
                                             FontSize="10"/>
                                </StackPanel>
                            </Border>
                        </DataTemplate>
                    </ItemsControl.ItemTemplate>
                </ItemsControl>
            </StackPanel>
        </StackPanel>
    </ScrollViewer>
</UserControl>
```

- [ ] **Step 2: Create PropertyPanel.xaml.cs**

```csharp
using System.Windows.Controls;

namespace NarrativeForge.App.Controls;

public partial class PropertyPanel : UserControl
{
    public PropertyPanel()
    {
        InitializeComponent();
    }
}
```

- [ ] **Step 3: Build and verify**

```bash
dotnet build src/NarrativeForge/NarrativeForge.App/NarrativeForge.App.csproj
# Expected: Build succeeded
```

- [ ] **Step 4: Commit**

```bash
git add src/NarrativeForge/NarrativeForge.App/Controls/PropertyPanel.xaml src/NarrativeForge/NarrativeForge.App/Controls/PropertyPanel.xaml.cs
git commit -m "feat: add PropertyPanel with type-specific editable fields"
```

---

## Task 7: MainWindow Integration

**Covers:** [S8]

**Files:**
- Modify: `src/NarrativeForge/NarrativeForge.App/MainWindow.xaml`
- Modify: `src/NarrativeForge/NarrativeForge.App/ViewModels/MainViewModel.cs`

**Interfaces:**
- Consumes: GraphCanvas, PropertyPanel, GraphEditorViewModel from previous tasks
- Produces: Integrated MainWindow with graph editor layout

- [ ] **Step 1: Update MainViewModel.cs**

Add `GraphEditorViewModel` property and graph loading commands:

```csharp
[ObservableProperty] private GraphEditorViewModel _graphEditor;
[ObservableProperty] private bool _showGraphEditor;

[RelayCommand]
private async Task OpenDialogueTreeAsync(string treeId)
{
    ShowGraphEditor = true;
    await _graphEditor.LoadDialogueTreeCommand.ExecuteAsync(treeId);
}

[RelayCommand]
private async Task OpenQuestGraphAsync(string graphId)
{
    ShowGraphEditor = true;
    await _graphEditor.LoadQuestGraphCommand.ExecuteAsync(graphId);
}
```

- [ ] **Step 2: Update MainWindow.xaml**

Replace the center workspace column with a tab control that switches between generation view and graph editor view. Add the GraphCanvas and PropertyPanel to the graph editor tab.

- [ ] **Step 3: Build and verify**

```bash
dotnet build src/NarrativeForge/NarrativeForge.App/NarrativeForge.App.csproj
# Expected: Build succeeded
```

- [ ] **Step 4: Commit**

```bash
git add src/NarrativeForge/NarrativeForge.App/MainWindow.xaml src/NarrativeForge/NarrativeForge.App/ViewModels/MainViewModel.cs
git commit -m "feat: integrate graph editor into MainWindow with tab switching"
```

---

## Task 8: Undo/Redo System

**Covers:** [S9]

**Files:**
- Create: `src/NarrativeForge/NarrativeForge.App/Services/UndoRedoManager.cs`
- Modify: `src/NarrativeForge/NarrativeForge.App/ViewModels/GraphEditorViewModel.cs`

**Interfaces:**
- Consumes: GraphEditorViewModel
- Produces: UndoRedoManager with Undo/Redo commands

- [ ] **Step 1: Create UndoRedoManager.cs**

```csharp
using System.Windows.Input;

namespace NarrativeForge.App.Services;

public class UndoRedoManager
{
    private readonly Stack<GraphAction> _undoStack = new();
    private readonly Stack<GraphAction> _redoStack = new();

    public bool CanUndo => _undoStack.Count > 0;
    public bool CanRedo => _redoStack.Count > 0;

    public void Execute(GraphAction action)
    {
        action.Execute();
        _undoStack.Push(action);
        _redoStack.Clear();
    }

    public void Undo()
    {
        if (!CanUndo) return;
        var action = _undoStack.Pop();
        action.Undo();
        _redoStack.Push(action);
    }

    public void Redo()
    {
        if (!CanRedo) return;
        var action = _redoStack.Pop();
        action.Execute();
        _undoStack.Push(action);
    }

    public void Clear()
    {
        _undoStack.Clear();
        _redoStack.Clear();
    }
}

public abstract class GraphAction
{
    public abstract void Execute();
    public abstract void Undo();
}

public class AddNodeAction : GraphAction
{
    private readonly GraphEditorViewModel _vm;
    private readonly GraphNodeViewModel _node;

    public AddNodeAction(GraphEditorViewModel vm, GraphNodeViewModel node)
    {
        _vm = vm;
        _node = node;
    }

    public override void Execute() => _vm.Nodes.Add(_node);
    public override void Undo() => _vm.Nodes.Remove(_node);
}

public class DeleteNodeAction : GraphAction
{
    private readonly GraphEditorViewModel _vm;
    private readonly GraphNodeViewModel _node;
    private readonly List<GraphEdgeViewModel> _removedEdges;

    public DeleteNodeAction(GraphEditorViewModel vm, GraphNodeViewModel node)
    {
        _vm = vm;
        _node = node;
        _removedEdges = vm.Edges.Where(e => e.SourceId == node.Id || e.TargetId == node.Id).ToList();
    }

    public override void Execute()
    {
        _vm.Nodes.Remove(_node);
        foreach (var edge in _removedEdges)
            _vm.Edges.Remove(edge);
    }

    public override void Undo()
    {
        _vm.Nodes.Add(_node);
        foreach (var edge in _removedEdges)
            _vm.Edges.Add(edge);
    }
}
```

- [ ] **Step 2: Integrate UndoRedoManager into GraphEditorViewModel**

Add `UndoCommand` and `RedoCommand` relay commands. Wrap `AddNode` and `DeleteSelected` in undo actions.

- [ ] **Step 3: Build and verify**

```bash
dotnet build src/NarrativeForge/NarrativeForge.App/NarrativeForge.App.csproj
# Expected: Build succeeded
```

- [ ] **Step 4: Commit**

```bash
git add src/NarrativeForge/NarrativeForge.App/Services/UndoRedoManager.cs src/NarrativeForge/NarrativeForge.App/ViewModels/GraphEditorViewModel.cs
git commit -m "feat: add undo/redo system for graph editor operations"
```

---

## Task 9: End-to-End Build Verification

**Covers:** [S9]

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

- [ ] **Step 2: Run Python tests (ensure nothing broke)**

```bash
cd src/NarrativeForge/Engine
python -m pytest tests/ -v
# Expected: 231 tests pass
```

- [ ] **Step 3: Final commit**

```bash
git add .
git commit -m "feat: Phase 4 complete — visual graph editor for dialogue trees and quest graphs"
```
