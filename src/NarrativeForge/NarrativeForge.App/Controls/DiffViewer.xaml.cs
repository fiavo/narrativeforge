using System.Collections.ObjectModel;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Controls;

public partial class DiffViewer : UserControl
{
    public ObservableCollection<DiffGroup> DiffGroups { get; } = [];

    public event EventHandler<EventArgs>? RestoreRequested;

    public DiffViewer()
    {
        InitializeComponent();
        DataContext = this;
    }

    public void Compare(StoryBibleDto? from, StoryBibleDto? to)
    {
        DiffGroups.Clear();
        EmptyState.Visibility = Visibility.Visible;

        if (from is null || to is null)
        {
            UpdateStats(0, 0, 0);
            StatusTextBlock.Text = "Both versions must be provided to compare.";
            return;
        }

        EmptyState.Visibility = Visibility.Collapsed;

        CompareCharacterGroups(from, to);
        CompareLocationGroups(from, to);
        CompareFactionGroups(from, to);
        CompareTimelineGroups(from, to);
        CompareLoreGroups(from, to);

        int added = 0, removed = 0, modified = 0;
        foreach (var group in DiffGroups)
        {
            foreach (var change in group.Changes)
            {
                switch (change.Type)
                {
                    case ChangeType.Added: added++; break;
                    case ChangeType.Removed: removed++; break;
                    case ChangeType.Modified: modified++; break;
                }
            }
        }

        UpdateStats(added, removed, modified);
        StatusTextBlock.Text = $"Comparing '{from.ProjectId}' with '{to.ProjectId}'. {DiffGroups.Count} entity types affected.";
        RestoreButton.IsEnabled = DiffGroups.Count > 0;
    }

    private void CompareCharacterGroups(StoryBibleDto from, StoryBibleDto to)
    {
        var changes = new ObservableCollection<DiffItem>();
        var fromDict = from.Characters.ToDictionary(c => c.Id);
        var toDict = to.Characters.ToDictionary(c => c.Id);

        foreach (var kvp in toDict)
        {
            if (!fromDict.TryGetValue(kvp.Key, out var oldChar))
            {
                changes.Add(new DiffItem(ChangeType.Added, "New Character", "", kvp.Value.Name));
            }
            else
            {
                var diffs = DiffCharacter(oldChar, kvp.Value);
                foreach (var d in diffs) changes.Add(d);
            }
        }

        foreach (var kvp in fromDict)
        {
            if (!toDict.ContainsKey(kvp.Key))
            {
                changes.Add(new DiffItem(ChangeType.Removed, "Removed Character", kvp.Value.Name, ""));
            }
        }

        if (changes.Count > 0)
        {
            DiffGroups.Add(new DiffGroup("Characters", changes));
        }
    }

    private List<DiffItem> DiffCharacter(CharacterDto from, CharacterDto to)
    {
        var items = new List<DiffItem>();
        if (from.Name != to.Name)
            items.Add(new DiffItem(ChangeType.Modified, "Name", from.Name, to.Name));
        if (from.Alias != to.Alias)
            items.Add(new DiffItem(ChangeType.Modified, "Alias", from.Alias, to.Alias));
        if (from.Role != to.Role)
            items.Add(new DiffItem(ChangeType.Modified, "Role", from.Role.ToString(), to.Role.ToString()));
        if (from.Backstory != to.Backstory)
            items.Add(new DiffItem(ChangeType.Modified, "Backstory", Truncate(from.Backstory), Truncate(to.Backstory)));
        if (from.Motivation != to.Motivation)
            items.Add(new DiffItem(ChangeType.Modified, "Motivation", Truncate(from.Motivation), Truncate(to.Motivation)));
        if (from.Appearance != to.Appearance)
            items.Add(new DiffItem(ChangeType.Modified, "Appearance", Truncate(from.Appearance), Truncate(to.Appearance)));
        if (from.DialogueStyle != to.DialogueStyle)
            items.Add(new DiffItem(ChangeType.Modified, "DialogueStyle", Truncate(from.DialogueStyle), Truncate(to.DialogueStyle)));
        if (from.IsAlive != to.IsAlive)
            items.Add(new DiffItem(ChangeType.Modified, "IsAlive", from.IsAlive.ToString(), to.IsAlive.ToString()));
        return items;
    }

