using System.Text.Json;

const int PipelineTileZoom = 8;

var root = args.Length > 0
    ? Path.GetFullPath(args[0])
    : FindProjectRoot(Directory.GetCurrentDirectory());

var publicData = Path.Combine(root, "public", "data");
var outputDir = Path.Combine(publicData, "pipelines");
var tileRoot = Path.Combine(publicData, "pipeline_tiles");
Directory.CreateDirectory(outputDir);
if (Directory.Exists(tileRoot)) Directory.Delete(tileRoot, recursive: true);
Directory.CreateDirectory(tileRoot);

var index = new PipelineIndex
{
    Version = 2,
    GeneratedAt = DateTimeOffset.UtcNow.ToString("O"),
};

SplitGeoJson(
    sourcePath: Path.Combine(publicData, "aer_feeder_pipelines.geojson"),
    projectRoot: root,
    outputDir,
    tileRoot,
    filePrefix: "aer_feeder",
    propertyName: "substance",
    keyMap: new Dictionary<string, string>(StringComparer.Ordinal)
    {
        ["Oil-Well Effluent"] = "pipe-oilwell",
        ["Crude Oil"] = "pipe-crude",
        ["HVP Products"] = "pipe-hvp",
        ["LVP Products"] = "pipe-lvp",
        ["Condensate"] = "pipe-condensate",
        ["Hydrocarbon Diluents"] = "pipe-diluent",
    },
    skipInactiveInstallations: false,
    buildLineTiles: true,
    target: index.LineCategories);

SplitGeoJson(
    sourcePath: Path.Combine(publicData, "aer_pipeline_installations.geojson"),
    projectRoot: root,
    outputDir,
    tileRoot: null,
    filePrefix: "aer_install",
    propertyName: "type",
    keyMap: new Dictionary<string, string>(StringComparer.Ordinal)
    {
        ["Pump Station"] = "inst-pump",
        ["Compressor Station"] = "inst-compressor",
        ["Oil Terminal"] = "inst-terminal",
        ["Tank Farm"] = "inst-terminal",
        ["Meter Station"] = "inst-meter",
        ["Regulator Station"] = "inst-meter",
        ["Meter Regulator Stn."] = "inst-meter",
        ["Line Heater"] = "inst-meter",
    },
    skipInactiveInstallations: true,
    buildLineTiles: false,
    target: index.InstallationCategories);

var indexPath = Path.Combine(publicData, "aer_pipeline_index.json");
WriteJson(indexPath, writer =>
{
    writer.WriteStartObject();
    writer.WriteNumber("version", index.Version);
    writer.WriteString("generated_at", index.GeneratedAt);
    WriteIndexGroup(writer, "line_categories", index.LineCategories);
    WriteIndexGroup(writer, "installation_categories", index.InstallationCategories);
    writer.WriteEndObject();
});

Console.WriteLine($"Wrote {Relative(root, indexPath)}");
foreach (var item in index.LineCategories.OrderBy(x => x.Key))
{
    var tileNote = item.Value.TileCount is > 0
        ? $", {item.Value.TileCount:N0} tiles, {item.Value.TileBytes.GetValueOrDefault() / 1024d / 1024d:N2} MB tiled"
        : "";
    Console.WriteLine($"{item.Key}: {item.Value.Count:N0} features, {item.Value.Bytes / 1024d / 1024d:N2} MB{tileNote}");
}
foreach (var item in index.InstallationCategories.OrderBy(x => x.Key))
{
    Console.WriteLine($"{item.Key}: {item.Value.Count:N0} features, {item.Value.Bytes / 1024d / 1024d:N2} MB");
}

