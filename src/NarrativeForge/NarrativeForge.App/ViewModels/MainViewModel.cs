using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using NarrativeForge.App.Services;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.ViewModels;

public partial class MainViewModel : ObservableObject
{
    private readonly ApiClient _apiClient;

    [ObservableProperty]
    private string _statusText = "Ready";

    [ObservableProperty]
    private bool _isBusy;

    [ObservableProperty]
    private ProjectDto? _selectedProject;

    [ObservableProperty]
    private string _generationRequest = string.Empty;

    [ObservableProperty]
    private string _generationOutput = string.Empty;

    [ObservableProperty]
    private float _temperature = 0.7f;

    [ObservableProperty]
    private bool _isConnected;

    [ObservableProperty]
    private bool _showGraphEditor;

    public GraphEditorViewModel GraphEditorViewModel { get; } = new();

    public ObservableCollection<ProjectDto> Projects { get; } = [];

    public MainViewModel()
    {
        _apiClient = new ApiClient();
    }

    [RelayCommand]
    private async Task ConnectAsync()
    {
        IsBusy = true;
        StatusText = "Connecting to backend...";

        try
        {
            var projects = await _apiClient.GetProjectsAsync();
            Projects.Clear();
            foreach (var project in projects)
                Projects.Add(project);

            IsConnected = true;
            StatusText = $"Connected. {Projects.Count} project(s) loaded.";
        }
        catch (Exception ex)
        {
            IsConnected = false;
            StatusText = $"Connection failed: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private async Task GenerateAsync()
    {
        if (SelectedProject is null)
        {
            StatusText = "No project selected.";
            return;
        }

        IsBusy = true;
        StatusText = "Generating...";
        GenerationOutput = string.Empty;

        try
        {
            var request = new GenerateRequestDto
            {
                ProjectId = SelectedProject.Id,
                Request = GenerationRequest,
                Temperature = Temperature
            };

            var response = await _apiClient.GenerateAsync(request);
            if (response is null)
            {
                StatusText = "Generation failed.";
                return;
            }

            GenerationOutput = System.Text.Json.JsonSerializer.Serialize(
                response.Content,
                new System.Text.Json.JsonSerializerOptions { WriteIndented = true });

            StatusText = $"Generation complete. Stages: {string.Join(", ", response.Stages)}";
        }
        catch (Exception ex)
        {
            StatusText = $"Generation error: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    [RelayCommand]
    private async Task NewProjectAsync()
    {
        IsBusy = true;
        StatusText = "Creating project...";

        try
        {
            var request = new CreateProjectRequest
            {
                Name = "New Project",
                Genre = Core.Enums.GameGenre.RPG
            };

            var project = await _apiClient.CreateProjectAsync(request);
            if (project is not null)
            {
                Projects.Add(project);
                SelectedProject = project;
                StatusText = $"Project '{project.Name}' created.";
            }
            else
            {
                StatusText = "Failed to create project.";
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
    private async Task DeleteProjectAsync()
    {
        if (SelectedProject is null) return;

        IsBusy = true;
        StatusText = "Deleting project...";

        try
        {
            var success = await _apiClient.DeleteProjectAsync(SelectedProject.Id);
            if (success)
            {
                Projects.Remove(SelectedProject);
                SelectedProject = null;
                StatusText = "Project deleted.";
            }
            else
            {
                StatusText = "Failed to delete project.";
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
    private void OpenDialogueTree()
    {
        GraphEditorViewModel.ClearGraphCommand.Execute(null);
        GraphEditorViewModel.GraphName = "New Dialogue Tree";
        ShowGraphEditor = true;
        StatusText = "Dialogue tree editor opened.";
    }

    [RelayCommand]
    private void OpenQuestGraph()
    {
        GraphEditorViewModel.ClearGraphCommand.Execute(null);
        GraphEditorViewModel.GraphName = "New Quest Graph";
        ShowGraphEditor = true;
        StatusText = "Quest graph editor opened.";
    }

}
