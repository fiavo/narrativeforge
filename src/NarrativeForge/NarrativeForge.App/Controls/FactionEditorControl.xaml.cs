using System.Windows;
using System.Windows.Controls;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Controls;

public partial class FactionEditorControl : UserControl
{
    private FactionDto? _faction;
    private bool _isUpdating;

    public static readonly DependencyProperty FactionProperty =
        DependencyProperty.Register(nameof(Faction), typeof(FactionDto), typeof(FactionEditorControl),
            new PropertyMetadata(null, OnFactionChanged));

    public FactionDto? Faction
    {
        get => (FactionDto?)GetValue(FactionProperty);
        set => SetValue(FactionProperty, value);
    }

    public event EventHandler? FactionUpdated;

    public FactionEditorControl()
    {
        InitializeComponent();
    }

    private static void OnFactionChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is FactionEditorControl control)
            control.BindFaction();
    }

    private void BindFaction()
    {
        _faction = Faction;
        var hasFaction = _faction is not null;

        EmptyState.Visibility = hasFaction ? Visibility.Collapsed : Visibility.Visible;
        EditorScrollViewer.Visibility = hasFaction ? Visibility.Visible : Visibility.Collapsed;

        if (_faction is null) return;

        _isUpdating = true;

        NameTextBox.Text = _faction.Name;
        DescriptionTextBox.Text = _faction.Description;
        MembersTextBox.Text = string.Join(Environment.NewLine, _faction.MemberIds);
        GoalsTextBox.Text = string.Join(Environment.NewLine, _faction.Goals);
        AlliesTextBox.Text = string.Join(Environment.NewLine, _faction.AllianceIds);
        EnemiesTextBox.Text = string.Join(Environment.NewLine, _faction.EnemyIds);

        _isUpdating = false;

        NameTextBox.TextChanged += OnFieldChanged;
        DescriptionTextBox.TextChanged += OnFieldChanged;
        MembersTextBox.TextChanged += OnFieldChanged;
        GoalsTextBox.TextChanged += OnFieldChanged;
        AlliesTextBox.TextChanged += OnFieldChanged;
        EnemiesTextBox.TextChanged += OnFieldChanged;
    }

    private void OnFieldChanged(object sender, RoutedEventArgs e)
    {
        if (_isUpdating || _faction is null) return;

        _faction.Name = NameTextBox.Text;
        _faction.Description = DescriptionTextBox.Text;
        _faction.MemberIds = ParseGuidList(MembersTextBox.Text);
        _faction.Goals = ParseList(GoalsTextBox.Text);
        _faction.AllianceIds = ParseGuidList(AlliesTextBox.Text);
        _faction.EnemyIds = ParseGuidList(EnemiesTextBox.Text);

        FactionUpdated?.Invoke(this, EventArgs.Empty);
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
