using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;

namespace PurlinPdfService.Documents;

/// <summary>Shared typography and color constants.</summary>
internal static class Styles
{
    // ── Colors ────────────────────────────────────────────────────────────────
    public static readonly Color Navy    = Color.FromHex("#0d1b2a");
    public static readonly Color Blue    = Color.FromHex("#1b4f72");
    public static readonly Color Accent  = Color.FromHex("#2e86ab");
    public static readonly Color Light   = Color.FromHex("#f0f4f8");
    public static readonly Color PassGrn = Color.FromHex("#1a7a4a");
    public static readonly Color PassBg  = Color.FromHex("#d4f5e4");
    public static readonly Color FailRed = Color.FromHex("#c0392b");
    public static readonly Color FailBg  = Color.FromHex("#fde8e8");
    public static readonly Color WarnYlw = Color.FromHex("#d68910");
    public static readonly Color WarnBg  = Color.FromHex("#fff3cd");
    public static readonly Color RowAlt  = Color.FromHex("#f7fafc");
    public static readonly Color Border  = Color.FromHex("#dde3ec");

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

    /// <summary>Allows conditional configuration on TextBlockDescriptor.</summary>
    public static TextBlockDescriptor With(this TextBlockDescriptor t, Action<TextBlockDescriptor> action)
    {
        action(t);
        return t;
    }

    /// <summary>Thai-capable text style for IContainer.</summary>
    public static void ThaiText(this IContainer c, string text, float? size = null, bool bold = false, Color? color = null)
    {
        var t = c.Text(text).FontFamily(Font).FontSize(size ?? FontBase);
        if (bold) t.Bold();
        if (color.HasValue) t.FontColor(color.Value);
    }

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

    public static void PassFailBanner(this IContainer c, bool isOk, string status)
    {
        var bg    = isOk ? PassBg  : FailBg;
        var color = isOk ? PassGrn : FailRed;
        var label = isOk ? $"✓  {status}" : $"✗  {status}";

        c.Background(bg).Border(1).BorderColor(color)
         .Padding(10).AlignCenter()
         .Text(label)
         .FontFamily(Font).FontSize(14).Bold().FontColor(color);
    }
}
