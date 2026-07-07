namespace NarrativeForge.App.Layout;

public class ForceDirectedLayout : IGraphLayout
{
    public string Name => "Force-Directed";
    public string Description => "Spring physics layout with Coulomb repulsion, Hooke attraction, and gravity.";

    public int MaxIterations { get; set; } = 200;
    public double RepulsionStrength { get; set; } = 5000;
    public double AttractionStrength { get; set; } = 0.01;
    public double Gravity { get; set; } = 0.1;
    public double Damping { get; set; } = 0.9;

    public void ComputeLayout(IList<GraphNode> nodes, IList<GraphEdge> edges)
    {
        if (nodes.Count == 0) return;
        if (nodes.Count == 1)
        {
            var single = nodes[0];
            nodes.Clear();
            nodes.Add(new GraphNode(single.Id, single.Type, 0, 0));
            return;
        }

        var positions = new Dictionary<string, (double X, double Y)>();
        var velocities = new Dictionary<string, (double VX, double VY)>();
        var rng = new Random(42);

        foreach (var node in nodes)
        {
            positions[node.Id] = (rng.NextDouble() * 100 - 50, rng.NextDouble() * 100 - 50);
            velocities[node.Id] = (0, 0);
        }

        var nodeMap = nodes.ToDictionary(n => n.Id);
        var edgeSet = edges
            .Where(e => nodeMap.ContainsKey(e.SourceId) && nodeMap.ContainsKey(e.TargetId))
            .Select(e => (e.SourceId, e.TargetId))
            .ToList();

        for (int iter = 0; iter < MaxIterations; iter++)
        {
            var forces = new Dictionary<string, (double FX, double FY)>();
            foreach (var node in nodes)
                forces[node.Id] = (0, 0);

            var ids = nodes.Select(n => n.Id).ToList();
            for (int i = 0; i < ids.Count; i++)
            {
                for (int j = i + 1; j < ids.Count; j++)
                {
                    var (x1, y1) = positions[ids[i]];
                    var (x2, y2) = positions[ids[j]];
                    double dx = x2 - x1;
                    double dy = y2 - y1;
                    double distSq = dx * dx + dy * dy;
                    if (distSq < 1) distSq = 1;
                    double dist = Math.Sqrt(distSq);
                    double force = RepulsionStrength / distSq;
                    double fx = (dx / dist) * force;
                    double fy = (dy / dist) * force;

                    forces[ids[i]] = (forces[ids[i]].FX - fx, forces[ids[i]].FY - fy);
                    forces[ids[j]] = (forces[ids[j]].FX + fx, forces[ids[j]].FY + fy);
                }
            }

            foreach (var (src, tgt) in edgeSet)
            {
                var (x1, y1) = positions[src];
                var (x2, y2) = positions[tgt];
                double dx = x2 - x1;
                double dy = y2 - y1;
                double dist = Math.Sqrt(dx * dx + dy * dy);
                if (dist < 1) dist = 1;
                double force = AttractionStrength * dist;
                double fx = (dx / dist) * force;
                double fy = (dy / dist) * force;

                forces[src] = (forces[src].FX + fx, forces[src].FY + fy);
                forces[tgt] = (forces[tgt].FX - fx, forces[tgt].FY - fy);
            }

            foreach (var node in nodes)
            {
                var (x, y) = positions[node.Id];
                forces[node.Id] = (forces[node.Id].FX - Gravity * x, forces[node.Id].FY - Gravity * y);
            }

            double totalMovement = 0;
            foreach (var node in nodes)
            {
                var (vx, vy) = velocities[node.Id];
                var (fx, fy) = forces[node.Id];
                vx = (vx + fx) * Damping;
                vy = (vy + fy) * Damping;
                velocities[node.Id] = (vx, vy);

                var (x, y) = positions[node.Id];
                x += vx;
                y += vy;
                positions[node.Id] = (x, y);

                totalMovement += Math.Abs(vx) + Math.Abs(vy);
            }

            if (totalMovement < 0.1)
                break;
        }

        var result = new List<GraphNode>();
        foreach (var node in nodes)
        {
            var (x, y) = positions[node.Id];
            result.Add(new GraphNode(node.Id, node.Type, x, y));
        }

        nodes.Clear();
        foreach (var n in result)
            nodes.Add(n);
    }
}
