using NarrativeForge.App.Export;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.Tests.Export;

public class JsonExporterTests
{
    [Fact]
    public async Task ExportAsync_WithDialogueTree_ProducesValidJson()
    {
        var exporter = new JsonExporter();
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
                    Content = "Hello, traveler!"
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
        Assert.Contains("TestProject", result.Content);
        Assert.Contains("Hello, traveler!", result.Content);
        Assert.Contains("dialogueTree", result.Content);
        Assert.Contains(".json", result.Filename);
    }

    [Fact]
    public async Task ExportAsync_WithQuestGraph_ProducesValidJson()
    {
        var exporter = new JsonExporter();
        var quest = new QuestGraphDto
        {
            Id = Guid.NewGuid(),
            Name = "Main Quest",
            StartNodeId = Guid.NewGuid(),
            Nodes =
            [
                new GraphNodeDto
                {
                    Id = Guid.NewGuid(),
                    Title = "Quest Start",
                    Content = "Find the artifact.",
                    Objectives =
                    [
                        new GraphObjectiveDto
                        {
                            Id = Guid.NewGuid(),
                            Description = "Locate the ancient relic",
                            Type = "primary",
                            Target = "relic_location"
                        }
                    ]
                }
            ],
            Edges = []
        };

        var request = new ExportRequest
        {
            ProjectName = "QuestProject",
            QuestGraph = quest
        };

        var result = await exporter.ExportAsync(request);

        Assert.True(result.Success);
        Assert.Contains("questGraph", result.Content);
        Assert.Contains("Main Quest", result.Content);
        Assert.Contains("Locate the ancient relic", result.Content);
    }

    [Fact]
    public async Task ExportAsync_WithoutData_ReturnsError()
    {
        var exporter = new JsonExporter();
        var request = new ExportRequest { ProjectName = "Empty" };

        var result = await exporter.ExportAsync(request);

        Assert.False(result.Success);
        Assert.Contains("No dialogue tree or quest graph", result.Error);
    }

    [Fact]
    public void CanExport_WithDialogueTree_ReturnsTrue()
    {
        var exporter = new JsonExporter();
        var request = new ExportRequest { DialogueTree = new DialogueTreeDto() };
        Assert.True(exporter.CanExport(request));
    }

    [Fact]
    public void CanExport_WithQuestGraph_ReturnsTrue()
    {
        var exporter = new JsonExporter();
        var request = new ExportRequest { QuestGraph = new QuestGraphDto() };
        Assert.True(exporter.CanExport(request));
    }

    [Fact]
    public void CanExport_Empty_ReturnsFalse()
    {
        var exporter = new JsonExporter();
        var request = new ExportRequest();
        Assert.False(exporter.CanExport(request));
    }
}
