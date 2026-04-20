using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;

namespace PurlinPdfService.Documents;

/// <summary>Shared typography and color constants.</summary>
internal static class Styles
{
    // ── Colors ────────────────────────────────────────────────────────────────
    public static readonly string Navy    = "#0d1b2a";
    public static readonly string Blue    = "#1b4f72";
    public static readonly string Accent  = "#2e86ab";
    public static readonly string Light   = "#f0f4f8";
    public static readonly string PassGrn = "#1a7a4a";
    public static readonly string PassBg  = "#d4f5e4";
    public static readonly string FailRed = "#c0392b";
    public static readonly string FailBg  = "#fde8e8";
    public static readonly string WarnYlw = "#d68910";
    public static readonly string WarnBg  = "#fff3cd";
    public static readonly string RowAlt  = "#f7fafc";
    public static readonly string Border  = "#dde3ec";

    // ── Font ──────────────────────────────────────────────────────────────────
    public const string Font     = "Arial Unicode MS";
    public const float  FontSm   = 8f;
    public const float  FontBase = 9f;
    public const float  FontMd   = 10f;
    public const float  FontLg   = 12f;

    // ── Number formatter ──────────────────────────────────────────────────────
    public static string Fmt(double v, int dec = 2) =>
        double.IsNaN(v) || double.IsInfinity(v) ? "—" : v.ToString($"F{dec}");

    public static string FmtRatio(double r) =>
        $"{Fmt(r, 3)} {(r <= 1.0 ? "✓" : "✗")}";

    // ── Fluent helpers ────────────────────────────────────────────────────────

    /// <summary>Thai-capable text style.</summary>
    public static TextDescriptor Thai(this TextDescriptor t) =>
        t.FontFamily(Font).FontSize(FontBase);

    public static IContainer SectionBanner(this IContainer c, string title)
    {
        return c.Background(Blue).Padding(6).Element(e =>
        {
            e.Text(title)
             .FontFamily(Font).FontSize(FontBase).Bold()
             .FontColor(Colors.White);
            return e;
        });
    }

    public static IContainer PassFailBanner(this IContainer c, bool isOk, string status)
    {
        var bg    = isOk ? PassBg  : FailBg;
        var color = isOk ? PassGrn : FailRed;
        var label = isOk ? $"✓  {status}" : $"✗  {status}";
        return c.Background(bg).Border(1).BorderColor(color)
                .Padding(10).AlignCenter()
                .Text(label)
                .FontFamily(Font).FontSize(14).Bold().FontColor(color);
    }
}
