using System.Windows;
using System.Windows.Controls;
using NarrativeForge.App.ViewModels;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Controls;

public partial class EntityListControl : UserControl
{
    public static readonly DependencyProperty ViewModelProperty =
        DependencyProperty.Register(nameof(ViewModel), typeof(StoryBibleManagerViewModel), typeof(EntityListControl),
            new PropertyMetadata(null, OnViewModelChanged));

    public StoryBibleManagerViewModel? ViewModel
    {
        get => (StoryBibleManagerViewModel?)GetValue(ViewModelProperty);
        set => SetValue(ViewModelProperty, value);
    }

    public event EventHandler<EntitySelectedEventArgs>? EntitySelected;

    public EntityListControl()
    {
        InitializeComponent();
    }

    private static void OnViewModelChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is EntityListControl control)
            control.BindViewModel();
    }

    private void BindViewModel()
    {
        if (ViewModel is null) return;

        CharactersList.ItemsSource = ViewModel.Characters;
        LocationsList.ItemsSource = ViewModel.Locations;
        FactionsList.ItemsSource = ViewModel.Factions;
        TimelineList.ItemsSource = ViewModel.TimelineEvents;
        LoreList.ItemsSource = ViewModel.LoreEntries;
    }

    private void CharactersList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (CharactersList.SelectedItem is CharacterDto character)
            EntitySelected?.Invoke(this, new EntitySelectedEventArgs(StoryBibleEntityType.Characters, character));
    }

    private void LocationsList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (LocationsList.SelectedItem is LocationDto location)
            EntitySelected?.Invoke(this, new EntitySelectedEventArgs(StoryBibleEntityType.Locations, location));
    }

    private void FactionsList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (FactionsList.SelectedItem is FactionDto faction)
            EntitySelected?.Invoke(this, new EntitySelectedEventArgs(StoryBibleEntityType.Factions, faction));
    }

    private void TimelineList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (TimelineList.SelectedItem is TimelineEventDto timelineEvent)
            EntitySelected?.Invoke(this, new EntitySelectedEventArgs(StoryBibleEntityType.TimelineEvents, timelineEvent));
    }

    private void LoreList_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (LoreList.SelectedItem is LoreEntryDto loreEntry)
            EntitySelected?.Invoke(this, new EntitySelectedEventArgs(StoryBibleEntityType.LoreEntries, loreEntry));
    }

    private async void AddCharacter_Click(object sender, RoutedEventArgs e)
    {
        if (ViewModel?.AddCharacterCommand.CanExecute(null) == true)
            await ViewModel.AddCharacterCommand.ExecuteAsync(null);
    }

    private async void AddLocation_Click(object sender, RoutedEventArgs e)
    {
        if (ViewModel?.AddLocationCommand.CanExecute(null) == true)
            await ViewModel.AddLocationCommand.ExecuteAsync(null);
    }

    private async void AddFaction_Click(object sender, RoutedEventArgs e)
    {
        if (ViewModel?.AddFactionCommand.CanExecute(null) == true)
            await ViewModel.AddFactionCommand.ExecuteAsync(null);
    }

    private async void AddTimelineEvent_Click(object sender, RoutedEventArgs e)
    {
        if (ViewModel?.AddTimelineEventCommand.CanExecute(null) == true)
            await ViewModel.AddTimelineEventCommand.ExecuteAsync(null);
    }

    private async void AddLoreEntry_Click(object sender, RoutedEventArgs e)
    {
        if (ViewModel?.AddLoreEntryCommand.CanExecute(null) == true)
            await ViewModel.AddLoreEntryCommand.ExecuteAsync(null);
    }
}

public class EntitySelectedEventArgs : EventArgs
{
    public StoryBibleEntityType EntityType { get; }
    public object Entity { get; }

    public EntitySelectedEventArgs(StoryBibleEntityType entityType, object entity)
    {
        EntityType = entityType;
        Entity = entity;
    }
}
