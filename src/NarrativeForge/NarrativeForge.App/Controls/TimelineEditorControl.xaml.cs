using System.Windows;
using System.Windows.Controls;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Controls;

public partial class TimelineEditorControl : UserControl
{
    private TimelineEventDto? _event;
    private bool _isUpdating;

    public static readonly DependencyProperty EventProperty =
        DependencyProperty.Register(nameof(Event), typeof(TimelineEventDto), typeof(TimelineEditorControl),
            new PropertyMetadata(null, OnEventChanged));

    public TimelineEventDto? Event
    {
        get => (TimelineEventDto?)GetValue(EventProperty);
        set => SetValue(EventProperty, value);
    }

    public event EventHandler? EventUpdated;

    public TimelineEditorControl()
    {
        InitializeComponent();
    }

    private static void OnEventChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is TimelineEditorControl control)
            control.BindEvent();
    }

    private void BindEvent()
    {
        _event = Event;
        var hasEvent = _event is not null;

        EmptyState.Visibility = hasEvent ? Visibility.Collapsed : Visibility.Visible;
        EditorScrollViewer.Visibility = hasEvent ? Visibility.Visible : Visibility.Collapsed;

        if (_event is null) return;

        _isUpdating = true;

        TitleTextBox.Text = _event.Name;
        DescriptionTextBox.Text = _event.Description;
        DateTextBox.Text = _event.Date;
        SyncTypeComboBox();
        ParticipantsTextBox.Text = string.Join(Environment.NewLine, _event.ParticipantIds);
        LocationTextBox.Text = _event.LocationId?.ToString() ?? string.Empty;
        ConsequencesTextBox.Text = string.Join(Environment.NewLine, _event.Consequences);
        OrderTextBox.Text = _event.Importance.ToString();

        _isUpdating = false;

        TitleTextBox.TextChanged += OnFieldChanged;
        DescriptionTextBox.TextChanged += OnFieldChanged;
        DateTextBox.TextChanged += OnFieldChanged;
        ParticipantsTextBox.TextChanged += OnFieldChanged;
        LocationTextBox.TextChanged += OnFieldChanged;
        ConsequencesTextBox.TextChanged += OnFieldChanged;
        OrderTextBox.TextChanged += OnFieldChanged;
    }

    private void SyncTypeComboBox()
    {
        if (_event is null) return;

        for (int i = 0; i < TypeComboBox.Items.Count; i++)
        {
            if (TypeComboBox.Items[i] is ComboBoxItem item &&
                string.Equals(item.Content?.ToString(), _event.Type, StringComparison.OrdinalIgnoreCase))
            {
                TypeComboBox.SelectedIndex = i;
                return;
            }
        }

        TypeComboBox.SelectedIndex = 0;
    }

    private void TypeComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_isUpdating || _event is null) return;
        if (TypeComboBox.SelectedItem is ComboBoxItem item && item.Content is string typeStr)
        {
            _event.Type = typeStr;
            EventUpdated?.Invoke(this, EventArgs.Empty);
        }
    }

    private void OnFieldChanged(object sender, RoutedEventArgs e)
    {
        if (_isUpdating || _event is null) return;

        _event.Name = TitleTextBox.Text;
        _event.Description = DescriptionTextBox.Text;
        _event.Date = DateTextBox.Text;
        _event.ParticipantIds = ParseGuidList(ParticipantsTextBox.Text);
        _event.LocationId = Guid.TryParse(LocationTextBox.Text, out var locId) ? locId : null;
        _event.Consequences = ParseList(ConsequencesTextBox.Text);
        _event.Importance = int.TryParse(OrderTextBox.Text, out var order) ? order : 0;

        EventUpdated?.Invoke(this, EventArgs.Empty);
    }

    private static List<string> ParseList(string text)
    {
        return [.. text.Split(Environment.NewLine, StringSplitOptions.RemoveEmptyEntries)
                       .Select(l => l.Trim())
                       .Where(l => !string.IsNullOrEmpty(l))];
    }

    private static List<Guid> ParseGuidList(string text)
    {
        return [.. text.Split(Environment.NewLine, StringSplitOptions.RemoveEmptyEntries)
                       .Select(l => l.Trim())
                       .Where(l => !string.IsNullOrEmpty(l))
                       .Where(l => Guid.TryParse(l, out _))
                       .Select(l => Guid.Parse(l))];
    }
}
