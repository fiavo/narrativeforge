using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using NarrativeForge.App.Services;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.ViewModels;

public partial class GraphEditorViewModel : ObservableObject
{
    private readonly UndoRedoManager _undoRedo = new();
    [ObservableProperty]
    private string _graphName = string.Empty;

    [ObservableProperty]
    private Guid _startNodeId;

    [ObservableProperty]
    private GraphNodeViewModel? _selectedNode;

    [ObservableProperty]
    private GraphEdgeViewModel? _selectedEdge;

    [ObservableProperty]
    private bool _isDirty;

    public ObservableCollection<GraphNodeViewModel> Nodes { get; } = [];

    public ObservableCollection<GraphEdgeViewModel> Edges { get; } = [];

    [RelayCommand(CanExecute = nameof(CanUndo))]
    private void Undo()
    {
        _undoRedo.Undo();
        NotifyUndoRedoStateChanged();
    }

    [RelayCommand(CanExecute = nameof(CanRedo))]
    private void Redo()
    {
        _undoRedo.Redo();
        NotifyUndoRedoStateChanged();
    }

    public bool CanUndo => _undoRedo.CanUndo;
    public bool CanRedo => _undoRedo.CanRedo;

    public void MoveNode(GraphNodeViewModel node, double oldX, double oldY, double newX, double newY)
    {
        _undoRedo.Execute(new MoveNodeAction(this, node, oldX, oldY, newX, newY));
        NotifyUndoRedoStateChanged();
    }

    [RelayCommand]
    private void AddNode(string nodeType = "dialogue")
    {
        var node = new GraphNodeViewModel
        {
            NodeType = nodeType,
            Title = $"New {nodeType}",
            X = 100 + Nodes.Count * 50,
            Y = 100 + Nodes.Count * 50
        };
        _undoRedo.Execute(new AddNodeAction(this, node));
        NotifyUndoRedoStateChanged();
    }

    [RelayCommand]
    private void DeleteNode(Guid nodeId)
    {
        var node = Nodes.FirstOrDefault(n => n.Id == nodeId);
        if (node is null) return;
        _undoRedo.Execute(new DeleteNodeAction(this, node));
        NotifyUndoRedoStateChanged();
    }

    public void ConnectNodes(Guid sourceId, Guid targetId, string condition = "")
    {
        if (sourceId == targetId) return;
        if (Edges.Any(e => e.SourceId == sourceId && e.TargetId == targetId)) return;

        var edge = new GraphEdgeViewModel
        {
            SourceId = sourceId,
            TargetId = targetId,
            Condition = condition
        };
        _undoRedo.Execute(new ConnectEdgeAction(this, edge));
        NotifyUndoRedoStateChanged();
    }

    [RelayCommand]
    private void DeleteEdge(Guid edgeId)
    {
        var edge = Edges.FirstOrDefault(e => e.Id == edgeId);
        if (edge is null) return;
        _undoRedo.Execute(new DeleteEdgeAction(this, edge));
        NotifyUndoRedoStateChanged();
    }

    [RelayCommand]
    private void ClearGraph()
    {
        _undoRedo.Clear();
        Nodes.Clear();
        Edges.Clear();
        SelectedNode = null;
        SelectedEdge = null;
        GraphName = string.Empty;
        StartNodeId = Guid.Empty;
        IsDirty = false;
        NotifyUndoRedoStateChanged();
    }

    private void NotifyUndoRedoStateChanged()
    {
        UndoCommand.NotifyCanExecuteChanged();
        RedoCommand.NotifyCanExecuteChanged();
    }

