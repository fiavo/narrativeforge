namespace NarrativeForge.Core.DTOs;

public class LocationDto
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public string Climate { get; set; } = string.Empty;
    public string Culture { get; set; } = string.Empty;
    public string Population { get; set; } = string.Empty;
    public List<string> NotableFeatures { get; set; } = [];
    public List<Guid> ConnectedLocationIds { get; set; } = [];
    public List<string> Inhabitants { get; set; } = [];
    public List<string> FactionsPresent { get; set; } = [];
    public string Significance { get; set; } = string.Empty;
    public bool IsLocked { get; set; } = false;
}

public class FactionDto
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public string Leader { get; set; } = string.Empty;
    public List<string> Goals { get; set; } = [];
    public string Territory { get; set; } = string.Empty;
    public List<Guid> MemberIds { get; set; } = [];
    public List<Guid> AllianceIds { get; set; } = [];
    public List<Guid> EnemyIds { get; set; } = [];
}

public class TimelineEventDto
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Date { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public List<Guid> ParticipantIds { get; set; } = [];
    public Guid? LocationId { get; set; }
    public List<string> Consequences { get; set; } = [];
    public int Importance { get; set; }
}

public class LoreEntryDto
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public string Category { get; set; } = string.Empty;
    public string Source { get; set; } = string.Empty;
    public List<Guid> RelatedEntityIds { get; set; } = [];
}

public class RelationshipDto
{
    public Guid Id { get; set; }
    public Guid SourceCharacterId { get; set; }
    public Guid TargetCharacterId { get; set; }
    public string Type { get; set; } = string.Empty;
    public int Strength { get; set; }
    public string Description { get; set; } = string.Empty;
    public List<string> History { get; set; } = [];
}

public class StoryBibleDto
{
    public Guid Id { get; set; }
    public Guid ProjectId { get; set; }
    public List<CharacterDto> Characters { get; set; } = [];
    public List<LocationDto> Locations { get; set; } = [];
    public List<FactionDto> Factions { get; set; } = [];
    public List<TimelineEventDto> TimelineEvents { get; set; } = [];
    public List<LoreEntryDto> LoreEntries { get; set; } = [];
    public List<RelationshipDto> Relationships { get; set; } = [];
    public string WorldSettings { get; set; } = string.Empty;
    public string MagicSystem { get; set; } = string.Empty;
    public string TechnologyLevel { get; set; } = string.Empty;
}

public class CreateLocationRequest
{
    public string Name { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Significance { get; set; } = string.Empty;
}

public class CreateFactionRequest
{
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public List<string> Goals { get; set; } = [];
}

public class CreateTimelineEventRequest
{
    public string Title { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Timestamp { get; set; } = string.Empty;
    public int Order { get; set; }
    public List<string> Consequences { get; set; } = [];
}

public class CreateLoreEntryRequest
{
    public string Title { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public string Category { get; set; } = string.Empty;
    public List<string> Tags { get; set; } = [];
}
