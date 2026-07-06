using System.Windows;
using System.Windows.Controls;
using NarrativeForge.App.ViewModels;

namespace NarrativeForge.App.Controls;

public partial class PropertyPanel : UserControl
{
    private static readonly string[] ChoiceTypes = ["text", "choice", "condition", "variable", "jump", "end"];
    private static readonly string[] ObjectiveTypes = ["start", "objective", "reward", "fail"];

    public static readonly DependencyProperty SelectedNodeProperty =
        DependencyProperty.Register(nameof(SelectedNode), typeof(GraphNodeViewModel), typeof(PropertyPanel),
            new PropertyMetadata(null, OnSelectedNodeChanged));

    public GraphNodeViewModel? SelectedNode
    {
        get => (GraphNodeViewModel?)GetValue(SelectedNodeProperty);
        set => SetValue(SelectedNodeProperty, value);
    }

    public PropertyPanel()
    {
        InitializeComponent();
        UpdateVisibility();
    }

    private static void OnSelectedNodeChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is PropertyPanel panel)
            panel.UpdateVisibility();
    }

    private void UpdateVisibility()
    {
        var hasNode = SelectedNode is not null;

        EmptyState.Visibility = hasNode ? Visibility.Collapsed : Visibility.Visible;
        PropScrollViewer.Visibility = hasNode ? Visibility.Visible : Visibility.Collapsed;

        if (hasNode)
        {
            SyncNodeTypeComboBox();
            UpdateTypeSpecificSections();
        }
    }

    private void SyncNodeTypeComboBox()
    {
        if (SelectedNode is null) return;

        for (int i = 0; i < NodeTypeComboBox.Items.Count; i++)
        {
            if (NodeTypeComboBox.Items[i] is ComboBoxItem item &&
                string.Equals(item.Content?.ToString(), SelectedNode.NodeType, StringComparison.OrdinalIgnoreCase))
            {
                NodeTypeComboBox.SelectedIndex = i;
                return;
            }
        }

        NodeTypeComboBox.SelectedIndex = 0;
    }

    private void NodeTypeComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (SelectedNode is null) return;
        if (NodeTypeComboBox.SelectedItem is ComboBoxItem item)
        {
            SelectedNode.NodeType = item.Content?.ToString() ?? "text";
            UpdateTypeSpecificSections();
        }
    }

    private void UpdateTypeSpecificSections()
    {
        if (SelectedNode is null) return;

        var type = SelectedNode.NodeType;
        ChoicesSection.Visibility = ChoiceTypes.Contains(type, StringComparer.OrdinalIgnoreCase)
            ? Visibility.Visible : Visibility.Collapsed;
        ObjectivesSection.Visibility = ObjectiveTypes.Contains(type, StringComparer.OrdinalIgnoreCase)
            ? Visibility.Visible : Visibility.Collapsed;
    }

    private void AddChoice_Click(object sender, RoutedEventArgs e)
    {
        SelectedNode?.Choices.Add(new ChoiceViewModel());
    }

    private void AddObjective_Click(object sender, RoutedEventArgs e)
    {
        SelectedNode?.Objectives.Add(new ObjectiveViewModel());
    }
}