    public DialogueTreeDto ToDialogueTreeDto()
    {
        return new DialogueTreeDto
        {
            Id = Guid.NewGuid(),
            Name = GraphName,
            StartNodeId = StartNodeId,
            Nodes = Nodes.Select(n => new GraphNodeDto
            {
                Id = n.Id,
                Type = n.NodeType,
                Title = n.Title,
                Content = n.Content,
                X = n.X,
                Y = n.Y,
                Choices = n.Choices.Select(c => new GraphChoiceDto
                {
                    Id = c.Id,
                    Text = c.Text,
                    NextNodeId = c.NextNodeId,
                    Condition = c.Condition
                }).ToList(),
                Objectives = n.Objectives.Select(o => new GraphObjectiveDto
                {
                    Id = o.Id,
                    Description = o.Description,
                    Type = o.Type,
                    Target = o.Target
                }).ToList()
            }).ToList(),
            Edges = Edges.Select(e => new GraphEdgeDto
            {
                Id = e.Id,
                SourceId = e.SourceId,
                TargetId = e.TargetId,
                Condition = e.Condition
            }).ToList()
        };
    }

    public QuestGraphDto ToQuestGraphDto()
    {
        return new QuestGraphDto
        {
            Id = Guid.NewGuid(),
            Name = GraphName,
            StartNodeId = StartNodeId,
            Nodes = Nodes.Select(n => new GraphNodeDto
            {
                Id = n.Id,
                Type = n.NodeType,
                Title = n.Title,
                Content = n.Content,
                X = n.X,
                Y = n.Y,
                Choices = n.Choices.Select(c => new GraphChoiceDto
                {
                    Id = c.Id,
                    Text = c.Text,
                    NextNodeId = c.NextNodeId,
                    Condition = c.Condition
                }).ToList(),
                Objectives = n.Objectives.Select(o => new GraphObjectiveDto
                {
                    Id = o.Id,
                    Description = o.Description,
                    Type = o.Type,
                    Target = o.Target
                }).ToList()
            }).ToList(),
            Edges = Edges.Select(e => new GraphEdgeDto
            {
                Id = e.Id,
                SourceId = e.SourceId,
                TargetId = e.TargetId,
                Condition = e.Condition
            }).ToList()
        };
    }

    public void LoadFromDialogueTree(DialogueTreeDto dto)
    {
        ClearGraph();
        _undoRedo.Clear();
        GraphName = dto.Name;
        StartNodeId = dto.StartNodeId;

        foreach (var nodeDto in dto.Nodes)
        {
            var node = new GraphNodeViewModel(nodeDto.Id, nodeDto.Type, nodeDto.Title, nodeDto.Content, nodeDto.X, nodeDto.Y);
            foreach (var choiceDto in nodeDto.Choices)
                node.Choices.Add(new ChoiceViewModel(choiceDto.Id, choiceDto.Text, choiceDto.NextNodeId, choiceDto.Condition));
            foreach (var objectiveDto in nodeDto.Objectives)
                node.Objectives.Add(new ObjectiveViewModel(objectiveDto.Id, objectiveDto.Description, objectiveDto.Type, objectiveDto.Target));
            Nodes.Add(node);
        }

        foreach (var edgeDto in dto.Edges)
            Edges.Add(new GraphEdgeViewModel(edgeDto.Id, edgeDto.SourceId, edgeDto.TargetId, edgeDto.Condition));

        IsDirty = false;
    }

    public void LoadFromQuestGraph(QuestGraphDto dto)
    {
        ClearGraph();
        _undoRedo.Clear();
        GraphName = dto.Name;
        StartNodeId = dto.StartNodeId;

        foreach (var nodeDto in dto.Nodes)
        {
            var node = new GraphNodeViewModel(nodeDto.Id, nodeDto.Type, nodeDto.Title, nodeDto.Content, nodeDto.X, nodeDto.Y);
            foreach (var choiceDto in nodeDto.Choices)
                node.Choices.Add(new ChoiceViewModel(choiceDto.Id, choiceDto.Text, choiceDto.NextNodeId, choiceDto.Condition));
            foreach (var objectiveDto in nodeDto.Objectives)
                node.Objectives.Add(new ObjectiveViewModel(objectiveDto.Id, objectiveDto.Description, objectiveDto.Type, objectiveDto.Target));
            Nodes.Add(node);
        }

        foreach (var edgeDto in dto.Edges)
            Edges.Add(new GraphEdgeViewModel(edgeDto.Id, edgeDto.SourceId, edgeDto.TargetId, edgeDto.Condition));

        IsDirty = false;
    }
}
