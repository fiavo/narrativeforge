using NarrativeForge.App.Export;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.Tests.Export;

public class InkExporterTests
{
    [Fact]
    public async Task ExportAsync_WithDialogueTree_ProducesValidInk()
    {
        var exporter = new InkExporter();
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
        Assert.Contains("=== Start ===", result.Content);
        Assert.Contains("Hello, traveler!", result.Content);
        Assert.Contains("-> DONE", result.Content);
    }

    [Fact]
    public async Task ExportAsync_WithChoices_GeneratesChoiceSyntax()
    {
        var exporter = new InkExporter();
        var nodeId = Guid.NewGuid();
        var choiceTargetId = Guid.NewGuid();

        var tree = new DialogueTreeDto
        {
            Id = Guid.NewGuid(),
            Name = "Choice Test",
            StartNodeId = nodeId,
            Nodes =
            [
                new GraphNodeDto
                {
                    Id = nodeId,
                    Title = "Greeting",
                    Content = "What would you like to do?",
                    Choices =
                    [
                        new GraphChoiceDto
                        {
                            Id = Guid.NewGuid(),
                            Text = "Attack",
                            NextNodeId = choiceTargetId
                        },
                        new GraphChoiceDto
                        {
                            Id = Guid.NewGuid(),
                            Text = "Flee",
                            NextNodeId = choiceTargetId
                        }
                    ]
                },
                new GraphNodeDto
                {
                    Id = choiceTargetId,
                    Title = "Action",
                    Content = "You act."
                }
            ],
            Edges = []
        };

        var request = new ExportRequest
        {
            ProjectName = "ChoiceProject",
            DialogueTree = tree
        };

        var result = await exporter.ExportAsync(request);

        Assert.True(result.Success);
        Assert.Contains("+ [Attack] -> Action", result.Content);
        Assert.Contains("+ [Flee] -> Action", result.Content);
    }

    [Fact]
    public async Task ExportAsync_WithVariables_GeneratesVariableSyntax()
    {
        var exporter = new InkExporter();
        var tree = new DialogueTreeDto
        {
            Id = Guid.NewGuid(),
            Name = "Var Test",
            StartNodeId = Guid.NewGuid(),
            Nodes =
            [
                new GraphNodeDto
                {
                    Id = Guid.NewGuid(),
                    Title = "Scene1",
                    Content = "The scene begins.",
                    VariablesSet =
                    [
                        new GraphVariableSetDto { Key = "reputation", Value = "0" },
                        new GraphVariableSetDto { Key = "met_guard", Value = "true" }
                    ]
                }
            ],
            Edges = []
        };

        var request = new ExportRequest
        {
            ProjectName = "VarProject",
            DialogueTree = tree
        };

        var result = await exporter.ExportAsync(request);

        Assert.True(result.Success);
        Assert.Contains("~ reputation = 0", result.Content);
        Assert.Contains("~ met_guard = true", result.Content);
    }

    [Fact]
    public async Task ExportAsync_WithEdges_GeneratesFlowLinks()
    {
        var exporter = new InkExporter();
        var nodeA = Guid.NewGuid();
        var nodeB = Guid.NewGuid();

        var tree = new DialogueTreeDto
        {
            Id = Guid.NewGuid(),
            Name = "Flow Test",
            StartNodeId = nodeA,
            Nodes =
            [
                new GraphNodeDto { Id = nodeA, Title = "Start", Content = "Beginning." },
                new GraphNodeDto { Id = nodeB, Title = "End", Content = "The end." }
            ],
            Edges =
            [
                new GraphEdgeDto { Id = Guid.NewGuid(), SourceId = nodeA, TargetId = nodeB }
            ]
        };

        var request = new ExportRequest
        {
            ProjectName = "FlowProject",
            DialogueTree = tree
        };

        var result = await exporter.ExportAsync(request);

        Assert.True(result.Success);
        Assert.Contains("-> End", result.Content);
    }

    [Fact]
    public void CanExport_WithDialogueTree_ReturnsTrue()
    {
        var exporter = new InkExporter();
        var request = new ExportRequest
        {
            DialogueTree = new DialogueTreeDto()
        };

        Assert.True(exporter.CanExport(request));
    }

    [Fact]
    public async Task ExportAsync_WithoutDialogueTree_ReturnsError()
    {
        var exporter = new InkExporter();
        var request = new ExportRequest();

        var result = await exporter.ExportAsync(request);

        Assert.False(result.Success);
        Assert.Contains("No dialogue tree", result.Error);
    }
}
