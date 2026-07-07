using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using NarrativeForge.App.ViewModels;

namespace NarrativeForge.App.Controls;

public partial class HistoryPanel : UserControl
{
    private VersionEntry? _selectedVersion;
    private VersionEntry? _compareFrom;
    private VersionEntry? _compareTo;

    public static readonly DependencyProperty ViewModelProperty =
        DependencyProperty.Register(nameof(ViewModel), typeof(HistoryViewModel), typeof(HistoryPanel),
            new PropertyMetadata(null));

    public HistoryViewModel? ViewModel
    {
        get => (HistoryViewModel?)GetValue(ViewModelProperty);
        set => SetValue(ViewModelProperty, value);
    }

    public HistoryPanel()
    {
        DataContext = ViewModel = new HistoryViewModel();
        InitializeComponent();
        ViewModel.Versions.CollectionChanged += (_, _) =>
        {
            EmptyState.Visibility = ViewModel.Versions.Count == 0
                ? Visibility.Visible
                : Visibility.Collapsed;
        };
    }

    private void CreateSnapshot_Click(object sender, RoutedEventArgs e)
    {
        ViewModel?.CreateSnapshotCommand.Execute(null);
        RefreshButtons();
    }

    private void Restore_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedVersion is not null)
        {
            ViewModel?.RestoreVersionCommand.Execute(null);
            StatusTextBlock.Text = $"Restored to '{_selectedVersion.Label}'.";
        }
    }

    private void Compare_Click(object sender, RoutedEventArgs e)
    {
        if (_compareFrom is not null && _compareTo is not null)
        {
            ViewModel?.CompareVersionsCommand.Execute(null);
            StatusTextBlock.Text = $"Comparing '{_compareFrom.Label}' with '{_compareTo.Label}'.";
        }
    }

    private void VersionCard_Click(object sender, MouseButtonEventArgs e)
    {
        if (sender is FrameworkElement fe && fe.Tag is VersionEntry entry)
        {
            _selectedVersion = entry;
            ViewModel!.SelectedVersion = entry;
            StatusTextBlock.Text = $"Selected: {entry.Label}";
            RefreshButtons();
        }
    }

    private void FromCheck_Changed(object sender, RoutedEventArgs e)
    {
        if (sender is CheckBox cb && cb.DataContext is VersionEntry entry)
        {
            _compareFrom = cb.IsChecked == true ? entry : null;
            ViewModel!.CompareFromVersion = _compareFrom;
            RefreshButtons();
        }
    }

    private void ToCheck_Changed(object sender, RoutedEventArgs e)
    {
        if (sender is CheckBox cb && cb.DataContext is VersionEntry entry)
        {
            _compareTo = cb.IsChecked == true ? entry : null;
            ViewModel!.CompareToVersion = _compareTo;
            RefreshButtons();
        }
    }

    private void RefreshButtons()
    {
        RestoreButton.IsEnabled = _selectedVersion is not null;
        CompareButton.IsEnabled = _compareFrom is not null && _compareTo is not null;
    }
}
