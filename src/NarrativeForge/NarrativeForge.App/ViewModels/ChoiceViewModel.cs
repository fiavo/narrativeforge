using CommunityToolkit.Mvvm.ComponentModel;

namespace NarrativeForge.App.ViewModels;

public partial class ChoiceViewModel : ObservableObject
{
    [ObservableProperty]
    private Guid _id = Guid.NewGuid();

    [ObservableProperty]
    private string _text = string.Empty;

    [ObservableProperty]
    private Guid _nextNodeId;

    [ObservableProperty]
    private string _condition = string.Empty;

    public ChoiceViewModel() { }

    public ChoiceViewModel(Guid id, string text, Guid nextNodeId, string condition)
    {
        _id = id;
        _text = text;
        _nextNodeId = nextNodeId;
        _condition = condition;
    }
}
