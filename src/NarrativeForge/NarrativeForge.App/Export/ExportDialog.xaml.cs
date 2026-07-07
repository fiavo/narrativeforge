using System.Windows;
using Microsoft.Win32;
using NarrativeForge.App.Export;
using NarrativeForge.App.ViewModels;

namespace NarrativeForge.App.Export;

public partial class ExportDialog : Window
{
    private readonly ExportDialogViewModel _viewModel;

    public ExportDialog(ExportManager exportManager, ExportRequest? request = null)
    {
        InitializeComponent();

        _viewModel = new ExportDialogViewModel(exportManager);
        if (request is not null)
            _viewModel.Request = request;

        _viewModel.RequestClose += () => DialogResult = false;
        DataContext = _viewModel;
    }

    private void SaveToFile_Click(object sender, RoutedEventArgs e)
    {
        var saveFileDialog = new SaveFileDialog();
        _viewModel.SaveToFileCommand.Execute(saveFileDialog);
    }
}
