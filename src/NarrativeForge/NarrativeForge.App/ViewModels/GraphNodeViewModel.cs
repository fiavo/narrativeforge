using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;

namespace NarrativeForge.App.ViewModels;

public partial class GraphNodeViewModel : ObservableObject
{
    [ObservableProperty]
    private Guid _id = Guid.NewGuid();

    [ObservableProperty]
    private string _nodeType = string.Empty;

    [ObservableProperty]
    private string _title = string.Empty;

    [ObservableProperty]
    private string _content = string.Empty;

    [ObservableProperty]
    private double _x;

    [ObservableProperty]
    private double _y;

    [ObservableProperty]
    private bool _isSelected;

    [ObservableProperty]
    private string _headerColor = "#FF4CAF50";

    public ObservableCollection<ChoiceViewModel> Choices { get; } = [];

    public ObservableCollection<ObjectiveViewModel> Objectives { get; } = [];

    public GraphNodeViewModel() { }

    public GraphNodeViewModel(Guid id, string nodeType, string title, string content, double x, double y)
    {
        _id = id;
        _nodeType = nodeType;
        _title = title;
        _content = content;
        _x = x;
        _y = y;
    }
}
