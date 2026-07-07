using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using NarrativeForge.App.Export;

namespace NarrativeForge.App.ViewModels;

public partial class ExportDialogViewModel : ObservableObject
{
    private readonly ExportManager _exportManager;
    private ExportResult? _currentResult;

    public event Action? RequestClose;

    [ObservableProperty]
    private IExporter? _selectedExporter;

    [ObservableProperty]
    private string _previewContent = string.Empty;

    [ObservableProperty]
    private bool _isExporting;

    [ObservableProperty]
    private string _statusMessage = string.Empty;

    public ObservableCollection<IExporter> Exporters { get; } = [];

    public ExportRequest Request { get; set; } = new();

    public ExportDialogViewModel(ExportManager exportManager)
    {
        _exportManager = exportManager;
        LoadExporters();
    }

    private void LoadExporters()
    {
        Exporters.Clear();
        foreach (var exporter in _exportManager.GetExporters())
            Exporters.Add(exporter);

        if (Exporters.Count > 0)
            SelectedExporter = Exporters[0];
    }

    partial void OnSelectedExporterChanged(IExporter? value)
    {
        if (value is not null)
            _ = GeneratePreviewAsync(value);
    }

    private async Task GeneratePreviewAsync(IExporter exporter)
    {
        IsExporting = true;
        StatusMessage = "Generating preview...";

        try
        {
            var result = await _exportManager.ExportAsync(exporter, Request);
            if (result.Success)
            {
                _currentResult = result;
                PreviewContent = result.Content;
                StatusMessage = $"Preview ready — {result.Content.Length:N0} characters";
            }
            else
            {
                _currentResult = null;
                PreviewContent = string.Empty;
                StatusMessage = $"Error: {result.Error}";
            }
        }
        catch (Exception ex)
        {
            _currentResult = null;
            PreviewContent = string.Empty;
            StatusMessage = $"Preview failed: {ex.Message}";
        }
        finally
        {
            IsExporting = false;
        }
    }

    [RelayCommand]
    private void Cancel()
    {
        RequestClose?.Invoke();
    }

    [RelayCommand]
    private void CopyToClipboard()
    {
        if (_currentResult?.Success == true && !string.IsNullOrEmpty(_currentResult.Content))
        {
            System.Windows.Clipboard.SetText(_currentResult.Content);
            StatusMessage = "Copied to clipboard.";
        }
    }

    [RelayCommand]
    private void SaveToFile(Microsoft.Win32.SaveFileDialog saveFileDialog)
    {
        if (_currentResult?.Success != true) return;

        var filename = string.IsNullOrEmpty(_currentResult.Filename)
            ? $"export{SelectedExporter?.FileExtension}"
            : _currentResult.Filename;

        saveFileDialog.FileName = filename;
        saveFileDialog.Filter = $"{SelectedExporter?.Name} files (*{SelectedExporter?.FileExtension})|*{SelectedExporter?.FileExtension}|All files (*.*)|*.*";

        if (saveFileDialog.ShowDialog() == true)
        {
            System.IO.File.WriteAllText(saveFileDialog.FileName, _currentResult.Content);
            StatusMessage = $"Saved to {saveFileDialog.FileName}";
        }
    }
}
