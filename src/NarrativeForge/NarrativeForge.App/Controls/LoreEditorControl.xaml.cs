using System.Windows;
using System.Windows.Controls;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Controls;

public partial class LoreEditorControl : UserControl
{
    private LoreEntryDto? _lore;
    private bool _isUpdating;

    public static readonly DependencyProperty LoreProperty =
        DependencyProperty.Register(nameof(Lore), typeof(LoreEntryDto), typeof(LoreEditorControl),
            new PropertyMetadata(null, OnLoreChanged));

    public LoreEntryDto? Lore
    {
        get => (LoreEntryDto?)GetValue(LoreProperty);
        set => SetValue(LoreProperty, value);
    }

    public event EventHandler? LoreUpdated;

    public LoreEditorControl()
    {
        InitializeComponent();
    }

    private static void OnLoreChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is LoreEditorControl control)
            control.BindLore();
    }

    private void BindLore()
    {
        _lore = Lore;
        var hasLore = _lore is not null;

        EmptyState.Visibility = hasLore ? Visibility.Collapsed : Visibility.Visible;
        EditorScrollViewer.Visibility = hasLore ? Visibility.Visible : Visibility.Collapsed;

        if (_lore is null) return;

        _isUpdating = true;

        TitleTextBox.Text = _lore.Title;
        ContentTextBox.Text = _lore.Content;
        SyncCategoryComboBox();
        SourceTextBox.Text = _lore.Source;
        RelatedEntriesTextBox.Text = string.Join(Environment.NewLine, _lore.RelatedEntityIds);

        _isUpdating = false;

        TitleTextBox.TextChanged += OnFieldChanged;
        ContentTextBox.TextChanged += OnFieldChanged;
        SourceTextBox.TextChanged += OnFieldChanged;
        RelatedEntriesTextBox.TextChanged += OnFieldChanged;
    }

    private void SyncCategoryComboBox()
    {
        if (_lore is null) return;

        for (int i = 0; i < CategoryComboBox.Items.Count; i++)
        {
            if (CategoryComboBox.Items[i] is ComboBoxItem item &&
                string.Equals(item.Content?.ToString(), _lore.Category, StringComparison.OrdinalIgnoreCase))
            {
                CategoryComboBox.SelectedIndex = i;
                return;
            }
        }

        CategoryComboBox.SelectedIndex = 0;
    }

    private void CategoryComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_isUpdating || _lore is null) return;
        if (CategoryComboBox.SelectedItem is ComboBoxItem item && item.Content is string categoryStr)
        {
            _lore.Category = categoryStr;
            LoreUpdated?.Invoke(this, EventArgs.Empty);
        }
    }

    private void OnFieldChanged(object sender, RoutedEventArgs e)
    {
        if (_isUpdating || _lore is null) return;

        _lore.Title = TitleTextBox.Text;
        _lore.Content = ContentTextBox.Text;
        _lore.Source = SourceTextBox.Text;
        _lore.RelatedEntityIds = ParseGuidList(RelatedEntriesTextBox.Text);

        LoreUpdated?.Invoke(this, EventArgs.Empty);
    }

    private static List<string> ParseList(string text)
    {
        return [.. text.Split(Environment.NewLine, StringSplitOptions.RemoveEmptyEntries)
                       .Select(l => l.Trim())
                       .Where(l => !string.IsNullOrEmpty(l))];
    }

    private static List<Guid> ParseGuidList(string text)
    {
        return [.. text.Split(Environment.NewLine, StringSplitOptions.RemoveEmptyEntries)
                       .Select(l => l.Trim())
                       .Where(l => !string.IsNullOrEmpty(l))
                       .Where(l => Guid.TryParse(l, out _))
                       .Select(l => Guid.Parse(l))];
    }
}
