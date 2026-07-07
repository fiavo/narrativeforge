using System.Collections.ObjectModel;
using System.Windows;
using System.Windows.Controls;
using NarrativeForge.App.ViewModels;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Controls;

public partial class RelationshipPanel : UserControl
{
    private CharacterDto? _selectedCharacter;
    private List<CharacterDto> _allCharacters = [];

    public static readonly DependencyProperty SelectedCharacterProperty =
        DependencyProperty.Register(nameof(SelectedCharacter), typeof(CharacterDto), typeof(RelationshipPanel),
            new PropertyMetadata(null, OnSelectedCharacterChanged));

    public static readonly DependencyProperty CharactersProperty =
        DependencyProperty.Register(nameof(Characters), typeof(ObservableCollection<CharacterDto>), typeof(RelationshipPanel),
            new PropertyMetadata(null, OnCharactersChanged));

    public CharacterDto? SelectedCharacter
    {
        get => (CharacterDto?)GetValue(SelectedCharacterProperty);
        set => SetValue(SelectedCharacterProperty, value);
    }

    public ObservableCollection<CharacterDto>? Characters
    {
        get => (ObservableCollection<CharacterDto>?)GetValue(CharactersProperty);
        set => SetValue(CharactersProperty, value);
    }

    public event EventHandler? RelationshipAdded;

    public ObservableCollection<RelationshipDisplayItem> DisplayItems { get; } = [];
    public ObservableCollection<GraphNodeViewModel> MiniNodes { get; } = [];
    public ObservableCollection<GraphEdgeViewModel> MiniEdges { get; } = [];

    public RelationshipPanel()
    {
        DataContext = this;
        InitializeComponent();
    }

