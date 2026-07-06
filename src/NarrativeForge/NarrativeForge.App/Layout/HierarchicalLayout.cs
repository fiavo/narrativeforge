namespace NarrativeForge.App.Layout;

public class HierarchicalLayout : IGraphLayout
{
    public string Name => "Hierarchical";
    public string Description => "Sugiyama-style hierarchical layout with layer-based positioning.";

    public double LayerSpacing { get; set; } = 120;
    public double NodeSpacing { get; set; } = 200;

    public void ComputeLayout(IList<GraphNode> nodes, IList<GraphEdge> edges)
    {
        if (nodes.Count == 0) return;

        var nodeMap = nodes.ToDictionary(n => n.Id);
        var children = edges.Where(e => nodeMap.ContainsKey(e.SourceId) && nodeMap.ContainsKey(e.TargetId))
            .GroupBy(e => e.SourceId)
            .ToDictionary(g => g.Key, g => g.Select(e => e.TargetId).ToList());
        var parentCount = nodes.ToDictionary(n => n.Id, _ => 0);
        foreach (var edge in edges)
        {
            if (parentCount.ContainsKey(edge.TargetId))
                parentCount[edge.TargetId]++;
        }

        var layers = AssignLayers(nodes, parentCount, children);
        OrderLayers(layers, children);
        var positions = PositionLayers(layers);

        var result = new List<GraphNode>();
        foreach (var (nodeId, pos) in positions)
        {
            result.Add(new GraphNode(nodeId, nodeMap[nodeId].Type, pos.X, pos.Y));
        }

        nodes.Clear();
        foreach (var n in result)
            nodes.Add(n);
    }

    private List<List<string>> AssignLayers(IList<GraphNode> nodes, Dictionary<string, int> parentCount, Dictionary<string, List<string>> children)
    {
        var layers = new List<List<string>>();
        var queue = new Queue<string>();
        var nodeLayer = new Dictionary<string, int>();

        foreach (var node in nodes)
        {
            if (parentCount[node.Id] == 0)
            {
                queue.Enqueue(node.Id);
                nodeLayer[node.Id] = 0;
            }
        }

        if (queue.Count == 0)
        {
            queue.Enqueue(nodes[0].Id);
            nodeLayer[nodes[0].Id] = 0;
        }

        while (queue.Count > 0)
        {
            var current = queue.Dequeue();
            var currentLayer = nodeLayer[current];

            while (layers.Count <= currentLayer)
                layers.Add(new List<string>());
            layers[currentLayer].Add(current);

            if (!children.ContainsKey(current)) continue;

            foreach (var child in children[current])
            {
                if (nodeLayer.ContainsKey(child)) continue;

                var childLayer = currentLayer + 1;
                nodeLayer[child] = childLayer;
                queue.Enqueue(child);
            }
        }

        foreach (var node in nodes)
        {
            if (!nodeLayer.ContainsKey(node.Id))
            {
                var lastLayer = layers.Count;
                layers.Add(new List<string> { node.Id });
                nodeLayer[node.Id] = lastLayer;
            }
        }

        return layers;
    }

    private void OrderLayers(List<List<string>> layers, Dictionary<string, List<string>> children)
    {
        for (int i = 1; i < layers.Count; i++)
        {
            var prevLayer = layers[i - 1];
            var prevPositions = new Dictionary<string, double>();
            for (int j = 0; j < prevLayer.Count; j++)
                prevPositions[prevLayer[j]] = j;

            layers[i].Sort((a, b) =>
            {
                double avgA = GetBarycenter(a, prevPositions, children);
                double avgB = GetBarycenter(b, prevPositions, children);
                return avgA.CompareTo(avgB);
            });
        }
    }

    private double GetBarycenter(string nodeId, Dictionary<string, double> prevPositions, Dictionary<string, List<string>> children)
    {
        double sum = 0;
        int count = 0;

        foreach (var (parentId, childList) in children)
        {
            if (childList.Contains(nodeId) && prevPositions.ContainsKey(parentId))
            {
                sum += prevPositions[parentId];
                count++;
            }
        }

        return count > 0 ? sum / count : 0;
    }

    private Dictionary<string, (double X, double Y)> PositionLayers(List<List<string>> layers)
    {
        var positions = new Dictionary<string, (double X, double Y)>();

        for (int i = 0; i < layers.Count; i++)
        {
            var layer = layers[i];
            double layerWidth = (layer.Count - 1) * NodeSpacing;
            double startX = -layerWidth / 2.0;

            for (int j = 0; j < layer.Count; j++)
            {
                positions[layer[j]] = (startX + j * NodeSpacing, i * LayerSpacing);
            }
        }

        return positions;
    }
}
