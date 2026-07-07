using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Export;

public class UnrealExporter : IExporter
{
    public string Name => "Unreal";
    public string FileExtension => ".json";
    public string Description => "Exports dialogue trees as Unreal Engine DataTable JSON";
    public string Category => "Game Engine";

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
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
        var filename = $"{SanitizeName(request.ProjectName)}_datatable.json";

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
            ["tableName"] = $"{SanitizeTableName(request.ProjectName)}_DataTable",
            ["tableType"] = "DialogueDataTable",
            ["metadata"] = request.Metadata,
            ["rows"] = new List<object>()
        };

        var rows = (List<object>)data["rows"];

        if (request.DialogueTree is not null)
        {
            foreach (var node in request.DialogueTree.Nodes)
            {
                rows.Add(BuildRow(node, "Dialogue"));
            }
        }

        if (request.QuestGraph is not null)
        {
            foreach (var node in request.QuestGraph.Nodes)
            {
                rows.Add(BuildRow(node, "Quest"));
            }
        }

        if (request.Nodes.Count > 0)
        {
            foreach (var node in request.Nodes)
            {
                rows.Add(BuildRow(node, "Graph"));
            }
        }

        return data;
    }

    private static object BuildRow(GraphNodeDto node, string source)
    {
        return new
        {
            rowName = node.Title,
            rowId = node.Id.ToString(),
            nodeType = node.Type,
            content = node.Content,
            source = source,
            position = new { x = node.X, y = node.Y },
            choices = node.Choices.Select(c => new
            {
                id = c.Id.ToString(),
                text = c.Text,
                nextNodeId = c.NextNodeId.ToString(),
                condition = c.Condition
            }).ToList(),
            objectives = node.Objectives.Select(o => new
            {
                id = o.Id.ToString(),
                description = o.Description,
                type = o.Type,
                target = o.Target
            }).ToList(),
            variables = node.VariablesSet.Select(v => new
            {
                key = v.Key,
                value = v.Value
            }).ToList()
        };
    }

    private static string SanitizeTableName(string name)
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
