using System.Text;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Export;

public class MarkdownExporter : IExporter
{
    public string Name => "Markdown";
    public string FileExtension => ".md";
    public string Description => "Generates human-readable Markdown documentation for dialogue trees and quest graphs";
    public string Category => "General";

    public bool CanExport(ExportRequest request)
    {
        return request.DialogueTree != null || request.QuestGraph != null;
    }

    public Task<ExportResult> ExportAsync(ExportRequest request, CancellationToken cancellationToken = default)
    {
        if (request.DialogueTree is null && request.QuestGraph is null)
            return Task.FromResult(new ExportResult { Success = false, Error = "No dialogue tree or quest graph provided." });

        var sb = new StringBuilder();
        sb.AppendLine($"# {request.ProjectName}");
        sb.AppendLine();

        if (request.Metadata.Count > 0)
        {
            sb.AppendLine("## Metadata");
            sb.AppendLine();
            foreach (var kv in request.Metadata)
            {
                sb.AppendLine($"- **{kv.Key}**: {kv.Value}");
            }
            sb.AppendLine();
        }

        if (request.DialogueTree is not null)
        {
            cancellationToken.ThrowIfCancellationRequested();
            WriteDialogueTreeSection(sb, request.DialogueTree);
        }

        if (request.QuestGraph is not null)
        {
            cancellationToken.ThrowIfCancellationRequested();
            WriteQuestGraphSection(sb, request.QuestGraph);
        }

        if (request.Nodes.Count > 0 || request.Edges.Count > 0)
        {
            cancellationToken.ThrowIfCancellationRequested();
            WriteGraphSection(sb, request.Nodes, request.Edges);
        }

        var filename = $"{SanitizeName(request.ProjectName)}_docs.md";
        return Task.FromResult(new ExportResult
        {
            Success = true,
            Content = sb.ToString(),
            Filename = filename
        });
    }

    private static void WriteDialogueTreeSection(StringBuilder sb, DialogueTreeDto tree)
    {
        sb.AppendLine("## Dialogue Tree");
        sb.AppendLine();
        sb.AppendLine($"- **Name**: {tree.Name}");
        sb.AppendLine($"- **ID**: {tree.Id}");
        sb.AppendLine($"- **Start Node**: {tree.StartNodeId}");
        sb.AppendLine($"- **Node Count**: {tree.Nodes.Count}");
        sb.AppendLine($"- **Edge Count**: {tree.Edges.Count}");
        sb.AppendLine();

        if (tree.Nodes.Count > 0)
        {
            sb.AppendLine("### Nodes");
            sb.AppendLine();
            foreach (var node in tree.Nodes)
            {
                WriteNodeEntry(sb, node);
            }
        }

        if (tree.Edges.Count > 0)
        {
            sb.AppendLine("### Edges");
            sb.AppendLine();
            sb.AppendLine("| ID | Source | Target | Condition |");
            sb.AppendLine("|---|--------|--------|-----------|");
            foreach (var edge in tree.Edges)
            {
                sb.AppendLine($"| {edge.Id} | {edge.SourceId} | {edge.TargetId} | {edge.Condition} |");
            }
            sb.AppendLine();
        }
    }

    private static void WriteQuestGraphSection(StringBuilder sb, QuestGraphDto quest)
    {
        sb.AppendLine("## Quest Graph");
        sb.AppendLine();
        sb.AppendLine($"- **Name**: {quest.Name}");
        sb.AppendLine($"- **ID**: {quest.Id}");
        sb.AppendLine($"- **Start Node**: {quest.StartNodeId}");
        sb.AppendLine($"- **Node Count**: {quest.Nodes.Count}");
        sb.AppendLine($"- **Edge Count**: {quest.Edges.Count}");
        sb.AppendLine();

        if (quest.Nodes.Count > 0)
        {
            sb.AppendLine("### Nodes");
            sb.AppendLine();
            foreach (var node in quest.Nodes)
            {
                WriteNodeEntry(sb, node);
            }
        }

        if (quest.Edges.Count > 0)
        {
            sb.AppendLine("### Edges");
            sb.AppendLine();
            sb.AppendLine("| ID | Source | Target | Condition |");
            sb.AppendLine("|---|--------|--------|-----------|");
            foreach (var edge in quest.Edges)
            {
                sb.AppendLine($"| {edge.Id} | {edge.SourceId} | {edge.TargetId} | {edge.Condition} |");
            }
            sb.AppendLine();
        }
    }

    private static void WriteGraphSection(StringBuilder sb, List<GraphNodeDto> nodes, List<GraphEdgeDto> edges)
    {
        if (nodes.Count > 0)
        {
            sb.AppendLine("## Graph Nodes");
            sb.AppendLine();
            foreach (var node in nodes)
            {
                WriteNodeEntry(sb, node);
            }
        }

        if (edges.Count > 0)
        {
            sb.AppendLine("## Graph Edges");
            sb.AppendLine();
            sb.AppendLine("| ID | Source | Target | Condition |");
            sb.AppendLine("|---|--------|--------|-----------|");
            foreach (var edge in edges)
            {
                sb.AppendLine($"| {edge.Id} | {edge.SourceId} | {edge.TargetId} | {edge.Condition} |");
            }
            sb.AppendLine();
        }
    }

    private static void WriteNodeEntry(StringBuilder sb, GraphNodeDto node)
    {
        sb.AppendLine($"#### {node.Title}");
        sb.AppendLine();
        sb.AppendLine($"- **ID**: {node.Id}");
        sb.AppendLine($"- **Type**: {node.Type}");

        if (!string.IsNullOrWhiteSpace(node.Content))
        {
            sb.AppendLine();
            sb.AppendLine("> " + node.Content.Replace("\n", "\n> "));
        }

        if (node.Choices.Count > 0)
        {
            sb.AppendLine();
            sb.AppendLine("**Choices:**");
            foreach (var choice in node.Choices)
            {
                var condition = string.IsNullOrWhiteSpace(choice.Condition) ? "" : $" *(if {choice.Condition})*";
                sb.AppendLine($"- [{choice.Text}] → {choice.NextNodeId}{condition}");
            }
        }

        if (node.Objectives.Count > 0)
        {
            sb.AppendLine();
            sb.AppendLine("**Objectives:**");
            foreach (var obj in node.Objectives)
            {
                sb.AppendLine($"- [{obj.Type}] {obj.Description} → {obj.Target}");
            }
        }

        if (node.VariablesSet.Count > 0)
        {
            sb.AppendLine();
            sb.AppendLine("**Variables:**");
            foreach (var v in node.VariablesSet)
            {
                sb.AppendLine($"- `{v.Key}` = `{v.Value}`");
            }
        }

        sb.AppendLine();
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
