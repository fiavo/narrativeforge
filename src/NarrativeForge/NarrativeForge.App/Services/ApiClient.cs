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

    public void Dispose()
    {
        _httpClient.Dispose();
    }
}