static void SplitGeoJson(
    string sourcePath,
    string projectRoot,
    string outputDir,
    string? tileRoot,
    string filePrefix,
    string propertyName,
    IReadOnlyDictionary<string, string> keyMap,
    bool skipInactiveInstallations,
    bool buildLineTiles,
    Dictionary<string, PipelineIndexEntry> target)
{
    using var doc = JsonDocument.Parse(File.ReadAllBytes(sourcePath));
    var groups = keyMap.Values.Distinct(StringComparer.Ordinal).ToDictionary(
        key => key,
        _ => new List<JsonElement>(),
        StringComparer.Ordinal);

    foreach (var feature in doc.RootElement.GetProperty("features").EnumerateArray())
    {
        var properties = feature.GetProperty("properties");
        if (skipInactiveInstallations
            && properties.TryGetProperty("status", out var statusElement)
            && IsInactive(statusElement.GetString()))
        {
            continue;
        }

        if (!properties.TryGetProperty(propertyName, out var valueElement)) continue;
        var value = valueElement.GetString();
        if (value is null || !keyMap.TryGetValue(value, out var key)) continue;
        groups[key].Add(feature.Clone());
    }

    foreach (var (key, features) in groups)
    {
        var path = Path.Combine(outputDir, $"{filePrefix}_{key}.geojson");
        WriteFeatureCollection(path, features);

        var entry = new PipelineIndexEntry(
            Path: Relative(projectRoot, path),
            Count: features.Count,
            Bytes: new FileInfo(path).Length);

        if (buildLineTiles && tileRoot is not null)
        {
            var tileDir = Path.Combine(tileRoot, key);
            var summary = WriteLineTiles(features, tileDir, PipelineTileZoom);
            entry = entry with
            {
                TileTemplate = Relative(projectRoot, Path.Combine(tileDir, PipelineTileZoom.ToString(), "{x}", "{y}.geojson")),
                TileZoom = PipelineTileZoom,
                TileCount = summary.TileCount,
                TileBytes = summary.Bytes,
                TileKeys = summary.TileKeys,
            };
        }

        target[key] = entry;
    }
}

static TileSummary WriteLineTiles(IReadOnlyList<JsonElement> features, string categoryDir, int zoom)
{
    var perTile = new Dictionary<TileCoord, List<TileFeature>>();

    foreach (var feature in features)
    {
        if (!feature.TryGetProperty("geometry", out var geometry)) continue;
        if (!feature.TryGetProperty("properties", out var properties)) continue;

        var linesByTile = new Dictionary<TileCoord, List<GeoLine>>();
        VisitLineStrings(geometry, line =>
        {
            for (var i = 1; i < line.Count; i++)
            {
                AddSegmentToTiles(line[i - 1], line[i], zoom, linesByTile);
            }
        });

        foreach (var (coord, lines) in linesByTile)
        {
            if (!perTile.TryGetValue(coord, out var tileFeatures))
            {
                tileFeatures = [];
                perTile[coord] = tileFeatures;
            }
            tileFeatures.Add(new TileFeature(properties.Clone(), lines));
        }
    }

    long bytes = 0;
    var tileKeys = new List<string>();
    foreach (var (coord, tileFeatures) in perTile.OrderBy(x => x.Key.X).ThenBy(x => x.Key.Y))
    {
        var path = Path.Combine(categoryDir, coord.Z.ToString(), coord.X.ToString(), $"{coord.Y}.geojson");
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        WriteJson(path, writer =>
        {
            writer.WriteStartObject();
            writer.WriteString("type", "FeatureCollection");
            writer.WritePropertyName("features");
            writer.WriteStartArray();
            foreach (var tileFeature in tileFeatures)
            {
                writer.WriteStartObject();
                writer.WriteString("type", "Feature");
                writer.WritePropertyName("properties");
                tileFeature.Properties.WriteTo(writer);
                writer.WritePropertyName("geometry");
                writer.WriteStartObject();
                writer.WriteString("type", "MultiLineString");
                writer.WritePropertyName("coordinates");
                writer.WriteStartArray();
                foreach (var line in tileFeature.Lines)
                {
                    writer.WriteStartArray();
                    WritePoint(writer, line.A);
                    WritePoint(writer, line.B);
                    writer.WriteEndArray();
                }
                writer.WriteEndArray();
                writer.WriteEndObject();
                writer.WriteEndObject();
            }
            writer.WriteEndArray();
            writer.WriteEndObject();
        });
        bytes += new FileInfo(path).Length;
        tileKeys.Add($"{coord.X}/{coord.Y}");
    }

    return new TileSummary(perTile.Count, bytes, tileKeys.Order(StringComparer.Ordinal).ToArray());
}

static void AddSegmentToTiles(GeoPoint a, GeoPoint b, int zoom, Dictionary<TileCoord, List<GeoLine>> linesByTile)
{
    if (!IsValid(a) || !IsValid(b)) return;

    var west = Math.Min(a.Lon, b.Lon);
    var east = Math.Max(a.Lon, b.Lon);
    var south = Math.Min(a.Lat, b.Lat);
    var north = Math.Max(a.Lat, b.Lat);
    var minTile = LonLatToTile(west, north, zoom);
    var maxTile = LonLatToTile(east, south, zoom);

    for (var x = minTile.X; x <= maxTile.X; x++)
    {
        for (var y = minTile.Y; y <= maxTile.Y; y++)
        {
            var bounds = TileBounds(x, y, zoom).Expand(0.0005);
            if (ClipSegment(a, b, bounds, out var clippedA, out var clippedB))
            {
                var coord = new TileCoord(zoom, x, y);
                if (!linesByTile.TryGetValue(coord, out var lines))
                {
                    lines = [];
                    linesByTile[coord] = lines;
                }
                lines.Add(new GeoLine(clippedA, clippedB));
            }
        }
    }
}

