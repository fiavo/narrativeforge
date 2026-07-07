using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using NarrativeForge.App.Services;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.ViewModels;

public partial class StoryBibleManagerViewModel : ObservableObject
{
    private readonly ApiClient _apiClient;

    [ObservableProperty]
    private Guid _projectId;

    [ObservableProperty]
    private bool _isLoaded;

    [ObservableProperty]
    private bool _isBusy;

    [ObservableProperty]
    private string _statusText = "Ready";

    [ObservableProperty]
    private StoryBibleEntityType _selectedEntityType;

    [ObservableProperty]
    private CharacterDto? _selectedCharacter;

    [ObservableProperty]
    private LocationDto? _selectedLocation;

    [ObservableProperty]
    private FactionDto? _selectedFaction;

    [ObservableProperty]
    private TimelineEventDto? _selectedTimelineEvent;

    [ObservableProperty]
    private LoreEntryDto? _selectedLoreEntry;

    [ObservableProperty]
    private string _worldSettings = string.Empty;

    [ObservableProperty]
    private string _magicSystem = string.Empty;

    [ObservableProperty]
    private string _technologyLevel = string.Empty;

    public ObservableCollection<CharacterDto> Characters { get; } = [];
    public ObservableCollection<LocationDto> Locations { get; } = [];
    public ObservableCollection<FactionDto> Factions { get; } = [];
    public ObservableCollection<TimelineEventDto> TimelineEvents { get; } = [];
    public ObservableCollection<LoreEntryDto> LoreEntries { get; } = [];

    public StoryBibleManagerViewModel()
    {
        _apiClient = new ApiClient();
    }

    public StoryBibleManagerViewModel(ApiClient apiClient)
    {
        _apiClient = apiClient;
    }

