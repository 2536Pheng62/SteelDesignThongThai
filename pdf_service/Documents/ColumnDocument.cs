using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;
using PurlinPdfService.Models;
using static PurlinPdfService.Documents.Styles;

namespace PurlinPdfService.Documents;

internal class ColumnDocument(InputModel model) : IDocument
{
    private readonly ProjectModel _proj = model.Project;
    private readonly DataModel    _data = model.Data;

    public DocumentMetadata GetMetadata() => new()
    {
        Title   = $"รายการคำนวณเสา — {_data.SectionName}",
        Author  = _proj.Engineer,
        Subject = "Steel Column Design Calculation",
    };

    public DocumentSettings GetSettings() => DocumentSettings.Default;

    public void Compose(IDocumentContainer container)
    {
        container.Page(page =>
        {
            page.Size(PageSizes.A4);
            page.MarginTop(20).MarginBottom(18).MarginHorizontal(20);
            page.DefaultTextStyle(t => t.FontFamily(Font).FontSize(FontBase));

            page.Header().Element(ComposeHeader);
            page.Content().PaddingTop(6).Element(ComposeContent);
            page.Footer().Element(ComposeFooter);
        });
    }

    private void ComposeHeader(IContainer c)
    {
        c.Background(Navy).Padding(6).Row(row =>
        {
            row.RelativeItem().Text(
                $"รายการคำนวณออกแบบโครงสร้างเหล็ก  |  {_proj.ProjectName}")
                .FontFamily(Font).FontSize(FontBase).Bold().FontColor(Colors.White);

            row.ConstantItem(180).AlignRight().Text(
                $"{_proj.Standard}  |  {_proj.Method}")
                .FontFamily(Font).FontSize(FontSm).FontColor("#a8d8ea");
        });
    }

    private void ComposeFooter(IContainer c)
    {
        c.Background(Light).BorderTop(0.5f).BorderColor(Border)
         .Padding(4).Row(row =>
         {
             row.RelativeItem().Text(
                 $"ออกแบบโดย: {_proj.Engineer}   ตรวจสอบโดย: {_proj.Checker}   วันที่: {_proj.Date}")
                 .FontFamily(Font).FontSize(7.5f).FontColor(Blue);

             row.AutoItem().AlignRight().Text(t =>
             {
                 t.CurrentPageNumber().FontFamily(Font).FontSize(7.5f).Bold().FontColor(Blue);
                 t.Span(" / ").FontFamily(Font).FontSize(7.5f).FontColor(Blue);
                 t.TotalPages().FontFamily(Font).FontSize(7.5f).Bold().FontColor(Blue);
             });
         });
    }

    private void ComposeContent(IContainer c)
    {
        c.Column(col =>
        {
            col.Spacing(6);

            CoverBlock(col.Item());

            SectionBanner(col.Item(), "1.  คุณสมบัติหน้าตัด (Section Properties)");
            SectionPropsTable(col.Item());

            SectionBanner(col.Item(), "2.  การตรวจสอบความชะลูด (Slenderness Check)");
            SlendernessTable(col.Item());

            SectionBanner(col.Item(), "3.  หน่วยแรงอัดที่ยอมให้ (Allowable Compressive Stress)");
            CompressiveStressTable(col.Item());

            SectionBanner(col.Item(), "4.  การตรวจสอบแรงรวม (Combined Loading — Interaction)");
            CombinedTable(col.Item());

            SectionBanner(col.Item(), "5.  สรุปผลการออกแบบ (Design Summary)");
            SummaryTable(col.Item());

            col.Item().Height(8);
            PassFailBanner(col.Item(), _data.IsOk, _data.Status);
        });
    }

    private void CoverBlock(IContainer c)
    {
        c.Background(Light).Border(0.5f).BorderColor(Border).Padding(8).Row(row =>
        {
            row.RelativeItem().Column(col =>
            {
                col.Item().Text($"ออกแบบเสาเหล็ก: {_data.SectionName}")
                   .FontFamily(Font).FontSize(FontLg).Bold().FontColor(Navy);
                col.Item().Text($"H = {Fmt(_data.Height)} m   |   {_proj.ProjectName}")
                   .FontFamily(Font).FontSize(FontBase).FontColor(Blue);
            });
            row.ConstantItem(120).Column(col =>
            {
                col.Item().AlignRight().Text(_proj.Date).FontFamily(Font).FontSize(FontSm).FontColor(Blue);
                col.Item().AlignRight().Text($"วิศวกร: {_proj.Engineer}").FontFamily(Font).FontSize(FontSm).FontColor(Blue);
            });
        });
    }

