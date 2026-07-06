using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;
using NarrativeForge.App.ViewModels;

namespace NarrativeForge.App.Controls;

public partial class GraphNodeControl : UserControl
{
    public static readonly DependencyProperty NodeProperty =
        DependencyProperty.Register(nameof(Node), typeof(GraphNodeViewModel), typeof(GraphNodeControl),
            new PropertyMetadata(null));

    public GraphNodeViewModel? Node
    {
        get => (GraphNodeViewModel?)GetValue(NodeProperty);
        set => SetValue(NodeProperty, value);
    }

    public GraphNodeControl()
    {
        InitializeComponent();
    }

    private Ellipse? _dragPort;

    private void Port_MouseLeftButtonDown(object sender, System.Windows.Input.MouseButtonEventArgs e)
    {
        if (sender is Ellipse port)
        {
            _dragPort = port;
            port.CaptureMouse();
            e.Handled = true;
        }
    }

    private void Port_MouseMove(object sender, System.Windows.Input.MouseEventArgs e)
    {
        if (_dragPort is not null && e.LeftButton == System.Windows.Input.MouseButtonState.Pressed)
        {
            var pos = e.GetPosition(Root);
            _dragPort.Margin = new Thickness(pos.X - 6, 0, 0, 0);
        }
    }

    private void Port_MouseLeftButtonUp(object sender, System.Windows.Input.MouseButtonEventArgs e)
    {
        if (_dragPort is not null)
        {
            _dragPort.ReleaseMouseCapture();
            _dragPort = null;
        }
    }
}