    [RelayCommand]
    private async Task LoadProjectAsync()
    {
        IsBusy = true;
        StatusText = "Loading story bible...";

        try
        {
            var storyBible = await _apiClient.GetStoryBibleAsync(ProjectId);
            if (storyBible is null)
            {
                StatusText = "No story bible found for this project.";
                return;
            }

            Characters.Clear();
            foreach (var c in storyBible.Characters)
                Characters.Add(c);

            Locations.Clear();
            foreach (var l in storyBible.Locations)
                Locations.Add(l);

            Factions.Clear();
            foreach (var f in storyBible.Factions)
                Factions.Add(f);

            TimelineEvents.Clear();
            foreach (var e in storyBible.TimelineEvents)
                TimelineEvents.Add(e);

            LoreEntries.Clear();
            foreach (var l in storyBible.LoreEntries)
                LoreEntries.Add(l);

            WorldSettings = storyBible.WorldSettings;
            MagicSystem = storyBible.MagicSystem;
            TechnologyLevel = storyBible.TechnologyLevel;

            IsLoaded = true;
            StatusText = $"Loaded: {Characters.Count} characters, {Locations.Count} locations, {Factions.Count} factions, {TimelineEvents.Count} events, {LoreEntries.Count} lore entries.";
        }
        catch (Exception ex)
        {
            StatusText = $"Error loading story bible: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private async Task SaveAsync()
    {
        if (!IsLoaded)
        {
            StatusText = "No story bible loaded.";
            return;
        }

        IsBusy = true;
        StatusText = "Saving story bible...";

        try
        {
            var storyBible = new StoryBibleDto
            {
                Id = Guid.NewGuid(),
                ProjectId = ProjectId,
                Characters = Characters.ToList(),
                Locations = Locations.ToList(),
                Factions = Factions.ToList(),
                TimelineEvents = TimelineEvents.ToList(),
                LoreEntries = LoreEntries.ToList(),
                WorldSettings = WorldSettings,
                MagicSystem = MagicSystem,
                TechnologyLevel = TechnologyLevel
            };

            var result = await _apiClient.SaveStoryBibleAsync(ProjectId, storyBible);
            if (result is not null)
                StatusText = "Story bible saved.";
            else
                StatusText = "Failed to save story bible.";
        }
        catch (Exception ex)
        {
            StatusText = $"Error saving: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private async Task AddCharacterAsync()
    {
        if (!IsLoaded) return;

        IsBusy = true;
        try
        {
            var request = new CreateCharacterRequest { Name = "New Character" };
            var character = await _apiClient.CreateCharacterAsync(ProjectId, request);
            if (character is not null)
            {
                Characters.Add(character);
                SelectedCharacter = character;
                StatusText = $"Character '{character.Name}' added.";
            }
            else
            {
                StatusText = "Failed to add character.";
            }
        }
        catch (Exception ex)
        {
            StatusText = $"Error: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private async Task DeleteCharacterAsync()
    {
        if (SelectedCharacter is null) return;

        IsBusy = true;
        try
        {
            var success = await _apiClient.DeleteCharacterAsync(ProjectId, SelectedCharacter.Id);
            if (success)
            {
                var name = SelectedCharacter.Name;
                Characters.Remove(SelectedCharacter);
                SelectedCharacter = null;
                StatusText = $"Character '{name}' deleted.";
            }
            else
            {
                StatusText = "Failed to delete character.";
            }
        }
        catch (Exception ex)
        {
            StatusText = $"Error: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private async Task AddLocationAsync()
    {
        if (!IsLoaded) return;

        IsBusy = true;
        try
        {
            var request = new CreateLocationRequest { Name = "New Location" };
            var location = await _apiClient.CreateLocationAsync(ProjectId, request);
            if (location is not null)
            {
                Locations.Add(location);
                SelectedLocation = location;
                StatusText = $"Location '{location.Name}' added.";
            }
            else
            {
                StatusText = "Failed to add location.";
            }
        }
        catch (Exception ex)
        {
            StatusText = $"Error: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private async Task DeleteLocationAsync()
    {
        if (SelectedLocation is null) return;

        IsBusy = true;
        try
        {
            var success = await _apiClient.DeleteLocationAsync(ProjectId, SelectedLocation.Id);
            if (success)
            {
                var name = SelectedLocation.Name;
                Locations.Remove(SelectedLocation);
                SelectedLocation = null;
                StatusText = $"Location '{name}' deleted.";
            }
            else
            {
                StatusText = "Failed to delete location.";
            }
        }
        catch (Exception ex)
        {
            StatusText = $"Error: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private async Task AddFactionAsync()
    {
        if (!IsLoaded) return;

        IsBusy = true;
        try
        {
            var request = new CreateFactionRequest { Name = "New Faction" };
            var faction = await _apiClient.CreateFactionAsync(ProjectId, request);
            if (faction is not null)
            {
                Factions.Add(faction);
                SelectedFaction = faction;
                StatusText = $"Faction '{faction.Name}' added.";
            }
            else
            {
                StatusText = "Failed to add faction.";
            }
        }
        catch (Exception ex)
        {
            StatusText = $"Error: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private async Task DeleteFactionAsync()
    {
        if (SelectedFaction is null) return;

        IsBusy = true;
        try
        {
            var success = await _apiClient.DeleteFactionAsync(ProjectId, SelectedFaction.Id);
            if (success)
            {
                var name = SelectedFaction.Name;
                Factions.Remove(SelectedFaction);
                SelectedFaction = null;
                StatusText = $"Faction '{name}' deleted.";
            }
            else
            {
                StatusText = "Failed to delete faction.";
            }
        }
        catch (Exception ex)
        {
            StatusText = $"Error: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private async Task AddTimelineEventAsync()
    {
        if (!IsLoaded) return;

        IsBusy = true;
        try
        {
            var request = new CreateTimelineEventRequest { Title = "New Event" };
            var timelineEvent = await _apiClient.CreateTimelineEventAsync(ProjectId, request);
            if (timelineEvent is not null)
            {
                TimelineEvents.Add(timelineEvent);
                SelectedTimelineEvent = timelineEvent;
                StatusText = $"Timeline event '{timelineEvent.Name}' added.";
            }
            else
            {
                StatusText = "Failed to add timeline event.";
            }
        }
        catch (Exception ex)
        {
            StatusText = $"Error: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private async Task DeleteTimelineEventAsync()
    {
        if (SelectedTimelineEvent is null) return;

        IsBusy = true;
        try
        {
            var success = await _apiClient.DeleteTimelineEventAsync(ProjectId, SelectedTimelineEvent.Id);
            if (success)
            {
                var name = SelectedTimelineEvent.Name;
                TimelineEvents.Remove(SelectedTimelineEvent);
                SelectedTimelineEvent = null;
                StatusText = $"Timeline event '{name}' deleted.";
            }
            else
            {
                StatusText = "Failed to delete timeline event.";
            }
        }
        catch (Exception ex)
        {
            StatusText = $"Error: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private async Task AddLoreEntryAsync()
    {
        if (!IsLoaded) return;

        IsBusy = true;
        try
        {
            var request = new CreateLoreEntryRequest { Title = "New Lore Entry" };
            var loreEntry = await _apiClient.CreateLoreEntryAsync(ProjectId, request);
            if (loreEntry is not null)
            {
                LoreEntries.Add(loreEntry);
                SelectedLoreEntry = loreEntry;
                StatusText = $"Lore entry '{loreEntry.Title}' added.";
            }
            else
            {
                StatusText = "Failed to add lore entry.";
            }
        }
        catch (Exception ex)
        {
            StatusText = $"Error: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private async Task DeleteLoreEntryAsync()
    {
        if (SelectedLoreEntry is null) return;

        IsBusy = true;
        try
        {
            var success = await _apiClient.DeleteLoreEntryAsync(ProjectId, SelectedLoreEntry.Id);
            if (success)
            {
                var title = SelectedLoreEntry.Title;
                LoreEntries.Remove(SelectedLoreEntry);
                SelectedLoreEntry = null;
                StatusText = $"Lore entry '{title}' deleted.";
            }
            else
            {
                StatusText = "Failed to delete lore entry.";
            }
        }
        catch (Exception ex)
        {
            StatusText = $"Error: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }
}

public enum StoryBibleEntityType
{
    Characters,
    Locations,
    Factions,
    TimelineEvents,
    LoreEntries
}
