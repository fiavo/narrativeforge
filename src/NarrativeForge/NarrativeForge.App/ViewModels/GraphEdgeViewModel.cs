using CommunityToolkit.Mvvm.ComponentModel;

namespace NarrativeForge.App.ViewModels;

public partial class GraphEdgeViewModel : ObservableObject
{
    [ObservableProperty]
    private Guid _id = Guid.NewGuid();

    [ObservableProperty]
    private Guid _sourceId;

    [ObservableProperty]
    private Guid _targetId;

    [ObservableProperty]
    private string _condition = string.Empty;

    [ObservableProperty]
    private string _edgeColor = "#FF757575";

    public GraphEdgeViewModel() { }

    public GraphEdgeViewModel(Guid id, Guid sourceId, Guid targetId, string condition)
    {
        _id = id;
        _sourceId = sourceId;
        _targetId = targetId;
        _condition = condition;
    }
}
