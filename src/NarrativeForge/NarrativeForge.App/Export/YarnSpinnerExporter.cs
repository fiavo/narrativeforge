using System.Text;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Export;

public class YarnSpinnerExporter : IExporter
{
    public string Name => "Yarn Spinner";
    public string FileExtension => ".yarn";
    public string Description => "Exports dialogue trees to Yarn Spinner format";
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

        bool firstNode = true;

        foreach (var node in tree.Nodes)
        {
            cancellationToken.ThrowIfCancellationRequested();

            if (!firstNode)
                sb.AppendLine();
            firstNode = false;

            var nodeName = SanitizeName(node.Title);
            sb.AppendLine($"title: {nodeName}");
            sb.AppendLine("tags: dialogue");
            sb.AppendLine("---");

            if (!string.IsNullOrWhiteSpace(node.Content))
            {
                sb.AppendLine(node.Content);
            }

            if (node.VariablesSet.Count > 0)
            {
                foreach (var v in node.VariablesSet)
                {
                    sb.AppendLine($"<<set {v.Key} to {v.Value}>>");
                }
            }

            if (node.Choices.Count > 0)
            {
                foreach (var choice in node.Choices)
                {
                    var targetNode = nodeMap.GetValueOrDefault(choice.NextNodeId);
                    var targetName = targetNode is not null ? SanitizeName(targetNode.Title) : "END";
                    sb.AppendLine($"<<option \"{choice.Text}\">> <<jump {targetName}>>");
                }
                sb.AppendLine("<<endoptions>>");
            }
            else if (edgesBySource.TryGetValue(node.Id, out var outgoingEdges))
            {
                foreach (var edge in outgoingEdges)
                {
                    var targetNode = nodeMap.GetValueOrDefault(edge.TargetId);
                    var targetName = targetNode is not null ? SanitizeName(targetNode.Title) : "END";
                    sb.AppendLine($"<<jump {targetName}>>");
                }
            }

            sb.AppendLine("===");
        }

        var filename = $"{SanitizeName(request.ProjectName)}_dialogue.yarn";
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
