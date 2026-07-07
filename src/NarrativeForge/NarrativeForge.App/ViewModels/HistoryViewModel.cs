using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace NarrativeForge.App.ViewModels;

public partial class HistoryViewModel : ObservableObject
{
    [ObservableProperty]
    private string _statusText = "Ready";

    [ObservableProperty]
    private VersionEntry? _selectedVersion;

    [ObservableProperty]
    private VersionEntry? _compareFromVersion;

    [ObservableProperty]
    private VersionEntry? _compareToVersion;

    public ObservableCollection<VersionEntry> Versions { get; } = [];

    public bool HasSelectedVersion => SelectedVersion is not null;

    public bool CanCompare => CompareFromVersion is not null && CompareToVersion is not null;

    [RelayCommand]
    private void CreateSnapshot()
    {
        var entry = new VersionEntry
        {
            Id = Guid.NewGuid(),
            Label = $"Snapshot {Versions.Count + 1}",
            Timestamp = DateTime.Now,
            Description = "Manual snapshot"
        };
        Versions.Insert(0, entry);
        StatusText = $"Snapshot '{entry.Label}' created.";
    }

    [RelayCommand]
    private void RestoreVersion()
    {
        if (SelectedVersion is null)
        {
            StatusText = "No version selected to restore.";
            return;
        }

        StatusText = $"Restored to '{SelectedVersion.Label}'.";
    }

    [RelayCommand]
    private void CompareVersions()
    {
        if (CompareFromVersion is null || CompareToVersion is null)
        {
            StatusText = "Select two versions to compare.";
            return;
        }

        StatusText = $"Comparing '{CompareFromVersion.Label}' with '{CompareToVersion.Label}'.";
    }

    partial void OnSelectedVersionChanged(VersionEntry? value)
    {
        OnPropertyChanged(nameof(HasSelectedVersion));
    }

    partial void OnCompareFromVersionChanged(VersionEntry? value)
    {
        OnPropertyChanged(nameof(CanCompare));
    }

    partial void OnCompareToVersionChanged(VersionEntry? value)
    {
        OnPropertyChanged(nameof(CanCompare));
    }
}

public class VersionEntry
{
    public Guid Id { get; set; }
    public string Label { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; }
    public string Description { get; set; } = string.Empty;
}
