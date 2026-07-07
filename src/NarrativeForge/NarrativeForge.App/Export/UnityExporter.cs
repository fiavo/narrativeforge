using System.Text;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Export;

public class UnityExporter : IExporter
{
    public string Name => "Unity";
    public string FileExtension => ".asset";
    public string Description => "Exports dialogue trees as Unity YAML ScriptableObjects";
    public string Category => "Game Engine";

    public bool CanExport(ExportRequest request)
    {
        return request.DialogueTree != null || request.QuestGraph != null;
    }

    public Task<ExportResult> ExportAsync(ExportRequest request, CancellationToken cancellationToken = default)
    {
        if (request.DialogueTree is null && request.QuestGraph is null)
            return Task.FromResult(new ExportResult { Success = false, Error = "No dialogue tree or quest graph provided." });

        var sb = new StringBuilder();
        sb.AppendLine("%YAML 1.1");
        sb.AppendLine("%TAG !u! tag:unity3d.com,2011:");
        sb.AppendLine("--- !u!114 &11400000");
        sb.AppendLine("MonoBehaviour:");
        sb.AppendLine("  m_ObjectHideFlags: 0");
        sb.AppendLine("  m_CorrespondingSourceObject: {fileID: 0}");
        sb.AppendLine("  m_PrefabInstance: {fileID: 0}");
        sb.AppendLine("  m_PrefabAsset: {fileID: 0}");
        sb.AppendLine("  m_GameObject: {fileID: 0}");
        sb.AppendLine("  m_Enabled: 1");
        sb.AppendLine("  m_EditorHideFlags: 0");
        sb.AppendLine("  m_Script: {fileID: 0}");
        sb.AppendLine($"  m_Name: \"{EscapeYaml(request.ProjectName)}\"");
        sb.AppendLine("  m_EditorClassIdentifier: NarrativeForge.DialogueData");

        if (request.DialogueTree is not null)
        {
            cancellationToken.ThrowIfCancellationRequested();
            WriteDialogueTreeYaml(sb, request.DialogueTree);
        }

        if (request.QuestGraph is not null)
        {
            cancellationToken.ThrowIfCancellationRequested();
            WriteQuestGraphYaml(sb, request.QuestGraph);
        }

        if (request.Nodes.Count > 0 || request.Edges.Count > 0)
        {
            cancellationToken.ThrowIfCancellationRequested();
            WriteGraphYaml(sb, request.Nodes, request.Edges);
        }

        var filename = $"{SanitizeName(request.ProjectName)}_dialogue.asset";
        return Task.FromResult(new ExportResult
        {
            Success = true,
            Content = sb.ToString(),
            Filename = filename
        });
    }

    private static void WriteDialogueTreeYaml(StringBuilder sb, DialogueTreeDto tree)
    {
        sb.AppendLine("  dialogueTree:");
        sb.AppendLine($"    name: \"{EscapeYaml(tree.Name)}\"");
        sb.AppendLine($"    startNodeId: \"{tree.StartNodeId}\"");
        sb.AppendLine($"    nodeCount: {tree.Nodes.Count}");
        sb.AppendLine($"    edgeCount: {tree.Edges.Count}");

        if (tree.Nodes.Count > 0)
        {
            sb.AppendLine("    nodes:");
            foreach (var node in tree.Nodes)
            {
                WriteNodeYaml(sb, node, 6);
            }
        }

        if (tree.Edges.Count > 0)
        {
            sb.AppendLine("    edges:");
            foreach (var edge in tree.Edges)
            {
                sb.AppendLine($"      - id: \"{edge.Id}\"");
                sb.AppendLine($"        sourceId: \"{edge.SourceId}\"");
                sb.AppendLine($"        targetId: \"{edge.TargetId}\"");
                sb.AppendLine($"        condition: \"{EscapeYaml(edge.Condition)}\"");
            }
        }
    }

