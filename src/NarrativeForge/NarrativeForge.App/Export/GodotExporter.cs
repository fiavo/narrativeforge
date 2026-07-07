using System.Text;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Export;

public class GodotExporter : IExporter
{
    public string Name => "Godot";
    public string FileExtension => ".tres";
    public string Description => "Exports dialogue trees as Godot Text Resource files";
    public string Category => "Game Engine";

    private int _resourceIndex = 1;

    public bool CanExport(ExportRequest request)
    {
        return request.DialogueTree != null || request.QuestGraph != null;
    }

    public Task<ExportResult> ExportAsync(ExportRequest request, CancellationToken cancellationToken = default)
    {
        if (request.DialogueTree is null && request.QuestGraph is null)
            return Task.FromResult(new ExportResult { Success = false, Error = "No dialogue tree or quest graph provided." });

        _resourceIndex = 1;
        var sb = new StringBuilder();
        sb.AppendLine("[gd_resource type=\"Resource\" format=3]");
        sb.AppendLine();
        sb.AppendLine("[ext_resource type=\"Script\" path=\"res://scripts/narrative/dialogue_data.gd\" id=\"1_script\"]");
        sb.AppendLine();

        var subResources = new List<string>();

        if (request.DialogueTree is not null)
        {
            cancellationToken.ThrowIfCancellationRequested();
            WriteDialogueTreeRes(sb, request.DialogueTree, subResources);
        }

        if (request.QuestGraph is not null)
        {
            cancellationToken.ThrowIfCancellationRequested();
            WriteQuestGraphRes(sb, request.QuestGraph, subResources);
        }

        if (request.Nodes.Count > 0 || request.Edges.Count > 0)
        {
            cancellationToken.ThrowIfCancellationRequested();
            WriteGraphRes(sb, request.Nodes, request.Edges, subResources);
        }

        foreach (var sub in subResources)
        {
            sb.AppendLine(sub);
        }

        sb.AppendLine("[resource]");
        sb.AppendLine($"script = ExtResource(\"1_script\")");
        sb.AppendLine($"project_name = \"{EscapeTresString(request.ProjectName)}\"");

        if (request.DialogueTree is not null)
        {
            sb.AppendLine($"dialogue_tree_name = \"{EscapeTresString(request.DialogueTree.Name)}\"");
            sb.AppendLine($"dialogue_tree_id = \"{request.DialogueTree.Id}\"");
        }

        if (request.QuestGraph is not null)
        {
            sb.AppendLine($"quest_graph_name = \"{EscapeTresString(request.QuestGraph.Name)}\"");
            sb.AppendLine($"quest_graph_id = \"{request.QuestGraph.Id}\"");
        }

        var filename = $"{SanitizeName(request.ProjectName)}_dialogue.tres";
        return Task.FromResult(new ExportResult
        {
            Success = true,
            Content = sb.ToString(),
            Filename = filename
        });
    }

    private void WriteDialogueTreeRes(StringBuilder sb, DialogueTreeDto tree, List<string> subResources)
    {
        var id = _resourceIndex++;
        subResources.Add($"[sub_resource type=\"Resource\" id=\"SubResource_{id}\"]");
        subResources.Add($"dialogue_name = \"{EscapeTresString(tree.Name)}\"");
        subResources.Add($"start_node_id = \"{tree.StartNodeId}\"");
        subResources.Add($"node_count = {tree.Nodes.Count}");

        if (tree.Nodes.Count > 0)
        {
            subResources.Add("nodes = [");
            foreach (var node in tree.Nodes)
            {
                subResources.Add($"  {{ \"id\": \"{node.Id}\", \"title\": \"{EscapeTresString(node.Title)}\", \"content\": \"{EscapeTresString(node.Content)}\", \"type\": \"{EscapeTresString(node.Type)}\" }}");
            }
            subResources.Add("]");
        }
    }

    private void WriteQuestGraphRes(StringBuilder sb, QuestGraphDto quest, List<string> subResources)
    {
        var id = _resourceIndex++;
        subResources.Add($"[sub_resource type=\"Resource\" id=\"SubResource_{id}\"]");
        subResources.Add($"quest_name = \"{EscapeTresString(quest.Name)}\"");
        subResources.Add($"start_node_id = \"{quest.StartNodeId}\"");
        subResources.Add($"node_count = {quest.Nodes.Count}");

        if (quest.Nodes.Count > 0)
        {
            subResources.Add("nodes = [");
            foreach (var node in quest.Nodes)
            {
                subResources.Add($"  {{ \"id\": \"{node.Id}\", \"title\": \"{EscapeTresString(node.Title)}\", \"content\": \"{EscapeTresString(node.Content)}\", \"type\": \"{EscapeTresString(node.Type)}\" }}");
            }
            subResources.Add("]");
        }
    }

    private void WriteGraphRes(StringBuilder sb, List<GraphNodeDto> nodes, List<GraphEdgeDto> edges, List<string> subResources)
    {
        if (nodes.Count > 0)
        {
            var id = _resourceIndex++;
            subResources.Add($"[sub_resource type=\"Resource\" id=\"SubResource_{id}\"]");
            subResources.Add("graph_nodes = [");
            foreach (var node in nodes)
            {
                subResources.Add($"  {{ \"id\": \"{node.Id}\", \"title\": \"{EscapeTresString(node.Title)}\", \"content\": \"{EscapeTresString(node.Content)}\", \"type\": \"{EscapeTresString(node.Type)}\" }}");
            }
            subResources.Add("]");
        }

        if (edges.Count > 0)
        {
            var id = _resourceIndex++;
            subResources.Add($"[sub_resource type=\"Resource\" id=\"SubResource_{id}\"]");
            subResources.Add("graph_edges = [");
            foreach (var edge in edges)
            {
                subResources.Add($"  {{ \"id\": \"{edge.Id}\", \"source\": \"{edge.SourceId}\", \"target\": \"{edge.TargetId}\", \"condition\": \"{EscapeTresString(edge.Condition)}\" }}");
            }
            subResources.Add("]");
        }
    }

    private static string EscapeTresString(string value)
    {
        if (string.IsNullOrEmpty(value)) return value;
        return value.Replace("\\", "\\\\").Replace("\"", "\\\"");
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
