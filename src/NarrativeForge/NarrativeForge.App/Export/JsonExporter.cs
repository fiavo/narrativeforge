using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Export;

public class JsonExporter : IExporter
{
    public string Name => "JSON";
    public string FileExtension => ".json";
    public string Description => "Exports dialogue trees and quest graphs as structured JSON";
    public string Category => "General";

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    public bool CanExport(ExportRequest request)
    {
        return request.DialogueTree != null || request.QuestGraph != null;
    }

    public Task<ExportResult> ExportAsync(ExportRequest request, CancellationToken cancellationToken = default)
    {
        if (request.DialogueTree is null && request.QuestGraph is null)
            return Task.FromResult(new ExportResult { Success = false, Error = "No dialogue tree or quest graph provided." });

        var exportData = BuildExportData(request);
        var json = JsonSerializer.Serialize(exportData, JsonOptions);
        var filename = $"{SanitizeName(request.ProjectName)}_export.json";

        return Task.FromResult(new ExportResult
        {
            Success = true,
            Content = json,
            Filename = filename
        });
    }

    private static object BuildExportData(ExportRequest request)
    {
        var data = new Dictionary<string, object>
        {
            ["projectName"] = request.ProjectName,
            ["metadata"] = request.Metadata
        };

        if (request.DialogueTree is not null)
        {
            data["dialogueTree"] = new
            {
                id = request.DialogueTree.Id,
                name = request.DialogueTree.Name,
                startNodeId = request.DialogueTree.StartNodeId,
                nodes = request.DialogueTree.Nodes.Select(n => new
                {
                    id = n.Id,
                    type = n.Type,
                    title = n.Title,
                    content = n.Content,
                    x = n.X,
                    y = n.Y,
                    choices = n.Choices.Select(c => new
                    {
                        id = c.Id,
                        text = c.Text,
                        nextNodeId = c.NextNodeId,
                        condition = c.Condition
                    }).ToList(),
                    objectives = n.Objectives.Select(o => new
                    {
                        id = o.Id,
                        description = o.Description,
                        type = o.Type,
                        target = o.Target
                    }).ToList(),
                    variablesSet = n.VariablesSet.Select(v => new
                    {
                        key = v.Key,
                        value = v.Value
                    }).ToList()
                }).ToList(),
                edges = request.DialogueTree.Edges.Select(e => new
                {
                    id = e.Id,
                    sourceId = e.SourceId,
                    targetId = e.TargetId,
                    condition = e.Condition
                }).ToList()
            };
        }

        if (request.QuestGraph is not null)
        {
            data["questGraph"] = new
            {
                id = request.QuestGraph.Id,
                name = request.QuestGraph.Name,
                startNodeId = request.QuestGraph.StartNodeId,
                nodes = request.QuestGraph.Nodes.Select(n => new
                {
                    id = n.Id,
                    type = n.Type,
                    title = n.Title,
                    content = n.Content,
                    x = n.X,
                    y = n.Y,
                    choices = n.Choices.Select(c => new
                    {
                        id = c.Id,
                        text = c.Text,
                        nextNodeId = c.NextNodeId,
                        condition = c.Condition
                    }).ToList(),
                    objectives = n.Objectives.Select(o => new
                    {
                        id = o.Id,
                        description = o.Description,
                        type = o.Type,
                        target = o.Target
                    }).ToList(),
                    variablesSet = n.VariablesSet.Select(v => new
                    {
                        key = v.Key,
                        value = v.Value
                    }).ToList()
                }).ToList(),
                edges = request.QuestGraph.Edges.Select(e => new
                {
                    id = e.Id,
                    sourceId = e.SourceId,
                    targetId = e.TargetId,
                    condition = e.Condition
                }).ToList()
            };
        }

        if (request.Nodes.Count > 0)
        {
            data["nodes"] = request.Nodes.Select(n => new
            {
                id = n.Id,
                type = n.Type,
                title = n.Title,
                content = n.Content,
                x = n.X,
                y = n.Y,
                choices = n.Choices.Select(c => new
                {
                    id = c.Id,
                    text = c.Text,
                    nextNodeId = c.NextNodeId,
                    condition = c.Condition
                }).ToList(),
                objectives = n.Objectives.Select(o => new
                {
                    id = o.Id,
                    description = o.Description,
                    type = o.Type,
                    target = o.Target
                }).ToList(),
                variablesSet = n.VariablesSet.Select(v => new
                {
                    key = v.Key,
                    value = v.Value
                }).ToList()
            }).ToList();
        }

        if (request.Edges.Count > 0)
        {
            data["edges"] = request.Edges.Select(e => new
            {
                id = e.Id,
                sourceId = e.SourceId,
                targetId = e.TargetId,
                condition = e.Condition
            }).ToList();
        }

        return data;
    }

    private static string SanitizeName(string name)
    {
        var sb = new StringBuilder(name.Length);
        foreach (var c in name)
        {
            if (char.IsLetterOrDigit(c) || c == '_')
                sb.Append(c);
            else
                sb.Append('_');
        }
        return sb.ToString();
    }
}
