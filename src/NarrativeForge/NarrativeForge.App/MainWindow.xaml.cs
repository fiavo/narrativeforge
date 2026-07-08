using System.Windows;
using NarrativeForge.App.Controls;

namespace NarrativeForge.App;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        EditorGraphCanvas.FileDropped += OnGraphCanvasFileDropped;
    }

    private async void OnGraphCanvasFileDropped(object? sender, FileDroppedEventArgs e)
    {
        if (DataContext is not ViewModels.MainViewModel vm) return;
        if (vm.SelectedProject is null)
        {
            vm.StatusText = "Select a project before importing a file.";
            return;
        }

        vm.IsBusy = true;
        vm.StatusText = $"Importing {System.IO.Path.GetFileName(e.FilePath)}...";

        try
        {
            var request = new NarrativeForge.Core.DTOs.ImportRequestDto
            {
                Filename = System.IO.Path.GetFileName(e.FilePath),
                Content = e.Content,
                Format = e.Format
            };

            var result = await vm.ImportFileAsync(vm.SelectedProject.Id, request);
            if (result is null)
            {
                vm.StatusText = "Import failed.";
                return;
            }

            vm.GraphEditorViewModel.LoadFromDialogueTree(new NarrativeForge.Core.DTOs.DialogueTreeDto
            {
                Id = result.TreeId,
                Name = result.Name,
                Nodes = result.Nodes,
                Edges = result.Edges
            });
            vm.ShowGraphEditor = true;
            vm.StatusText = $"Imported '{result.Name}' with {result.Nodes.Count} nodes.";
        }
        catch (Exception ex)
        {
            vm.StatusText = $"Import error: {ex.Message}";
        }
        finally
        {
            vm.IsBusy = false;
        }
    }

    private void MenuItem_Import_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new ImportDialog { Owner = this };
        dialog.ShowDialog();
    }

    private void MenuItem_Exit_Click(object sender, RoutedEventArgs e)
    {
        Application.Current.Shutdown();
    }

    private void ViewHistory_Click(object sender, RoutedEventArgs e)
    {
        HistoryTab.IsSelected = true;
    }
}
