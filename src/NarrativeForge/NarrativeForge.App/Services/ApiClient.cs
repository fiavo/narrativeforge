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

    public void Dispose()
    {
        _httpClient.Dispose();
    }
}
