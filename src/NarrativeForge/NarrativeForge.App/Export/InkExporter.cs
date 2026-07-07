using System.Text;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Export;

public class InkExporter : IExporter
{
    public string Name => "Ink";
    public string FileExtension => ".ink";
    public string Description => "Exports dialogue trees to Ink scripting format";
    public string Category => "Dialogue";

    public bool CanExport(ExportRequest request)
    {
        return request.DialogueTree != null;
    }

    public Task<ExportResult> ExportAsync(ExportRequest request, CancellationToken cancellationToken = default)
    {
        if (request.DialogueTree is null)
            return Task.FromResult(new ExportResult { Success = false, Error = "No dialogue tree provided." });

        var tree = request.DialogueTree;
        var sb = new StringBuilder();

        var nodeMap = tree.Nodes.ToDictionary(n => n.Id);
        var edgesBySource = tree.Edges
            .GroupBy(e => e.SourceId)
            .ToDictionary(g => g.Key, g => g.ToList());

        foreach (var node in tree.Nodes)
        {
            cancellationToken.ThrowIfCancellationRequested();

            var knotName = SanitizeName(node.Title);
            sb.AppendLine($"=== {knotName} ===");
            sb.AppendLine();

            if (!string.IsNullOrWhiteSpace(node.Content))
            {
                sb.AppendLine(node.Content);
                sb.AppendLine();
            }

            if (node.VariablesSet.Count > 0)
            {
                foreach (var v in node.VariablesSet)
                {
                    sb.AppendLine($"~ {v.Key} = {v.Value}");
                }
                sb.AppendLine();
            }

            if (node.Choices.Count > 0)
            {
                foreach (var choice in node.Choices)
                {
                    var targetNode = nodeMap.GetValueOrDefault(choice.NextNodeId);
                    var targetName = targetNode is not null ? SanitizeName(targetNode.Title) : "END";
                    sb.AppendLine($"+ [{choice.Text}] -> {targetName}");
                }
            }
            else if (edgesBySource.TryGetValue(node.Id, out var outgoingEdges))
            {
                foreach (var edge in outgoingEdges)
                {
                    var targetNode = nodeMap.GetValueOrDefault(edge.TargetId);
                    var targetName = targetNode is not null ? SanitizeName(targetNode.Title) : "END";
                    sb.AppendLine($"-> {targetName}");
                }
            }
            else
            {
                sb.AppendLine("-> DONE");
            }

            sb.AppendLine();
        }

        var filename = $"{SanitizeName(request.ProjectName)}_dialogue.ink";
        return Task.FromResult(new ExportResult
        {
            Success = true,
            Content = sb.ToString(),
            Filename = filename
        });
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