static bool ClipSegment(GeoPoint a, GeoPoint b, GeoBounds bounds, out GeoPoint clippedA, out GeoPoint clippedB)
{
    var x0 = a.Lon;
    var y0 = a.Lat;
    var x1 = b.Lon;
    var y1 = b.Lat;
    var code0 = OutCode(x0, y0, bounds);
    var code1 = OutCode(x1, y1, bounds);

    while (true)
    {
        if ((code0 | code1) == 0)
        {
            clippedA = new GeoPoint(x0, y0);
            clippedB = new GeoPoint(x1, y1);
            return true;
        }
        if ((code0 & code1) != 0)
        {
            clippedA = default;
            clippedB = default;
            return false;
        }

        var outCode = code0 != 0 ? code0 : code1;
        double x;
        double y;
        if ((outCode & 8) != 0)
        {
            x = x0 + (x1 - x0) * (bounds.North - y0) / ((y1 - y0) == 0 ? 1e-12 : y1 - y0);
            y = bounds.North;
        }
        else if ((outCode & 4) != 0)
        {
            x = x0 + (x1 - x0) * (bounds.South - y0) / ((y1 - y0) == 0 ? 1e-12 : y1 - y0);
            y = bounds.South;
        }
        else if ((outCode & 2) != 0)
        {
            y = y0 + (y1 - y0) * (bounds.East - x0) / ((x1 - x0) == 0 ? 1e-12 : x1 - x0);
            x = bounds.East;
        }
        else
        {
            y = y0 + (y1 - y0) * (bounds.West - x0) / ((x1 - x0) == 0 ? 1e-12 : x1 - x0);
            x = bounds.West;
        }

        if (outCode == code0)
        {
            x0 = x;
            y0 = y;
            code0 = OutCode(x0, y0, bounds);
        }
        else
        {
            x1 = x;
            y1 = y;
            code1 = OutCode(x1, y1, bounds);
        }
    }
}

static int OutCode(double lon, double lat, GeoBounds bounds)
{
    var code = 0;
    if (lon < bounds.West) code |= 1;
    else if (lon > bounds.East) code |= 2;
    if (lat < bounds.South) code |= 4;
    else if (lat > bounds.North) code |= 8;
    return code;
}

static void VisitLineStrings(JsonElement geometry, Action<List<GeoPoint>> visit)
{
    var type = geometry.GetProperty("type").GetString();
    if (!geometry.TryGetProperty("coordinates", out var coordinates)) return;

    if (type == "LineString")
    {
        var line = ReadLine(coordinates);
        if (line.Count > 1) visit(line);
    }
    else if (type == "MultiLineString")
    {
        foreach (var lineElement in coordinates.EnumerateArray())
        {
            var line = ReadLine(lineElement);
            if (line.Count > 1) visit(line);
        }
    }
}

static List<GeoPoint> ReadLine(JsonElement coordinates)
{
    var line = new List<GeoPoint>();
    foreach (var point in coordinates.EnumerateArray())
    {
        if (point.GetArrayLength() < 2) continue;
        line.Add(new GeoPoint(point[0].GetDouble(), point[1].GetDouble()));
    }
    return line;
}

static bool IsValid(GeoPoint point) =>
    double.IsFinite(point.Lon) && double.IsFinite(point.Lat);

static TileCoord LonLatToTile(double lon, double lat, int zoom)
{
    var n = 1 << zoom;
    var clampedLat = Math.Clamp(lat, -85.05112878, 85.05112878);
    var x = (int)Math.Floor((lon + 180.0) / 360.0 * n);
    var latRad = clampedLat * Math.PI / 180.0;
    var y = (int)Math.Floor((1.0 - Math.Log(Math.Tan(latRad) + 1.0 / Math.Cos(latRad)) / Math.PI) / 2.0 * n);
    return new TileCoord(zoom, Math.Clamp(x, 0, n - 1), Math.Clamp(y, 0, n - 1));
}

