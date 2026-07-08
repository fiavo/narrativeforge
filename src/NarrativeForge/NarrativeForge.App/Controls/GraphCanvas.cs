using System.Collections.ObjectModel;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;
using NarrativeForge.App.ViewModels;

namespace NarrativeForge.App.Controls;

public class GraphCanvas : Canvas
{
    public event EventHandler<FileDroppedEventArgs>? FileDropped;

    private readonly ScaleTransform _scaleTransform = new();
    private readonly TranslateTransform _translateTransform = new();
    private readonly TransformGroup _transformGroup;
    private readonly Canvas _edgeLayer;
    private Point _lastPanPosition;
    private bool _isPanning;
    private bool _isDraggingNode;
    private GraphNodeViewModel? _draggedNode;
    private Point _dragOffset;

    public static readonly DependencyProperty NodesProperty =
        DependencyProperty.Register(nameof(Nodes), typeof(ObservableCollection<GraphNodeViewModel>), typeof(GraphCanvas),
            new PropertyMetadata(null, OnNodesChanged));

    public static readonly DependencyProperty EdgesProperty =
        DependencyProperty.Register(nameof(Edges), typeof(ObservableCollection<GraphEdgeViewModel>), typeof(GraphCanvas),
            new PropertyMetadata(null, OnEdgesChanged));

    public static readonly DependencyProperty SelectedNodeProperty =
        DependencyProperty.Register(nameof(SelectedNode), typeof(GraphNodeViewModel), typeof(GraphCanvas),
            new FrameworkPropertyMetadata(null, FrameworkPropertyMetadataOptions.BindsTwoWayByDefault, OnSelectedNodeChanged));

    public static readonly DependencyProperty ZoomProperty =
        DependencyProperty.Register(nameof(Zoom), typeof(double), typeof(GraphCanvas),
            new PropertyMetadata(1.0, OnZoomChanged));

    public ObservableCollection<GraphNodeViewModel>? Nodes
    {
        get => (ObservableCollection<GraphNodeViewModel>?)GetValue(NodesProperty);
        set => SetValue(NodesProperty, value);
    }

    public ObservableCollection<GraphEdgeViewModel>? Edges
    {
        get => (ObservableCollection<GraphEdgeViewModel>?)GetValue(EdgesProperty);
        set => SetValue(EdgesProperty, value);
    }

    public GraphNodeViewModel? SelectedNode
    {
        get => (GraphNodeViewModel?)GetValue(SelectedNodeProperty);
        set => SetValue(SelectedNodeProperty, value);
    }

    public double Zoom
    {
        get => (double)GetValue(ZoomProperty);
        set => SetValue(ZoomProperty, value);
    }

    public GraphCanvas()
    {
        _transformGroup = new TransformGroup();
        _transformGroup.Children.Add(_scaleTransform);
        _transformGroup.Children.Add(_translateTransform);
        RenderTransform = _transformGroup;
        ClipToBounds = true;
        Background = Brushes.Transparent;

        _edgeLayer = new Canvas { IsHitTestVisible = false };
        _edgeLayer.RenderTransform = _transformGroup;
        Children.Add(_edgeLayer);

        AllowDrop = true;
        MouseWheel += OnMouseWheel;
        MouseLeftButtonDown += OnMouseLeftButtonDown;
        MouseLeftButtonUp += OnMouseLeftButtonUp;
        MouseMove += OnMouseMove;
        MouseRightButtonDown += OnMouseRightButtonDown;
        MouseRightButtonUp += OnMouseRightButtonUp;
        Drop += OnDrop;
        DragOver += OnDragOver;
        SizeChanged += (_, _) => DrawEdges();
    }

