using NarrativeForge.Core.Enums;

namespace NarrativeForge.Core.DTOs;

public class PersonalityDto
{
    public List<string> Traits { get; set; } = [];
    public List<string> Values { get; set; } = [];
    public List<string> Fears { get; set; } = [];
    public List<string> Desires { get; set; } = [];
}

public class CharacterDto
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Alias { get; set; } = string.Empty;
    public CharacterRole Role { get; set; }
    public PersonalityDto Personality { get; set; } = new();
    public string Backstory { get; set; } = string.Empty;
    public string Motivation { get; set; } = string.Empty;
    public List<string> Goals { get; set; } = [];
    public List<string> Fears { get; set; } = [];
    public Dictionary<Guid, string> Relationships { get; set; } = [];
    public CharacterArcDto Arc { get; set; } = new();
    public string DialogueStyle { get; set; } = string.Empty;
    public string Appearance { get; set; } = string.Empty;
    public bool IsAlive { get; set; } = true;
    public bool IsLocked { get; set; } = false;
}

public class CharacterArcDto
{
    public string StartState { get; set; } = string.Empty;
    public string EndState { get; set; } = string.Empty;
    public List<string> TurningPoints { get; set; } = [];
}
