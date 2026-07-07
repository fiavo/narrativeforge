using NarrativeForge.App.Export;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.Tests.Export;

public class GameEngineExporterTests
{
    [Fact]
    public async Task UnityExporter_WithDialogueTree_ProducesYaml()
    {
        var exporter = new UnityExporter();
        var tree = new DialogueTreeDto
        {
            Id = Guid.NewGuid(),
            Name = "Test Dialogue",
            StartNodeId = Guid.NewGuid(),
            Nodes =
            [
                new GraphNodeDto
                {
                    Id = Guid.NewGuid(),
                    Title = "Start",
                    Content = "Hello, world!"
                }
            ],
            Edges = []
        };

        var request = new ExportRequest
        {
            ProjectName = "TestProject",
            DialogueTree = tree
        };

        var result = await exporter.ExportAsync(request);

        Assert.True(result.Success);
        Assert.Contains("%YAML", result.Content);
        Assert.Contains("Hello, world!", result.Content);
        Assert.Contains(".asset", result.Filename);
    }

    [Fact]
    public async Task UnrealExporter_WithDialogueTree_ProducesDataTable()
    {
        var exporter = new UnrealExporter();
        var tree = new DialogueTreeDto
        {
            Id = Guid.NewGuid(),
            Name = "Test Dialogue",
            StartNodeId = Guid.NewGuid(),
            Nodes =
            [
                new GraphNodeDto
                {
                    Id = Guid.NewGuid(),
                    Title = "Start",
                    Content = "Welcome!"
                }
            ],
            Edges = []
        };

        var request = new ExportRequest
        {
            ProjectName = "TestProject",
            DialogueTree = tree
        };

        var result = await exporter.ExportAsync(request);

        Assert.True(result.Success);
        Assert.Contains("DataTable", result.Content);
        Assert.Contains("Welcome!", result.Content);
        Assert.Contains(".json", result.Filename);
    }

    [Fact]
    public async Task GodotExporter_WithDialogueTree_ProducesTres()
    {
        var exporter = new GodotExporter();
        var tree = new DialogueTreeDto
        {
            Id = Guid.NewGuid(),
            Name = "Test Dialogue",
            StartNodeId = Guid.NewGuid(),
            Nodes =
            [
                new GraphNodeDto
                {
                    Id = Guid.NewGuid(),
                    Title = "Start",
                    Content = "Greetings!"
                }
            ],
            Edges = []
        };

        var request = new ExportRequest
        {
            ProjectName = "TestProject",
            DialogueTree = tree
        };

        var result = await exporter.ExportAsync(request);

        Assert.True(result.Success);
        Assert.Contains("[gd_resource", result.Content);
        Assert.Contains("Greetings!", result.Content);
        Assert.Contains(".tres", result.Filename);
    }

    [Fact]
    public async Task UnityExporter_WithoutData_ReturnsError()
    {
        var exporter = new UnityExporter();
        var request = new ExportRequest { ProjectName = "Empty" };

        var result = await exporter.ExportAsync(request);

        Assert.False(result.Success);
        Assert.Contains("No dialogue tree or quest graph", result.Error);
    }

    [Fact]
    public void CanExport_GameEngineExporters_ReturnCorrectCategories()
    {
        var unityExporter = new UnityExporter();
        var unrealExporter = new UnrealExporter();
        var godotExporter = new GodotExporter();

        Assert.Equal("Game Engine", unityExporter.Category);
        Assert.Equal("Game Engine", unrealExporter.Category);
        Assert.Equal("Game Engine", godotExporter.Category);

        var requestWithTree = new ExportRequest { DialogueTree = new DialogueTreeDto() };
        Assert.True(unityExporter.CanExport(requestWithTree));
        Assert.True(unrealExporter.CanExport(requestWithTree));
        Assert.True(godotExporter.CanExport(requestWithTree));

        var emptyRequest = new ExportRequest();
        Assert.False(unityExporter.CanExport(emptyRequest));
        Assert.False(unrealExporter.CanExport(emptyRequest));
        Assert.False(godotExporter.CanExport(emptyRequest));
    }
}
