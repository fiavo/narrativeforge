using System.Windows;
using System.Windows.Controls;
using NarrativeForge.Core.DTOs;
using NarrativeForge.Core.Enums;

namespace NarrativeForge.App.Controls;

public partial class CharacterEditorControl : UserControl
{
    private CharacterDto? _character;
    private bool _isUpdating;

    public static readonly DependencyProperty CharacterProperty =
        DependencyProperty.Register(nameof(Character), typeof(CharacterDto), typeof(CharacterEditorControl),
            new PropertyMetadata(null, OnCharacterChanged));

    public CharacterDto? Character
    {
        get => (CharacterDto?)GetValue(CharacterProperty);
        set => SetValue(CharacterProperty, value);
    }

    public event EventHandler? CharacterUpdated;

    public CharacterEditorControl()
    {
        InitializeComponent();
    }

    private static void OnCharacterChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is CharacterEditorControl control)
            control.BindCharacter();
    }

    private void BindCharacter()
    {
        _character = Character;
        var hasCharacter = _character is not null;

        EmptyState.Visibility = hasCharacter ? Visibility.Collapsed : Visibility.Visible;
        EditorScrollViewer.Visibility = hasCharacter ? Visibility.Visible : Visibility.Collapsed;

        if (_character is null) return;

        _isUpdating = true;

        NameTextBox.Text = _character.Name;
        SyncRoleComboBox();
        TraitsTextBox.Text = string.Join(Environment.NewLine, _character.Personality.Traits);
        BackstoryTextBox.Text = _character.Backstory;
        MotivationTextBox.Text = _character.Motivation;
        GoalsTextBox.Text = string.Join(Environment.NewLine, _character.Goals);
        FearsTextBox.Text = string.Join(Environment.NewLine, _character.Fears);
        DialogueStyleTextBox.Text = _character.DialogueStyle;
        AppearanceTextBox.Text = _character.Appearance;
        IsAliveCheckBox.IsChecked = _character.IsAlive;
        IsLockedCheckBox.IsChecked = _character.IsLocked;

        _isUpdating = false;

        NameTextBox.TextChanged += OnFieldChanged;
        TraitsTextBox.TextChanged += OnFieldChanged;
        BackstoryTextBox.TextChanged += OnFieldChanged;
        MotivationTextBox.TextChanged += OnFieldChanged;
        GoalsTextBox.TextChanged += OnFieldChanged;
        FearsTextBox.TextChanged += OnFieldChanged;
        DialogueStyleTextBox.TextChanged += OnFieldChanged;
        AppearanceTextBox.TextChanged += OnFieldChanged;
        IsAliveCheckBox.Checked += OnFieldChanged;
        IsAliveCheckBox.Unchecked += OnFieldChanged;
        IsLockedCheckBox.Checked += OnFieldChanged;
        IsLockedCheckBox.Unchecked += OnFieldChanged;
    }

    private void SyncRoleComboBox()
    {
        if (_character is null) return;

        for (int i = 0; i < RoleComboBox.Items.Count; i++)
        {
            if (RoleComboBox.Items[i] is ComboBoxItem item &&
                string.Equals(item.Content?.ToString(), _character.Role.ToString(), StringComparison.OrdinalIgnoreCase))
            {
                RoleComboBox.SelectedIndex = i;
                return;
            }
        }

        RoleComboBox.SelectedIndex = 0;
    }

    private void RoleComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_isUpdating || _character is null) return;
        if (RoleComboBox.SelectedItem is ComboBoxItem item && item.Content is string roleStr)
        {
            if (Enum.TryParse<CharacterRole>(roleStr, true, out var role))
            {
                _character.Role = role;
                CharacterUpdated?.Invoke(this, EventArgs.Empty);
            }
        }
    }

    private void OnFieldChanged(object sender, RoutedEventArgs e)
    {
        if (_isUpdating || _character is null) return;

        _character.Name = NameTextBox.Text;
        _character.Personality.Traits = ParseList(TraitsTextBox.Text);
        _character.Backstory = BackstoryTextBox.Text;
        _character.Motivation = MotivationTextBox.Text;
        _character.Goals = ParseList(GoalsTextBox.Text);
        _character.Fears = ParseList(FearsTextBox.Text);
        _character.DialogueStyle = DialogueStyleTextBox.Text;
        _character.Appearance = AppearanceTextBox.Text;
        _character.IsAlive = IsAliveCheckBox.IsChecked == true;
        _character.IsLocked = IsLockedCheckBox.IsChecked == true;

        CharacterUpdated?.Invoke(this, EventArgs.Empty);
    }

    private static List<string> ParseList(string text)
    {
        return [.. text.Split(Environment.NewLine, StringSplitOptions.RemoveEmptyEntries)
                       .Select(l => l.Trim())
                       .Where(l => !string.IsNullOrEmpty(l))];
    }
}