    private void SectionPropsTable(IContainer c)
    {
        var items = new (string Key, string Value)[]
        {
            ("หน้าตัด (Section)",       _data.SectionName),
            ("ความสูงเสา H",            $"{Fmt(_data.Height)} m"),
            ("พื้นที่หน้าตัด A",        $"{Fmt(_data.A, 0)} mm²"),
            ("rx",                       $"{Fmt(_data.Rx, 1)} mm"),
            ("ry",                       $"{Fmt(_data.Ry, 1)} mm"),
            ("E (เหล็ก)",               "200,000 MPa"),
            ("หน่วยแรงอัดที่ยอมให้ Fa",$"{Fmt(_data.Fa)} MPa"),
            ("กรณีวิกฤต",               _data.CriticalLoadCase),
        };
        PropsGrid(c, items);
    }

    private void SlendernessTable(IContainer c)
    {
        double E = 2e5;
        double Cc = _data.Fy > 0 ? Math.Sqrt(2 * Math.PI * Math.PI * E / _data.Fy) : 0;

        var rows = new (string, string, string, string)[]
        {
            ("KLx", "KLx = Kx·H",      $"= 1.0×{Fmt(_data.Height)}", $"{Fmt(_data.KLx)} m"),
            ("KLy", "KLy = Ky·H",      $"= 1.0×{Fmt(_data.Height)}", $"{Fmt(_data.KLy)} m"),
            ("KLx/rx", "= KLx×1000/rx", $"= {Fmt(_data.KLx*1000,0)}/{Fmt(_data.Rx,1)}", $"{Fmt(_data.SlendernessX, 1)}"),
            ("KLy/ry", "= KLy×1000/ry", $"= {Fmt(_data.KLy*1000,0)}/{Fmt(_data.Ry,1)}", $"{Fmt(_data.SlendernessY, 1)}"),
            ("(KL/r)_max", "ค่าวิกฤต ≤ 200", "max(KLx/rx, KLy/ry)", $"{Fmt(_data.CriticalSlenderness, 1)}"),
            ("Cc", "Cc = √(2π²E/Fy)", $"= √(2π²×{Fmt(E,0)}/{Fmt(_data.Fy,0)})", $"{Fmt(Cc, 1)}"),
        };
        FormulaTable(c, rows);
    }

    private void CompressiveStressTable(IContainer c)
    {
        double E = 2e5;
        double Cc = _data.Fy > 0 ? Math.Sqrt(2 * Math.PI * Math.PI * E / _data.Fy) : 0;
        string regime = _data.CriticalSlenderness <= Cc
            ? "KL/r ≤ Cc  (Inelastic buckling)"
            : "KL/r > Cc  (Elastic buckling)";

        var rows = new (string, string, string, string)[]
        {
            ("fa",
             "fa = P×1000/A",
             $"= {Fmt(_data.MaxAxialLoad)}×1000/{Fmt(_data.A,0)}",
             $"{Fmt(_data.Fa_actual)} MPa"),
            ("Fa",
             "สูตร วสท. 011038-22",
             $"{regime}",
             $"{Fmt(_data.Fa)} MPa"),
            ("fa/Fa ≤ 1.0",
             "อัตราส่วนการอัด",
             $"= {Fmt(_data.Fa_actual)}/{Fmt(_data.Fa)}",
             FmtRatio(_data.AxialRatio)),
        };
        FormulaTable(c, rows);
    }

    private void CombinedTable(IContainer c)
    {
        var rows = new (string, string, string, string)[]
        {
            ("P/P_allow",
             "P_allow = Fa×A/1000",
             $"= {Fmt(_data.Fa)}×{Fmt(_data.A,0)}/1000",
             $"{Fmt(_data.AllowableAxialLoad)} kN"),
            ("Interaction",
             "H1: fa/Fa + fb/Fb ≤ 1.0",
             "แรงรวมทุกกรณี",
             FmtRatio(_data.InteractionRatio)),
        };
        FormulaTable(c, rows);
    }

