using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Animation;
using NarrativeForge.App.ViewModels;

namespace NarrativeForge.App.Controls;

public static class LayoutAnimator
{
    public static Task AnimateLayout(GraphCanvas canvas, IReadOnlyList<GraphNodeViewModel> nodes)
    {
        if (canvas is null || nodes.Count == 0)
            return Task.CompletedTask;

        var tcs = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);

        var durationMs = Math.Min(500, 200 + nodes.Count * 10);
        var duration = new Duration(TimeSpan.FromMilliseconds(durationMs));
        var storyboard = new Storyboard();
        var pending = nodes.Count;

        foreach (var node in nodes)
        {
            var ctrl = FindNodeControl(canvas, node);
            if (ctrl is null)
            {
                pending--;
                continue;
            }

            var currentLeft = Canvas.GetLeft(ctrl);
            var currentTop = Canvas.GetTop(ctrl);
            var targetX = node.X;
            var targetY = node.Y;

            var xAnim = new DoubleAnimation(currentLeft, targetX, duration)
            {
                EasingFunction = new ExponentialEase { EasingMode = EasingMode.EaseOut, Exponent = 2 }
            };
            Storyboard.SetTarget(xAnim, ctrl);
            Storyboard.SetTargetProperty(xAnim, new PropertyPath("(Canvas.Left)"));
            storyboard.Children.Add(xAnim);

            var yAnim = new DoubleAnimation(currentTop, targetY, duration)
            {
                EasingFunction = new ExponentialEase { EasingMode = EasingMode.EaseOut, Exponent = 2 }
            };
            Storyboard.SetTarget(yAnim, ctrl);
            Storyboard.SetTargetProperty(yAnim, new PropertyPath("(Canvas.Top)"));
            storyboard.Children.Add(yAnim);
        }

        if (pending == 0)
            return Task.CompletedTask;

        storyboard.Completed += (_, _) => tcs.TrySetResult();
        storyboard.Freeze();
        storyboard.Begin();

        return tcs.Task;
    }

    private static GraphNodeControl? FindNodeControl(GraphCanvas canvas, GraphNodeViewModel node)
    {
        return canvas.Children.OfType<GraphNodeControl>().FirstOrDefault(c => c.Node == node);
    }
}
