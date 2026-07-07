using System.Windows;
using System.Windows.Controls;
using NarrativeForge.Core.DTOs;

namespace NarrativeForge.App.Controls;

public partial class LocationEditorControl : UserControl
{
    private LocationDto? _location;
    private bool _isUpdating;

    public static readonly DependencyProperty LocationProperty =
        DependencyProperty.Register(nameof(Location), typeof(LocationDto), typeof(LocationEditorControl),
            new PropertyMetadata(null, OnLocationChanged));

    public LocationDto? Location
    {
        get => (LocationDto?)GetValue(LocationProperty);
        set => SetValue(LocationProperty, value);
    }

    public event EventHandler? LocationUpdated;

    public LocationEditorControl()
    {
        InitializeComponent();
    }

    private static void OnLocationChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
    {
        if (d is LocationEditorControl control)
            control.BindLocation();
    }

    private void BindLocation()
    {
        _location = Location;
        var hasLocation = _location is not null;

        EmptyState.Visibility = hasLocation ? Visibility.Collapsed : Visibility.Visible;
        EditorScrollViewer.Visibility = hasLocation ? Visibility.Visible : Visibility.Collapsed;

        if (_location is null) return;

        _isUpdating = true;

        NameTextBox.Text = _location.Name;
        SyncTypeComboBox();
        DescriptionTextBox.Text = _location.Description;
        ConnectedToTextBox.Text = string.Join(Environment.NewLine, _location.ConnectedLocationIds);
        InhabitantsTextBox.Text = string.Join(Environment.NewLine, _location.Inhabitants);
        FactionsPresentTextBox.Text = string.Join(Environment.NewLine, _location.FactionsPresent);
        SignificanceTextBox.Text = _location.Significance;
        IsLockedCheckBox.IsChecked = _location.IsLocked;

        _isUpdating = false;

        NameTextBox.TextChanged += OnFieldChanged;
        DescriptionTextBox.TextChanged += OnFieldChanged;
        ConnectedToTextBox.TextChanged += OnFieldChanged;
        InhabitantsTextBox.TextChanged += OnFieldChanged;
        FactionsPresentTextBox.TextChanged += OnFieldChanged;
        SignificanceTextBox.TextChanged += OnFieldChanged;
        IsLockedCheckBox.Checked += OnFieldChanged;
        IsLockedCheckBox.Unchecked += OnFieldChanged;
    }

    private void SyncTypeComboBox()
    {
        if (_location is null) return;

        for (int i = 0; i < TypeComboBox.Items.Count; i++)
        {
            if (TypeComboBox.Items[i] is ComboBoxItem item &&
                string.Equals(item.Content?.ToString(), _location.Type, StringComparison.OrdinalIgnoreCase))
            {
                TypeComboBox.SelectedIndex = i;
                return;
            }
        }

        TypeComboBox.SelectedIndex = 0;
    }

    private void TypeComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_isUpdating || _location is null) return;
        if (TypeComboBox.SelectedItem is ComboBoxItem item && item.Content is string typeStr)
        {
            _location.Type = typeStr;
            LocationUpdated?.Invoke(this, EventArgs.Empty);
        }
    }

    private void OnFieldChanged(object sender, RoutedEventArgs e)
    {
        if (_isUpdating || _location is null) return;

        _location.Name = NameTextBox.Text;
        _location.Description = DescriptionTextBox.Text;
        _location.ConnectedLocationIds = ParseGuidList(ConnectedToTextBox.Text);
        _location.Inhabitants = ParseList(InhabitantsTextBox.Text);
        _location.FactionsPresent = ParseList(FactionsPresentTextBox.Text);
        _location.Significance = SignificanceTextBox.Text;
        _location.IsLocked = IsLockedCheckBox.IsChecked == true;

        LocationUpdated?.Invoke(this, EventArgs.Empty);
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
