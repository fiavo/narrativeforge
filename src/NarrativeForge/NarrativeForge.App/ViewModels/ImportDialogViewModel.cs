using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace NarrativeForge.App.ViewModels;

public partial class ImportDialogViewModel : ObservableObject
{
    public event Action? RequestClose;
    public event Action<string, string>? ImportRequested;

    [ObservableProperty]
    private string _selectedFilePath = string.Empty;

    [ObservableProperty]
    private string? _selectedFormat;

    [ObservableProperty]
    private string _previewContent = string.Empty;

    [ObservableProperty]
    private bool _isFileLoaded;

    [ObservableProperty]
    private string _statusMessage = string.Empty;

    [ObservableProperty]
    private string _fileSizeDisplay = string.Empty;

    public ObservableCollection<string> AvailableFormats { get; } =
    [
        "JSON",
        "XML",
        "YAML",
        "Ink",
        "Twine HTML"
    ];

    public string? LoadedContent { get; private set; }

    [RelayCommand]
    private void Cancel()
    {
        RequestClose?.Invoke();
    }

    [RelayCommand]
    private void Import()
    {
        if (!IsFileLoaded || string.IsNullOrEmpty(SelectedFilePath) || string.IsNullOrEmpty(LoadedContent))
            return;

        ImportRequested?.Invoke(SelectedFilePath, LoadedContent);
    }

    public void LoadFile(string filePath)
    {
        try
        {
            SelectedFilePath = filePath;
            LoadedContent = System.IO.File.ReadAllText(filePath);

            var fileInfo = new System.IO.FileInfo(filePath);
            FileSizeDisplay = fileInfo.Length > 1024 * 1024
                ? $"{fileInfo.Length / (1024.0 * 1024.0):F1} MB"
                : $"{fileInfo.Length / 1024.0:F1} KB";

            AutoDetectFormat(filePath);
            GeneratePreview();
            IsFileLoaded = true;
            StatusMessage = $"Loaded {fileInfo.Name}";
        }
        catch (Exception ex)
        {
            IsFileLoaded = false;
            PreviewContent = string.Empty;
            StatusMessage = $"Error loading file: {ex.Message}";
        }
    }

    private void AutoDetectFormat(string filePath)
    {
        var ext = System.IO.Path.GetExtension(filePath).ToLowerInvariant();
        SelectedFormat = ext switch
        {
            ".json" => "JSON",
            ".xml" => "XML",
            ".yaml" or ".yml" => "YAML",
            ".ink" => "Ink",
            ".html" or ".htm" => "Twine HTML",
            _ => AvailableFormats.FirstOrDefault()
        };
    }

    private void GeneratePreview()
    {
        if (string.IsNullOrEmpty(LoadedContent))
        {
            PreviewContent = string.Empty;
            return;
        }

        var lines = LoadedContent.Split('\n');
        var previewLines = lines.Take(50);
        PreviewContent = string.Join('\n', previewLines);

        if (lines.Length > 50)
            PreviewContent += $"\n\n... ({lines.Length - 50} more lines)";
    }
}
