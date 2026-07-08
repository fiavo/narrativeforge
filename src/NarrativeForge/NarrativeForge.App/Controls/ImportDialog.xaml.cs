using System.Windows;
using Microsoft.Win32;
using NarrativeForge.App.ViewModels;

namespace NarrativeForge.App.Controls;

public partial class ImportDialog : Window
{
    public ImportDialog()
    {
        InitializeComponent();
        DataContext = new ImportDialogViewModel();
    }

    private void Browse_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog
        {
            Filter = "JSON files (*.json)|*.json|XML files (*.xml)|*.xml|YAML files (*.yaml;*.yml)|*.yaml;*.yml|All files (*.*)|*.*",
            Title = "Select file to import"
        };

        if (dialog.ShowDialog() == true)
        {
            var vm = (ImportDialogViewModel)DataContext;
            vm.LoadFile(dialog.FileName);
        }
    }
}