    private static void WriteQuestGraphYaml(StringBuilder sb, QuestGraphDto quest)
    {
        sb.AppendLine("  questGraph:");
        sb.AppendLine($"    name: \"{EscapeYaml(quest.Name)}\"");
        sb.AppendLine($"    startNodeId: \"{quest.StartNodeId}\"");
        sb.AppendLine($"    nodeCount: {quest.Nodes.Count}");
        sb.AppendLine($"    edgeCount: {quest.Edges.Count}");

        if (quest.Nodes.Count > 0)
        {
            sb.AppendLine("    nodes:");
            foreach (var node in quest.Nodes)
            {
                WriteNodeYaml(sb, node, 6);
            }
        }

        if (quest.Edges.Count > 0)
        {
            sb.AppendLine("    edges:");
            foreach (var edge in quest.Edges)
            {
                sb.AppendLine($"      - id: \"{edge.Id}\"");
                sb.AppendLine($"        sourceId: \"{edge.SourceId}\"");
                sb.AppendLine($"        targetId: \"{edge.TargetId}\"");
                sb.AppendLine($"        condition: \"{EscapeYaml(edge.Condition)}\"");
            }
        }
    }

    private static void WriteGraphYaml(StringBuilder sb, List<GraphNodeDto> nodes, List<GraphEdgeDto> edges)
    {
        if (nodes.Count > 0)
        {
            sb.AppendLine("  nodes:");
            foreach (var node in nodes)
            {
                WriteNodeYaml(sb, node, 4);
            }
        }

        if (edges.Count > 0)
        {
            sb.AppendLine("  edges:");
            foreach (var edge in edges)
            {
                sb.AppendLine($"    - id: \"{edge.Id}\"");
                sb.AppendLine($"      sourceId: \"{edge.SourceId}\"");
                sb.AppendLine($"      targetId: \"{edge.TargetId}\"");
                sb.AppendLine($"      condition: \"{EscapeYaml(edge.Condition)}\"");
            }
        }
    }

    private static void WriteNodeYaml(StringBuilder sb, GraphNodeDto node, int indent)
    {
        var pad = new string(' ', indent);
        sb.AppendLine($"{pad}- id: \"{node.Id}\"");
        sb.AppendLine($"{pad}  type: \"{EscapeYaml(node.Type)}\"");
        sb.AppendLine($"{pad}  title: \"{EscapeYaml(node.Title)}\"");
        sb.AppendLine($"{pad}  content: \"{EscapeYaml(node.Content)}\"");
        sb.AppendLine($"{pad}  x: {node.X}");
        sb.AppendLine($"{pad}  y: {node.Y}");

        if (node.Choices.Count > 0)
        {
            sb.AppendLine($"{pad}  choices:");
            foreach (var choice in node.Choices)
            {
                sb.AppendLine($"{pad}    - id: \"{choice.Id}\"");
                sb.AppendLine($"{pad}      text: \"{EscapeYaml(choice.Text)}\"");
                sb.AppendLine($"{pad}      nextNodeId: \"{choice.NextNodeId}\"");
                sb.AppendLine($"{pad}      condition: \"{EscapeYaml(choice.Condition)}\"");
            }
        }

        if (node.Objectives.Count > 0)
        {
            sb.AppendLine($"{pad}  objectives:");
            foreach (var obj in node.Objectives)
            {
                sb.AppendLine($"{pad}    - id: \"{obj.Id}\"");
                sb.AppendLine($"{pad}      description: \"{EscapeYaml(obj.Description)}\"");
                sb.AppendLine($"{pad}      type: \"{EscapeYaml(obj.Type)}\"");
                sb.AppendLine($"{pad}      target: \"{EscapeYaml(obj.Target)}\"");
            }
        }

        if (node.VariablesSet.Count > 0)
        {
            sb.AppendLine($"{pad}  variablesSet:");
            foreach (var v in node.VariablesSet)
            {
                sb.AppendLine($"{pad}    - key: \"{EscapeYaml(v.Key)}\"");
                sb.AppendLine($"{pad}      value: \"{EscapeYaml(v.Value)}\"");
            }
        }
    }

    private static string EscapeYaml(string value)
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