    private void SummaryTable(IContainer c)
    {
        var checks = new (string Label, double Ratio, string Criteria)[]
        {
            ("ความชะลูด KL/r",          _data.CriticalSlenderness / 200.0, "KL/r ≤ 200"),
            ("แรงอัด (fa/Fa)",           _data.AxialRatio,                  "≤ 1.00"),
            ("แรงรวม (Interaction H1)",  _data.InteractionRatio,            "≤ 1.00"),
        };

        c.Table(table =>
        {
            table.ColumnsDefinition(cols =>
            {
                cols.RelativeColumn(2.5f);
                cols.RelativeColumn(1.2f);
                cols.RelativeColumn(1.5f);
                cols.RelativeColumn(1.2f);
                cols.RelativeColumn(1.3f);
            });

            foreach (var h in new[] { "การตรวจสอบ", "อัตราส่วน", "เกณฑ์", "ค่า", "ผล" })
                table.Header(hdr => hdr.Cell().Background(Navy).Padding(3)
                    .Text(h).FontFamily(Font).FontSize(FontSm).Bold().FontColor(Colors.White));

            foreach (var (label, ratio, criteria) in checks)
            {
                bool ok  = ratio <= 1.0;
                var  bg  = ok ? PassBg  : FailBg;
                var  clr = ok ? PassGrn : FailRed;

                void SC(string t, bool right = false, string? color = null, bool bold = false) =>
                    table.Cell().Background(bg).Border(0.3f).BorderColor(Border).Padding(3)
                         .Text(t).FontFamily(Font).FontSize(FontSm)
                         .With(tx =>
                         {
                             if (right) tx.AlignRight();
                             if (bold)  tx.Bold();
                             if (color != null) tx.FontColor(color);
                         });

                SC(label);
                SC(Fmt(ratio, 3), right: true);
                SC(criteria, right: true);
                SC(Fmt(ratio * (label.StartsWith("ความ") ? 200 : 1), label.StartsWith("ความ") ? 1 : 3), right: true);
                SC(ok ? "✓ ผ่าน" : "✗ ไม่ผ่าน", color: clr, bold: true);
            }
        });
    }

    // ── Shared ────────────────────────────────────────────────────────────────

    private static void PropsGrid(IContainer c, (string Key, string Value)[] items)
    {
        c.Table(table =>
        {
            table.ColumnsDefinition(cols =>
            {
                cols.RelativeColumn(1.8f); cols.RelativeColumn(1.2f);
                cols.RelativeColumn(1.8f); cols.RelativeColumn(1.2f);
            });

            for (int i = 0; i < items.Length; i += 2)
            {
                string bg = i % 4 == 0 ? Colors.White : RowAlt;
                (string k1, string v1) = items[i];
                (string k2, string v2) = i + 1 < items.Length ? items[i + 1] : ("", "");

                table.Cell().Background(Light).Border(0.3f).BorderColor(Border)
                     .Padding(3).Text(k1).FontFamily(Font).FontSize(FontSm).Bold().FontColor(Navy);
                table.Cell().Background(bg).Border(0.3f).BorderColor(Border)
                     .Padding(3).AlignRight().Text(v1).FontFamily(Font).FontSize(FontSm).FontColor(Navy);
                table.Cell().Background(Light).Border(0.3f).BorderColor(Border)
                     .Padding(3).Text(k2).FontFamily(Font).FontSize(FontSm).Bold().FontColor(Navy);
                table.Cell().Background(bg).Border(0.3f).BorderColor(Border)
                     .Padding(3).AlignRight().Text(v2).FontFamily(Font).FontSize(FontSm).FontColor(Navy);
            }
        });
    }

    private static void FormulaTable(IContainer c, (string Var, string Formula, string Sub, string Result)[] rows)
    {
        c.Table(table =>
        {
            table.ColumnsDefinition(cols =>
            {
                cols.RelativeColumn(1.8f);
                cols.RelativeColumn(2f);
                cols.RelativeColumn(2.5f);
                cols.RelativeColumn(1f);
            });

            foreach (var h in new[] { "ตัวแปร", "สูตร", "แทนค่า", "ผลลัพธ์" })
                table.Header(hdr => hdr.Cell().Background(Blue).Padding(3)
                    .Text(h).FontFamily(Font).FontSize(FontSm).Bold().FontColor(Colors.White));

            foreach (var (variable, formula, sub, result) in rows)
            {
                void FC(string t, bool right = false, bool bold = false) =>
                    table.Cell().Border(0.3f).BorderColor(Border).Padding(3)
                         .Text(t).FontFamily(Font).FontSize(FontSm).FontColor(Navy)
                         .With(tx => { if (bold) tx.Bold(); if (right) tx.AlignRight(); });

                FC(variable, bold: true); FC(formula); FC(sub); FC(result, right: true, bold: true);
            }
        });
    }
}