    private void CompareLocationGroups(StoryBibleDto from, StoryBibleDto to)
    {
        var changes = new ObservableCollection<DiffItem>();
        var fromDict = from.Locations.ToDictionary(l => l.Id);
        var toDict = to.Locations.ToDictionary(l => l.Id);

        foreach (var kvp in toDict)
        {
            if (!fromDict.TryGetValue(kvp.Key, out var oldLoc))
            {
                changes.Add(new DiffItem(ChangeType.Added, "New Location", "", kvp.Value.Name));
            }
            else
            {
                if (oldLoc.Name != kvp.Value.Name)
                    changes.Add(new DiffItem(ChangeType.Modified, "Name", oldLoc.Name, kvp.Value.Name));
                if (oldLoc.Description != kvp.Value.Description)
                    changes.Add(new DiffItem(ChangeType.Modified, "Description", Truncate(oldLoc.Description), Truncate(kvp.Value.Description)));
                if (oldLoc.Type != kvp.Value.Type)
                    changes.Add(new DiffItem(ChangeType.Modified, "Type", oldLoc.Type, kvp.Value.Type));
                if (oldLoc.Climate != kvp.Value.Climate)
                    changes.Add(new DiffItem(ChangeType.Modified, "Climate", oldLoc.Climate, kvp.Value.Climate));
            }
        }

        foreach (var kvp in fromDict)
        {
            if (!toDict.ContainsKey(kvp.Key))
            {
                changes.Add(new DiffItem(ChangeType.Removed, "Removed Location", kvp.Value.Name, ""));
            }
        }

        if (changes.Count > 0)
        {
            DiffGroups.Add(new DiffGroup("Locations", changes));
        }
    }

    private void CompareFactionGroups(StoryBibleDto from, StoryBibleDto to)
    {
        var changes = new ObservableCollection<DiffItem>();
        var fromDict = from.Factions.ToDictionary(f => f.Id);
        var toDict = to.Factions.ToDictionary(f => f.Id);

        foreach (var kvp in toDict)
        {
            if (!fromDict.TryGetValue(kvp.Key, out var oldFac))
            {
                changes.Add(new DiffItem(ChangeType.Added, "New Faction", "", kvp.Value.Name));
            }
            else
            {
                if (oldFac.Name != kvp.Value.Name)
                    changes.Add(new DiffItem(ChangeType.Modified, "Name", oldFac.Name, kvp.Value.Name));
                if (oldFac.Description != kvp.Value.Description)
                    changes.Add(new DiffItem(ChangeType.Modified, "Description", Truncate(oldFac.Description), Truncate(kvp.Value.Description)));
                if (oldFac.Leader != kvp.Value.Leader)
                    changes.Add(new DiffItem(ChangeType.Modified, "Leader", oldFac.Leader, kvp.Value.Leader));
                if (oldFac.Territory != kvp.Value.Territory)
                    changes.Add(new DiffItem(ChangeType.Modified, "Territory", oldFac.Territory, kvp.Value.Territory));
            }
        }

        foreach (var kvp in fromDict)
        {
            if (!toDict.ContainsKey(kvp.Key))
            {
                changes.Add(new DiffItem(ChangeType.Removed, "Removed Faction", kvp.Value.Name, ""));
            }
        }

        if (changes.Count > 0)
        {
            DiffGroups.Add(new DiffGroup("Factions", changes));
        }
    }

    private void CompareTimelineGroups(StoryBibleDto from, StoryBibleDto to)
    {
        var changes = new ObservableCollection<DiffItem>();
        var fromDict = from.TimelineEvents.ToDictionary(e => e.Id);
        var toDict = to.TimelineEvents.ToDictionary(e => e.Id);

        foreach (var kvp in toDict)
        {
            if (!fromDict.TryGetValue(kvp.Key, out var oldEvt))
            {
                changes.Add(new DiffItem(ChangeType.Added, "New Event", "", kvp.Value.Name));
            }
            else
            {
                if (oldEvt.Name != kvp.Value.Name)
                    changes.Add(new DiffItem(ChangeType.Modified, "Name", oldEvt.Name, kvp.Value.Name));
                if (oldEvt.Description != kvp.Value.Description)
                    changes.Add(new DiffItem(ChangeType.Modified, "Description", Truncate(oldEvt.Description), Truncate(kvp.Value.Description)));
                if (oldEvt.Date != kvp.Value.Date)
                    changes.Add(new DiffItem(ChangeType.Modified, "Date", oldEvt.Date, kvp.Value.Date));
                if (oldEvt.Importance != kvp.Value.Importance)
                    changes.Add(new DiffItem(ChangeType.Modified, "Importance", oldEvt.Importance.ToString(), kvp.Value.Importance.ToString()));
            }
        }

        foreach (var kvp in fromDict)
        {
            if (!toDict.ContainsKey(kvp.Key))
            {
                changes.Add(new DiffItem(ChangeType.Removed, "Removed Event", kvp.Value.Name, ""));
            }
        }

        if (changes.Count > 0)
        {
            DiffGroups.Add(new DiffGroup("Timeline Events", changes));
        }
    }