    private static void OnNodesChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is GraphCanvas canvas)
        {
            if (e.OldValue is ObservableCollection<GraphNodeViewModel> oldNodes)
            {
                oldNodes.CollectionChanged -= canvas.OnNodesCollectionChanged;
                foreach (var node in oldNodes)
                    node.PropertyChanged -= canvas.OnNodePropertyChanged;
            }
            if (e.NewValue is ObservableCollection<GraphNodeViewModel> newNodes)
            {
                newNodes.CollectionChanged += canvas.OnNodesCollectionChanged;
                foreach (var node in newNodes)
                    node.PropertyChanged += canvas.OnNodePropertyChanged;
                canvas.RebuildNodes();
            }
        }
    }

    private static void OnEdgesChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is GraphCanvas canvas)
        {
            if (e.OldValue is ObservableCollection<GraphEdgeViewModel> oldEdges)
                oldEdges.CollectionChanged -= canvas.OnEdgesCollectionChanged;
            if (e.NewValue is ObservableCollection<GraphEdgeViewModel> newEdges)
            {
                newEdges.CollectionChanged += canvas.OnEdgesCollectionChanged;
                canvas.DrawEdges();
            }
        }
    }

    private static void OnSelectedNodeChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is GraphCanvas canvas && e.OldValue is GraphNodeViewModel oldNode)
            oldNode.IsSelected = false;
        if (e.NewValue is GraphNodeViewModel newNode)
            newNode.IsSelected = true;
    }

    private static void OnZoomChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is GraphCanvas canvas)
            canvas._scaleTransform.ScaleX = canvas._scaleTransform.ScaleY = (double)e.NewValue;
    }

    private void OnNodesCollectionChanged(object? sender, System.Collections.Specialized.NotifyCollectionChangedEventArgs e)
    {
        if (e.OldItems != null)
            foreach (GraphNodeViewModel node in e.OldItems)
                node.PropertyChanged -= OnNodePropertyChanged;
        if (e.NewItems != null)
            foreach (GraphNodeViewModel node in e.NewItems)
                node.PropertyChanged += OnNodePropertyChanged;
        RebuildNodes();
        DrawEdges();
    }

    private void OnEdgesCollectionChanged(object? sender, System.Collections.Specialized.NotifyCollectionChangedEventArgs e)
    {
        DrawEdges();
    }

    private void OnNodePropertyChanged(object? sender, System.ComponentModel.PropertyChangedEventArgs e)
    {
        if (e.PropertyName is nameof(GraphNodeViewModel.X) or nameof(GraphNodeViewModel.Y))
            DrawEdges();
    }

    private void RebuildNodes()
    {
        var existing = Children.OfType<GraphNodeControl>().ToList();
        foreach (var ctrl in existing)
            Children.Remove(ctrl);

        if (Nodes is null) return;

        foreach (var node in Nodes)
        {
            var ctrl = new GraphNodeControl { Node = node };
            Canvas.SetLeft(ctrl, node.X);
            Canvas.SetTop(ctrl, node.Y);
            ctrl.MouseLeftButtonDown += NodeControl_MouseLeftButtonDown;
            Children.Add(ctrl);
        }
    }

    private void NodeControl_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (sender is GraphNodeControl { Node: { } node })
        {
            SelectedNode = node;
            _isDraggingNode = true;
            _draggedNode = node;
            _dragOffset = e.GetPosition(this);
            _dragOffset.X -= node.X;
            _dragOffset.Y -= node.Y;
            e.Handled = true;
        }
    }

    private void OnMouseWheel(object sender, MouseWheelEventArgs e)
    {
        var pos = e.GetPosition(this);
        var oldScale = _scaleTransform.ScaleX;
        var factor = e.Delta > 0 ? 1.1 : 1.0 / 1.1;
        var newScale = Math.Clamp(oldScale * factor, 0.1, 5.0);

        var relativeX = pos.X - _translateTransform.X;
        var relativeY = pos.Y - _translateTransform.Y;

        _scaleTransform.ScaleX = _scaleTransform.ScaleY = newScale;
        Zoom = newScale;

        _translateTransform.X = pos.X - relativeX * (newScale / oldScale);
        _translateTransform.Y = pos.Y - relativeY * (newScale / oldScale);

        DrawEdges();
    }

    private void OnMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (_isDraggingNode) return;
        SelectedNode = null;
    }

    private void OnMouseLeftButtonUp(object sender, MouseButtonEventArgs e)
    {
        _isDraggingNode = false;
        _draggedNode = null;
    }

    private void OnMouseRightButtonDown(object sender, MouseButtonEventArgs e)
    {
        _isPanning = true;
        _lastPanPosition = e.GetPosition(this);
        CaptureMouse();
    }

    private void OnMouseRightButtonUp(object sender, MouseButtonEventArgs e)
    {
        _isPanning = false;
        ReleaseMouseCapture();
    }

    private void OnMouseMove(object sender, MouseEventArgs e)
    {
        if (_isDraggingNode && _draggedNode is { } node)
        {
            var pos = e.GetPosition(this);
            node.X = pos.X - _dragOffset.X;
            node.Y = pos.Y - _dragOffset.Y;
            var ctrl = FindNodeControl(node);
            if (ctrl is not null)
            {
                Canvas.SetLeft(ctrl, node.X);
                Canvas.SetTop(ctrl, node.Y);
            }
            DrawEdges();
        }
        else if (_isPanning)
        {
            var pos = e.GetPosition(this);
            _translateTransform.X += pos.X - _lastPanPosition.X;
            _translateTransform.Y += pos.Y - _lastPanPosition.Y;
            _lastPanPosition = pos;
            DrawEdges();
        }
    }

    private GraphNodeControl? FindNodeControl(GraphNodeViewModel node)
    {
        return Children.OfType<GraphNodeControl>().FirstOrDefault(c => c.Node == node);
    }

    private void DrawEdges()
    {
        _edgeLayer.Children.Clear();
        if (Edges is null || Nodes is null) return;

        foreach (var edge in Edges)
        {
            var source = Nodes.FirstOrDefault(n => n.Id == edge.SourceId);
            var target = Nodes.FirstOrDefault(n => n.Id == edge.TargetId);
            if (source is null || target is null) continue;

            var sourceCtrl = FindNodeControl(source);
            var targetCtrl = FindNodeControl(target);
            if (sourceCtrl is null || targetCtrl is null) continue;

            var sourceCenter = new Point(source.X + sourceCtrl.ActualWidth / 2, source.Y + sourceCtrl.ActualHeight);
            var targetCenter = new Point(target.X + targetCtrl.ActualWidth / 2, target.Y);

            var dx = Math.Abs(targetCenter.X - sourceCenter.X) * 0.5;
            dx = Math.Max(dx, 50);

            var pathGeometry = new PathGeometry();
            var figure = new PathFigure { StartPoint = sourceCenter };
            figure.Segments.Add(new BezierSegment(
                new Point(sourceCenter.X, sourceCenter.Y + dx),
                new Point(targetCenter.X, targetCenter.Y - dx),
                targetCenter,
                true));
            pathGeometry.Figures.Add(figure);

            var path = new Path
            {
                Stroke = new SolidColorBrush((Color)ColorConverter.ConvertFromString(edge.EdgeColor)),
                StrokeThickness = 2,
                Data = pathGeometry
            };
            _edgeLayer.Children.Add(path);

            DrawArrowHead(targetCenter, sourceCenter, edge.EdgeColor);
        }
    }

    private void DrawArrowHead(Point tip, Point from, string color)
    {
        var angle = Math.Atan2(tip.Y - from.Y, tip.X - from.X);
        const double arrowLength = 12;
        const double arrowAngle = Math.PI / 6;

        var p1 = new Point(
            tip.X - arrowLength * Math.Cos(angle - arrowAngle),
            tip.Y - arrowLength * Math.Sin(angle - arrowAngle));
        var p2 = new Point(
            tip.X - arrowLength * Math.Cos(angle + arrowAngle),
            tip.Y - arrowLength * Math.Sin(angle + arrowAngle));

        var arrowGeometry = new StreamGeometry();
        using (var ctx = arrowGeometry.Open())
        {
            ctx.BeginFigure(tip, true, true);
            ctx.LineTo(p1, true, false);
            ctx.LineTo(p2, true, false);
        }
        arrowGeometry.Freeze();

        var arrow = new Path
        {
            Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString(color)),
            Data = arrowGeometry
        };
        _edgeLayer.Children.Add(arrow);
    }

    private void OnDragOver(object sender, DragEventArgs e)
    {
        e.Effects = DragDropEffects.None;
        if (e.Data.GetDataPresent(DataFormats.FileDrop))
        {
            var files = e.Data.GetData(DataFormats.FileDrop) as string[];
            if (files is { Length: > 0 })
            {
                var ext = System.IO.Path.GetExtension(files[0]).ToLowerInvariant();
                if (ext is ".ink" or ".yarn")
                    e.Effects = DragDropEffects.Copy;
            }
        }
        e.Handled = true;
    }

    private void OnDrop(object sender, DragEventArgs e)
    {
        if (!e.Data.GetDataPresent(DataFormats.FileDrop)) return;

        var files = e.Data.GetData(DataFormats.FileDrop) as string[];
        if (files is null or { Length: 0 }) return;

        foreach (var file in files)
        {
            var ext = System.IO.Path.GetExtension(file).ToLowerInvariant();
            if (ext is ".ink" or ".yarn")
            {
                var content = System.IO.File.ReadAllText(file);
                var format = ext == ".ink" ? "ink" : "yarn";
                FileDropped?.Invoke(this, new FileDroppedEventArgs(file, content, format));
            }
        }
        e.Handled = true;
    }

    public void ZoomToFit()
    {
        if (Nodes is null || Nodes.Count == 0)
        {
            _scaleTransform.ScaleX = _scaleTransform.ScaleY = 1.0;
            _translateTransform.X = _translateTransform.Y = 0;
            Zoom = 1.0;
            return;
        }

        var padding = 50;
        var minX = Nodes.Min(n => n.X);
        var minY = Nodes.Min(n => n.Y);
        var maxX = Nodes.Max(n => n.X + 200);
        var maxY = Nodes.Max(n => n.Y + 120);

        var contentWidth = maxX - minX + padding * 2;
        var contentHeight = maxY - minY + padding * 2;

        var scaleX = ActualWidth / contentWidth;
        var scaleY = ActualHeight / contentHeight;
        var scale = Math.Min(scaleX, scaleY);
        scale = Math.Clamp(scale, 0.1, 5.0);

        _scaleTransform.ScaleX = _scaleTransform.ScaleY = scale;
        Zoom = scale;

        _translateTransform.X = (ActualWidth - contentWidth * scale) / 2 - (minX - padding) * scale;
        _translateTransform.Y = (ActualHeight - contentHeight * scale) / 2 - (minY - padding) * scale;

        DrawEdges();
    }
}

public class FileDroppedEventArgs : EventArgs
{
    public string FilePath { get; }
    public string Content { get; }
    public string Format { get; }

    public FileDroppedEventArgs(string filePath, string content, string format)
    {
        FilePath = filePath;
        Content = content;
        Format = format;
    }
}