static GeoBounds TileBounds(int x, int y, int zoom)
{
    var n = 1 << zoom;
    var west = x / (double)n * 360.0 - 180.0;
    var east = (x + 1) / (double)n * 360.0 - 180.0;
    var north = MercatorYToLat(Math.PI * (1.0 - 2.0 * y / n));
    var south = MercatorYToLat(Math.PI * (1.0 - 2.0 * (y + 1) / n));
    return new GeoBounds(west, south, east, north);
}

static double MercatorYToLat(double y) =>
    Math.Atan(Math.Sinh(y)) * 180.0 / Math.PI;

static void WritePoint(Utf8JsonWriter writer, GeoPoint point)
{
    writer.WriteStartArray();
    writer.WriteNumberValue(Math.Round(point.Lon, 7));
    writer.WriteNumberValue(Math.Round(point.Lat, 7));
    writer.WriteEndArray();
}

static bool IsInactive(string? status) =>
    status is "Abandoned" or "Removed" or "Discontinued";

static void WriteFeatureCollection(string path, IReadOnlyList<JsonElement> features)
{
    WriteJson(path, writer =>
    {
        writer.WriteStartObject();
        writer.WriteString("type", "FeatureCollection");
        writer.WritePropertyName("features");
        writer.WriteStartArray();
        foreach (var feature in features)
        {
            feature.WriteTo(writer);
        }
        writer.WriteEndArray();
        writer.WriteEndObject();
    });
}

static void WriteIndexGroup(
    Utf8JsonWriter writer,
    string propertyName,
    IReadOnlyDictionary<string, PipelineIndexEntry> entries)
{
    writer.WritePropertyName(propertyName);
    writer.WriteStartObject();
    foreach (var (key, entry) in entries.OrderBy(x => x.Key))
    {
        writer.WritePropertyName(key);
        writer.WriteStartObject();
        writer.WriteString("path", entry.Path);
        writer.WriteNumber("count", entry.Count);
        writer.WriteNumber("bytes", entry.Bytes);
        if (entry.TileTemplate is not null && entry.TileZoom is not null)
        {
            writer.WriteString("tile_template", entry.TileTemplate);
            writer.WriteNumber("tile_zoom", entry.TileZoom.Value);
            writer.WriteNumber("tile_count", entry.TileCount.GetValueOrDefault());
            writer.WriteNumber("tile_bytes", entry.TileBytes.GetValueOrDefault());
            writer.WritePropertyName("tile_keys");
            writer.WriteStartArray();
            foreach (var tileKey in entry.TileKeys ?? [])
            {
                writer.WriteStringValue(tileKey);
            }
            writer.WriteEndArray();
        }
        writer.WriteEndObject();
    }
    writer.WriteEndObject();
}

static void WriteJson(string path, Action<Utf8JsonWriter> write)
{
    Directory.CreateDirectory(Path.GetDirectoryName(path)!);
    using var stream = File.Create(path);
    using var writer = new Utf8JsonWriter(stream, new JsonWriterOptions { Indented = false });
    write(writer);
}

static string FindProjectRoot(string start)
{
    var dir = new DirectoryInfo(start);
    while (dir is not null)
    {
        if (File.Exists(Path.Combine(dir.FullName, "index.html"))
            && Directory.Exists(Path.Combine(dir.FullName, "public", "data")))
        {
            return dir.FullName;
        }
        dir = dir.Parent;
    }
    throw new DirectoryNotFoundException("Could not find project root containing index.html and public/data.");
}

static string Relative(string root, string path) =>
    Path.GetRelativePath(root, path).Replace('\\', '/');

sealed record PipelineIndex
{
    public int Version { get; init; }
    public string GeneratedAt { get; init; } = "";
    public Dictionary<string, PipelineIndexEntry> LineCategories { get; } = new(StringComparer.Ordinal);
    public Dictionary<string, PipelineIndexEntry> InstallationCategories { get; } = new(StringComparer.Ordinal);
}

sealed record PipelineIndexEntry(
    string Path,
    int Count,
    long Bytes,
    string? TileTemplate = null,
    int? TileZoom = null,
    int? TileCount = null,
    long? TileBytes = null,
    string[]? TileKeys = null);

readonly record struct GeoPoint(double Lon, double Lat);
readonly record struct GeoLine(GeoPoint A, GeoPoint B);
readonly record struct TileCoord(int Z, int X, int Y);
readonly record struct GeoBounds(double West, double South, double East, double North)
{
    public GeoBounds Expand(double degrees) =>
        new(West - degrees, South - degrees, East + degrees, North + degrees);
}

sealed record TileFeature(JsonElement Properties, List<GeoLine> Lines);
sealed record TileSummary(int TileCount, long Bytes, string[] TileKeys);
