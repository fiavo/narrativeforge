using System.Net.Http;
using System.Net.Http.Json;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Services;

public class ApiClient : IDisposable
{
    private readonly HttpClient _httpClient;

    public ApiClient(string baseUrl = "http://localhost:8000")
    {
        _httpClient = new HttpClient { BaseAddress = new Uri(baseUrl) };
    }

    public async Task<List<ProjectDto>> GetProjectsAsync()
    {
        var response = await _httpClient.GetAsync("/api/projects");
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<List<ProjectDto>>() ?? [];
    }

    public async Task<ProjectDto?> GetProjectAsync(Guid id)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{id}");
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            return null;
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<ProjectDto>();
    }

    public async Task<ProjectDto?> CreateProjectAsync(CreateProjectRequest request)
    {
        var response = await _httpClient.PostAsJsonAsync("/api/projects", request);
        if (!response.IsSuccessStatusCode)
            return null;
        return await response.Content.ReadFromJsonAsync<ProjectDto>();
    }

    public async Task<bool> DeleteProjectAsync(Guid id)
    {
        var response = await _httpClient.DeleteAsync($"/api/projects/{id}");
        return response.IsSuccessStatusCode;
    }

    public async Task<GenerateResponseDto?> GenerateAsync(GenerateRequestDto request)
    {
        var response = await _httpClient.PostAsJsonAsync("/api/generate", request);
        if (!response.IsSuccessStatusCode)
            return null;
        return await response.Content.ReadFromJsonAsync<GenerateResponseDto>();
    }

    public async Task<List<DialogueTreeDto>> GetDialogueTreesAsync(Guid projectId)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/dialogue-trees");
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<List<DialogueTreeDto>>() ?? [];
    }

    public async Task<DialogueTreeDto?> GetDialogueTreeAsync(Guid projectId, Guid id)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/dialogue-trees/{id}");
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            return null;
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<DialogueTreeDto>();
    }

    public async Task<DialogueTreeDto?> CreateDialogueTreeAsync(Guid projectId, CreateDialogueTreeRequest request)
    {
        var response = await _httpClient.PostAsJsonAsync($"/api/projects/{projectId}/dialogue-trees", request);
        if (!response.IsSuccessStatusCode)
            return null;
        return await response.Content.ReadFromJsonAsync<DialogueTreeDto>();
    }

    public async Task<bool> DeleteDialogueTreeAsync(Guid projectId, Guid id)
    {
        var response = await _httpClient.DeleteAsync($"/api/projects/{projectId}/dialogue-trees/{id}");
        return response.IsSuccessStatusCode;
    }

    public async Task<List<QuestGraphDto>> GetQuestGraphsAsync(Guid projectId)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/quest-graphs");
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<List<QuestGraphDto>>() ?? [];
    }

    public async Task<QuestGraphDto?> GetQuestGraphAsync(Guid projectId, Guid id)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/quest-graphs/{id}");
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            return null;
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<QuestGraphDto>();
    }

    public async Task<QuestGraphDto?> CreateQuestGraphAsync(Guid projectId, CreateQuestGraphRequest request)
    {
        var response = await _httpClient.PostAsJsonAsync($"/api/projects/{projectId}/quest-graphs", request);
        if (!response.IsSuccessStatusCode)
            return null;
        return await response.Content.ReadFromJsonAsync<QuestGraphDto>();
    }

    public async Task<bool> DeleteQuestGraphAsync(Guid projectId, Guid id)
    {
        var response = await _httpClient.DeleteAsync($"/api/projects/{projectId}/quest-graphs/{id}");
        return response.IsSuccessStatusCode;
    }

    public async Task<StoryBibleDto?> GetStoryBibleAsync(Guid projectId)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/story-bible");
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            return null;
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<StoryBibleDto>();
    }

    public async Task<StoryBibleDto?> SaveStoryBibleAsync(Guid projectId, StoryBibleDto storyBible)
    {
        var response = await _httpClient.PutAsJsonAsync($"/api/projects/{projectId}/story-bible", storyBible);
        if (!response.IsSuccessStatusCode)
            return null;
        return await response.Content.ReadFromJsonAsync<StoryBibleDto>();
    }

    public async Task<List<CharacterDto>> GetCharactersAsync(Guid projectId)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/characters");
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<List<CharacterDto>>() ?? [];
    }

    public async Task<CharacterDto?> GetCharacterAsync(Guid projectId, Guid id)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/characters/{id}");
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            return null;
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<CharacterDto>();
    }

    public async Task<CharacterDto?> CreateCharacterAsync(Guid projectId, CreateCharacterRequest request)
    {
        var response = await _httpClient.PostAsJsonAsync($"/api/projects/{projectId}/characters", request);
        if (!response.IsSuccessStatusCode)
            return null;
        return await response.Content.ReadFromJsonAsync<CharacterDto>();
    }

    public async Task<bool> DeleteCharacterAsync(Guid projectId, Guid id)
    {
        var response = await _httpClient.DeleteAsync($"/api/projects/{projectId}/characters/{id}");
        return response.IsSuccessStatusCode;
    }

    public async Task<List<LocationDto>> GetLocationsAsync(Guid projectId)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/locations");
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<List<LocationDto>>() ?? [];
    }

    public async Task<LocationDto?> GetLocationAsync(Guid projectId, Guid id)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/locations/{id}");
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            return null;
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<LocationDto>();
    }

    public async Task<LocationDto?> CreateLocationAsync(Guid projectId, CreateLocationRequest request)
    {
        var response = await _httpClient.PostAsJsonAsync($"/api/projects/{projectId}/locations", request);
        if (!response.IsSuccessStatusCode)
            return null;
        return await response.Content.ReadFromJsonAsync<LocationDto>();
    }

    public async Task<bool> DeleteLocationAsync(Guid projectId, Guid id)
    {
        var response = await _httpClient.DeleteAsync($"/api/projects/{projectId}/locations/{id}");
        return response.IsSuccessStatusCode;
    }

    public async Task<List<FactionDto>> GetFactionsAsync(Guid projectId)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/factions");
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<List<FactionDto>>() ?? [];
    }

    public async Task<FactionDto?> GetFactionAsync(Guid projectId, Guid id)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/factions/{id}");
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            return null;
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<FactionDto>();
    }

    public async Task<FactionDto?> CreateFactionAsync(Guid projectId, CreateFactionRequest request)
    {
        var response = await _httpClient.PostAsJsonAsync($"/api/projects/{projectId}/factions", request);
        if (!response.IsSuccessStatusCode)
            return null;
        return await response.Content.ReadFromJsonAsync<FactionDto>();
    }

    public async Task<bool> DeleteFactionAsync(Guid projectId, Guid id)
    {
        var response = await _httpClient.DeleteAsync($"/api/projects/{projectId}/factions/{id}");
        return response.IsSuccessStatusCode;
    }

    public async Task<List<TimelineEventDto>> GetTimelineAsync(Guid projectId)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/timeline");
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<List<TimelineEventDto>>() ?? [];
    }

    public async Task<TimelineEventDto?> GetTimelineEventAsync(Guid projectId, Guid id)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/timeline/{id}");
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            return null;
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<TimelineEventDto>();
    }

    public async Task<TimelineEventDto?> CreateTimelineEventAsync(Guid projectId, CreateTimelineEventRequest request)
    {
        var response = await _httpClient.PostAsJsonAsync($"/api/projects/{projectId}/timeline", request);
        if (!response.IsSuccessStatusCode)
            return null;
        return await response.Content.ReadFromJsonAsync<TimelineEventDto>();
    }

    public async Task<bool> DeleteTimelineEventAsync(Guid projectId, Guid id)
    {
        var response = await _httpClient.DeleteAsync($"/api/projects/{projectId}/timeline/{id}");
        return response.IsSuccessStatusCode;
    }

    public async Task<List<LoreEntryDto>> GetLoreEntriesAsync(Guid projectId)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/lore");
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<List<LoreEntryDto>>() ?? [];
    }

    public async Task<LoreEntryDto?> GetLoreEntryAsync(Guid projectId, Guid id)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/lore/{id}");
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            return null;
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<LoreEntryDto>();
    }

    public async Task<LoreEntryDto?> CreateLoreEntryAsync(Guid projectId, CreateLoreEntryRequest request)
    {
        var response = await _httpClient.PostAsJsonAsync($"/api/projects/{projectId}/lore", request);
        if (!response.IsSuccessStatusCode)
            return null;
        return await response.Content.ReadFromJsonAsync<LoreEntryDto>();
    }

    public async Task<bool> DeleteLoreEntryAsync(Guid projectId, Guid id)
    {
        var response = await _httpClient.DeleteAsync($"/api/projects/{projectId}/lore/{id}");
        return response.IsSuccessStatusCode;
    }

    public async Task<List<VersionDto>> GetVersionsAsync(Guid projectId)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/versions");
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<List<VersionDto>>() ?? [];
    }

    public async Task<VersionDto?> GetVersionAsync(Guid projectId, Guid versionId)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/versions/{versionId}");
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            return null;
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<VersionDto>();
    }

    public async Task<List<VersionDiffDto>> GetVersionDiffAsync(Guid projectId, Guid versionId)
    {
        var response = await _httpClient.GetAsync($"/api/projects/{projectId}/versions/{versionId}/diff");
        if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            return [];
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadFromJsonAsync<List<VersionDiffDto>>() ?? [];
    }

    public async Task<VersionDto?> RestoreVersionAsync(Guid projectId, Guid versionId)
    {
        var response = await _httpClient.PostAsJsonAsync($"/api/projects/{projectId}/versions/{versionId}/restore", new { });
        if (!response.IsSuccessStatusCode)
            return null;
        return await response.Content.ReadFromJsonAsync<VersionDto>();
    }

    public void Dispose()
    {
        _httpClient.Dispose();
    }
}
