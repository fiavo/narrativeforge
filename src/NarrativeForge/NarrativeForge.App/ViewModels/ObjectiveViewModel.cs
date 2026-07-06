using CommunityToolkit.Mvvm.ComponentModel;

namespace NarrativeForge.App.ViewModels;

public partial class ObjectiveViewModel : ObservableObject
{
    [ObservableProperty]
    private Guid _id = Guid.NewGuid();

    [ObservableProperty]
    private string _description = string.Empty;

    [ObservableProperty]
    private string _type = string.Empty;

    [ObservableProperty]
    private string _target = string.Empty;

    public ObjectiveViewModel() { }

    public ObjectiveViewModel(Guid id, string description, string type, string target)
    {
        _id = id;
        _description = description;
        _type = type;
        _target = target;
    }
}
