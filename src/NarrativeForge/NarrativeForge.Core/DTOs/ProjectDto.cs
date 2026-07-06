using NarrativeForge.Core.Enums;

namespace NarrativeForge.Core.DTOs;

public class ProjectDto
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public GameGenre Genre { get; set; }
    public List<GameGenre> SubGenres { get; set; } = [];
    public string TargetAudience { get; set; } = string.Empty;
    public string Tone { get; set; } = string.Empty;
    public List<string> Themes { get; set; } = [];
    public Guid? StoryBibleId { get; set; }
    public Dictionary<string, object> Settings { get; set; } = [];
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

public class CreateProjectRequest
{
    public string Name { get; set; } = string.Empty;
    public GameGenre Genre { get; set; }
    public List<GameGenre> SubGenres { get; set; } = [];
    public string TargetAudience { get; set; } = string.Empty;
    public string Tone { get; set; } = string.Empty;
    public List<string> Themes { get; set; } = [];
}