    private void CompareLoreGroups(StoryBibleDto from, StoryBibleDto to)
    {
        var changes = new ObservableCollection<DiffItem>();
        var fromDict = from.LoreEntries.ToDictionary(l => l.Id);
        var toDict = to.LoreEntries.ToDictionary(l => l.Id);

        foreach (var kvp in toDict)
        {
            if (!fromDict.TryGetValue(kvp.Key, out var oldEntry))
            {
                changes.Add(new DiffItem(ChangeType.Added, "New Lore Entry", "", kvp.Value.Title));
            }
            else
            {
                if (oldEntry.Title != kvp.Value.Title)
                    changes.Add(new DiffItem(ChangeType.Modified, "Title", oldEntry.Title, kvp.Value.Title));
                if (oldEntry.Content != kvp.Value.Content)
                    changes.Add(new DiffItem(ChangeType.Modified, "Content", Truncate(oldEntry.Content), Truncate(kvp.Value.Content)));
                if (oldEntry.Category != kvp.Value.Category)
                    changes.Add(new DiffItem(ChangeType.Modified, "Category", oldEntry.Category, kvp.Value.Category));
                if (oldEntry.Source != kvp.Value.Source)
                    changes.Add(new DiffItem(ChangeType.Modified, "Source", oldEntry.Source, kvp.Value.Source));
            }
        }

        foreach (var kvp in fromDict)
        {
            if (!toDict.ContainsKey(kvp.Key))
            {
                changes.Add(new DiffItem(ChangeType.Removed, "Removed Lore Entry", kvp.Value.Title, ""));
            }
        }

        if (changes.Count > 0)
        {
            DiffGroups.Add(new DiffGroup("Lore Entries", changes));
        }
    }

    private void UpdateStats(int added, int removed, int modified)
    {
        AddedCount.Text = $"{added} added";
        RemovedCount.Text = $"{removed} removed";
        ModifiedCount.Text = $"{modified} modified";
    }

    private static string Truncate(string? value)
    {
        if (string.IsNullOrEmpty(value)) return "(empty)";
        return value.Length > 80 ? value[..77] + "..." : value;
    }

    private void Restore_Click(object sender, RoutedEventArgs e)
    {
        RestoreRequested?.Invoke(this, EventArgs.Empty);
        StatusTextBlock.Text = "Restore requested.";
    }

    private void Clear_Click(object sender, RoutedEventArgs e)
    {
        DiffGroups.Clear();
        EmptyState.Visibility = Visibility.Visible;
        UpdateStats(0, 0, 0);
        RestoreButton.IsEnabled = false;
        StatusTextBlock.Text = "Cleared.";
    }
}

public enum ChangeType
{
    Added,
    Removed,
    Modified
}

public class DiffGroup
{
    public string EntityType { get; }
    public ObservableCollection<DiffItem> Changes { get; }
    public int ChangeCount => Changes.Count;

    public DiffGroup(string entityType, ObservableCollection<DiffItem> changes)
    {
        EntityType = entityType;
        Changes = changes;
    }
}

public class DiffItem
{
    public ChangeType Type { get; }
    public string PropertyName { get; }
    public string OldValue { get; }
    public string NewValue { get; }

    public string ChangeTypeLabel => Type switch
    {
        ChangeType.Added => "+",
        ChangeType.Removed => "-",
        ChangeType.Modified => "~",
        _ => "?"
    };

    public Brush ChangeBrush => Type switch
    {
        ChangeType.Added => new SolidColorBrush(Color.FromArgb(30, 166, 227, 161)),
        ChangeType.Removed => new SolidColorBrush(Color.FromArgb(30, 243, 139, 168)),
        ChangeType.Modified => new SolidColorBrush(Color.FromArgb(30, 249, 226, 175)),
        _ => new SolidColorBrush(Colors.Transparent)
    };

    public Brush BadgeBrush => Type switch
    {
        ChangeType.Added => new SolidColorBrush(Color.FromArgb(200, 166, 227, 161)),
        ChangeType.Removed => new SolidColorBrush(Color.FromArgb(200, 243, 139, 168)),
        ChangeType.Modified => new SolidColorBrush(Color.FromArgb(200, 249, 226, 175)),
        _ => new SolidColorBrush(Colors.Transparent)
    };

    public DiffItem(ChangeType type, string propertyName, string oldValue, string newValue)
    {
        Type = type;
        PropertyName = propertyName;
        OldValue = oldValue;
        NewValue = newValue;
    }
}
