using NarrativeForge.App.ViewModels;

namespace NarrativeForge.App.Services;

public abstract class GraphAction
{
    protected readonly GraphEditorViewModel ViewModel;

    protected GraphAction(GraphEditorViewModel viewModel)
    {
        ViewModel = viewModel;
    }

    public abstract void Execute();
    public abstract void Undo();
}

public class AddNodeAction : GraphAction
{
    private readonly GraphNodeViewModel _node;

    public AddNodeAction(GraphEditorViewModel viewModel, GraphNodeViewModel node)
        : base(viewModel)
    {
        _node = node;
    }

    public override void Execute()
    {
        ViewModel.Nodes.Add(_node);
        ViewModel.SelectedNode = _node;
        ViewModel.IsDirty = true;
    }

    public override void Undo()
    {
        ViewModel.Nodes.Remove(_node);
        if (ViewModel.SelectedNode?.Id == _node.Id)
            ViewModel.SelectedNode = null;
        ViewModel.IsDirty = true;
    }
}

public class DeleteNodeAction : GraphAction
{
    private readonly GraphNodeViewModel _node;
    private readonly List<GraphEdgeViewModel> _connectedEdges = [];

    public DeleteNodeAction(GraphEditorViewModel viewModel, GraphNodeViewModel node)
        : base(viewModel)
    {
        _node = node;
    }

    public override void Execute()
    {
        _connectedEdges.AddRange(
            ViewModel.Edges.Where(e => e.SourceId == _node.Id || e.TargetId == _node.Id));

        foreach (var edge in _connectedEdges)
            ViewModel.Edges.Remove(edge);

        ViewModel.Nodes.Remove(_node);

        if (ViewModel.SelectedNode?.Id == _node.Id)
            ViewModel.SelectedNode = null;

        ViewModel.IsDirty = true;
    }

    public override void Undo()
    {
        ViewModel.Nodes.Add(_node);
        foreach (var edge in _connectedEdges)
            ViewModel.Edges.Add(edge);
        ViewModel.IsDirty = true;
    }
}

public class MoveNodeAction : GraphAction
{
    private readonly GraphNodeViewModel _node;
    private readonly double _oldX;
    private readonly double _oldY;
    private readonly double _newX;
    private readonly double _newY;

    public MoveNodeAction(GraphEditorViewModel viewModel, GraphNodeViewModel node,
        double oldX, double oldY, double newX, double newY)
        : base(viewModel)
    {
        _node = node;
        _oldX = oldX;
        _oldY = oldY;
        _newX = newX;
        _newY = newY;
    }

    public override void Execute()
    {
        _node.X = _newX;
        _node.Y = _newY;
        ViewModel.IsDirty = true;
    }

    public override void Undo()
    {
        _node.X = _oldX;
        _node.Y = _oldY;
        ViewModel.IsDirty = true;
    }
}

public class ConnectEdgeAction : GraphAction
{
    private readonly GraphEdgeViewModel _edge;

    public ConnectEdgeAction(GraphEditorViewModel viewModel, GraphEdgeViewModel edge)
        : base(viewModel)
    {
        _edge = edge;
    }

    public override void Execute()
    {
        ViewModel.Edges.Add(_edge);
        ViewModel.IsDirty = true;
    }

    public override void Undo()
    {
        ViewModel.Edges.Remove(_edge);
        if (ViewModel.SelectedEdge?.Id == _edge.Id)
            ViewModel.SelectedEdge = null;
        ViewModel.IsDirty = true;
    }
}

public class DeleteEdgeAction : GraphAction
{
    private readonly GraphEdgeViewModel _edge;

    public DeleteEdgeAction(GraphEditorViewModel viewModel, GraphEdgeViewModel edge)
        : base(viewModel)
    {
        _edge = edge;
    }

    public override void Execute()
    {
        ViewModel.Edges.Remove(_edge);
        if (ViewModel.SelectedEdge?.Id == _edge.Id)
            ViewModel.SelectedEdge = null;
        ViewModel.IsDirty = true;
    }

    public override void Undo()
    {
        ViewModel.Edges.Add(_edge);
        ViewModel.IsDirty = true;
    }
}

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
        if (_undoStack.Count == 0) return;
        var action = _undoStack.Pop();
        action.Undo();
        _redoStack.Push(action);
    }

    public void Redo()
    {
        if (_redoStack.Count == 0) return;
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