    private static void OnSelectedCharacterChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is RelationshipPanel panel)
            panel.RefreshView();
    }

    private static void OnCharactersChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is RelationshipPanel panel)
        {
            if (e.OldValue is ObservableCollection<CharacterDto> oldChars)
                oldChars.CollectionChanged -= panel.OnCharactersCollectionChanged;
            if (e.NewValue is ObservableCollection<CharacterDto> newChars)
            {
                newChars.CollectionChanged += panel.OnCharactersCollectionChanged;
                panel._allCharacters = [.. newChars];
            }
        }
    }

    private void OnCharactersCollectionChanged(object? sender, System.Collections.Specialized.NotifyCollectionChangedEventArgs e)
    {
        if (Characters is not null)
            _allCharacters = [.. Characters];
        RefreshView();
    }

    private void RefreshView()
    {
        _selectedCharacter = SelectedCharacter;
        var hasCharacter = _selectedCharacter is not null;

        EmptyState.Visibility = hasCharacter ? Visibility.Collapsed : Visibility.Visible;
        ContentPanel.Visibility = hasCharacter ? Visibility.Visible : Visibility.Collapsed;
        AddDialog.Visibility = Visibility.Collapsed;

        DisplayItems.Clear();
        MiniNodes.Clear();
        MiniEdges.Clear();

        if (_selectedCharacter is null) return;

        // Add the selected character as the center node
        var centerNode = new GraphNodeViewModel
        {
            Id = _selectedCharacter.Id,
            Title = _selectedCharacter.Name,
            NodeType = "character",
            X = 120,
            Y = 60,
            HeaderColor = "#FF4CAF50"
        };
        MiniNodes.Add(centerNode);

        // Build list of related characters and mini graph
        if (_selectedCharacter.Relationships is { Count: > 0 })
        {
            int index = 0;
            foreach (var kvp in _selectedCharacter.Relationships)
            {
                var targetId = kvp.Key;
                var relType = kvp.Value;
                var targetChar = _allCharacters.FirstOrDefault(c => c.Id == targetId);
                if (targetChar is null) continue;

                DisplayItems.Add(new RelationshipDisplayItem
                {
                    EntityId = targetId,
                    EntityName = targetChar.Name,
                    RelationshipType = relType
                });

                // Position nodes in a circle around the center
                var angle = (2 * Math.PI * index) / _selectedCharacter.Relationships.Count;
                var radius = 60.0;
                var nodeX = 120 + radius * Math.Cos(angle) - 40;
                var nodeY = 60 + radius * Math.Sin(angle) - 20;

                var relNode = new GraphNodeViewModel
                {
                    Id = targetId,
                    Title = targetChar.Name,
                    NodeType = "character",
                    X = nodeX,
                    Y = nodeY,
                    HeaderColor = GetRelationshipColor(relType)
                };
                MiniNodes.Add(relNode);

                MiniEdges.Add(new GraphEdgeViewModel
                {
                    SourceId = _selectedCharacter.Id,
                    TargetId = targetId,
                    Condition = relType,
                    EdgeColor = GetRelationshipColor(relType)
                });

                index++;
            }
        }

        RelationshipItemsControl.ItemsSource = DisplayItems;
    }

    private static string GetRelationshipColor(string relType)
    {
        return relType.ToLowerInvariant() switch
        {
            "friend" or "ally" or "mentor" or "student" or "family" or "romantic" => "#FF4CAF50",
            "rival" or "enemy" or "follower" => "#FFEF5350",
            "leader" => "#FFFFA726",
            _ => "#FF757575"
        };
    }

    private void AddRelationship_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedCharacter is null || Characters is null) return;

        AddDialog.Visibility = Visibility.Visible;

        TargetCharacterComboBox.Items.Clear();
        foreach (var c in Characters.Where(c => c.Id != _selectedCharacter.Id))
        {
            TargetCharacterComboBox.Items.Add(new ComboBoxItem
            {
                Content = c.Name,
                Tag = c.Id
            });
        }

        if (TargetCharacterComboBox.Items.Count > 0)
            TargetCharacterComboBox.SelectedIndex = 0;

        RelationshipTypeComboBox.SelectedIndex = 0;
        CustomTypeLabel.Visibility = Visibility.Collapsed;
        CustomTypeTextBox.Visibility = Visibility.Collapsed;
    }

    private void ConfirmAddRelationship_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedCharacter is null || TargetCharacterComboBox.SelectedItem is not ComboBoxItem targetItem)
            return;

        var targetId = (Guid)targetItem.Tag!;

        var relType = RelationshipTypeComboBox.SelectedItem is ComboBoxItem relItem
            ? relItem.Content?.ToString() ?? "Neutral"
            : "Neutral";

        if (relType == "Custom")
            relType = string.IsNullOrWhiteSpace(CustomTypeTextBox.Text) ? "Custom" : CustomTypeTextBox.Text;

        // Add to the selected character's relationships
        _selectedCharacter.Relationships[targetId] = relType;

        // Add reverse relationship to the target character
        var targetChar = _allCharacters.FirstOrDefault(c => c.Id == targetId);
        if (targetChar is not null)
        {
            targetChar.Relationships[_selectedCharacter.Id] = relType;
        }

        AddDialog.Visibility = Visibility.Collapsed;

        RelationshipAdded?.Invoke(this, EventArgs.Empty);
        RefreshView();
    }

    private void CancelAddRelationship_Click(object sender, RoutedEventArgs e)
    {
        AddDialog.Visibility = Visibility.Collapsed;
    }

    private void RemoveRelationship_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedCharacter is null || sender is not Button button || button.Tag is not Guid targetId)
            return;

        _selectedCharacter.Relationships.Remove(targetId);

        var targetChar = _allCharacters.FirstOrDefault(c => c.Id == targetId);
        if (targetChar is not null)
            targetChar.Relationships.Remove(_selectedCharacter.Id);

        RelationshipAdded?.Invoke(this, EventArgs.Empty);
        RefreshView();
    }
}

public class RelationshipDisplayItem
{
    public Guid EntityId { get; set; }
    public string EntityName { get; set; } = string.Empty;
    public string RelationshipType { get; set; } = string.Empty;
}
