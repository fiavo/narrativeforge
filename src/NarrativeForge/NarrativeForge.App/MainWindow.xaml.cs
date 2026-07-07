using System.Windows;

namespace NarrativeForge.App;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
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
