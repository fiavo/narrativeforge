using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.ViewModels;

public partial class GraphEditorViewModel : ObservableObject
{
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
        Nodes.Add(node);
        SelectedNode = node;
        IsDirty = true;
    }

    [RelayCommand]
    private void DeleteNode(Guid nodeId)
    {
        var node = Nodes.FirstOrDefault(n => n.Id == nodeId);
        if (node is null) return;

        var connectedEdges = Edges.Where(e => e.SourceId == nodeId || e.TargetId == nodeId).ToList();
        foreach (var edge in connectedEdges)
            Edges.Remove(edge);

        Nodes.Remove(node);

        if (SelectedNode?.Id == nodeId)
            SelectedNode = null;

        IsDirty = true;
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
        Edges.Add(edge);
        IsDirty = true;
    }

    [RelayCommand]
    private void DeleteEdge(Guid edgeId)
    {
        var edge = Edges.FirstOrDefault(e => e.Id == edgeId);
        if (edge is null) return;

        Edges.Remove(edge);

        if (SelectedEdge?.Id == edgeId)
            SelectedEdge = null;

        IsDirty = true;
    }

    [RelayCommand]
    private void ClearGraph()
    {
        Nodes.Clear();
        Edges.Clear();
        SelectedNode = null;
        SelectedEdge = null;
        GraphName = string.Empty;
        StartNodeId = Guid.Empty;
        IsDirty = false;
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
