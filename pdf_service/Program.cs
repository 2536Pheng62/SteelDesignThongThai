/*
  PurlinPdfService — QuestPDF-based PDF generator for steel structure calculations
  Usage:
    echo '{...json...}' | PurlinPdfService.exe [output.pdf]
    PurlinPdfService.exe input.json [output.pdf]

  If output path is given → saves to file and exits 0.
  Otherwise             → writes raw PDF bytes to stdout.
*/

using System.Text.Json;
using QuestPDF.Fluent;
using QuestPDF.Infrastructure;
using PurlinPdfService.Models;
using PurlinPdfService.Documents;

// ── License ────────────────────────────────────────────────────────────────────
QuestPDF.Settings.License = LicenseType.Community;

// ── Thai font ──────────────────────────────────────────────────────────────────
var fontPaths = new[]
{
    @"C:\Windows\Fonts\ARIALUNI.ttf",
    @"/usr/share/fonts/truetype/arialuni.ttf",    // Linux fallback
    Path.Combine(AppContext.BaseDirectory, "fonts", "ARIALUNI.ttf"),
};
foreach (var fp in fontPaths)
{
    if (File.Exists(fp))
    {
        QuestPDF.Drawing.FontManager.RegisterFontWithCustomName(
            "Arial Unicode MS", File.OpenRead(fp));
        break;
    }
}

// ── Read input ─────────────────────────────────────────────────────────────────
string jsonText;
string? outputPath = null;

if (args.Length >= 1 && File.Exists(args[0]))
{
    // File mode: PurlinPdfService.exe input.json [output.pdf]
    jsonText   = await File.ReadAllTextAsync(args[0]);
    outputPath = args.Length >= 2 ? args[1] : null;
}
else
{
    // Stdin mode: echo '{...}' | PurlinPdfService.exe [output.pdf]
    if (!Console.IsInputRedirected)
    {
        Console.Error.WriteLine("Usage: PurlinPdfService.exe [input.json] [output.pdf]");
        Console.Error.WriteLine("       or pipe JSON to stdin");
        return 2;
    }
    jsonText   = await Console.In.ReadToEndAsync();
    outputPath = args.Length >= 1 ? args[0] : null;
}

// ── Parse ──────────────────────────────────────────────────────────────────────
InputModel model;
try
{
    model = JsonSerializer.Deserialize<InputModel>(jsonText,
        new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
        ?? throw new InvalidOperationException("JSON deserialized to null");
}
catch (Exception ex)
{
    Console.Error.WriteLine($"JSON parse error: {ex.Message}");
    return 1;
}

// Fill date if empty
if (string.IsNullOrWhiteSpace(model.Project.Date))
    model.Project.Date = DateTime.Now.ToString("dd/MM/yyyy");

// ── Generate ───────────────────────────────────────────────────────────────────
IDocument doc = model.Module.ToLower() switch
{
    "beam"   => new BeamDocument(model),
    "column" => new ColumnDocument(model),
    _        => throw new NotSupportedException($"module '{model.Module}' not supported"),
};

byte[] pdfBytes;
try
{
    pdfBytes = doc.GeneratePdf();
}
catch (Exception ex)
{
    Console.Error.WriteLine($"PDF generation error: {ex.Message}");
    return 1;
}

// ── Output ─────────────────────────────────────────────────────────────────────
if (outputPath is not null)
{
    await File.WriteAllBytesAsync(outputPath, pdfBytes);
    Console.Error.WriteLine($"Saved: {outputPath} ({pdfBytes.Length:N0} bytes)");
}
else
{
    using var stdout = Console.OpenStandardOutput();
    await stdout.WriteAsync(pdfBytes);
}

return 0;
