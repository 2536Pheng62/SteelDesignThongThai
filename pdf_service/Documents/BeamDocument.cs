using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;
using PurlinPdfService.Models;
using static PurlinPdfService.Documents.Styles;

namespace PurlinPdfService.Documents;

internal class BeamDocument(InputModel model) : IDocument
{
    private readonly ProjectModel _proj = model.Project;
    private readonly DataModel    _data = model.Data;

    public DocumentMetadata GetMetadata() => new()
    {
        Title   = $"รายการคำนวณคาน — {_data.SectionName}",
        Author  = _proj.Engineer,
        Subject = "Steel Beam Design Calculation",
    };

    public DocumentSettings GetSettings() => DocumentSettings.Default;

    public void Compose(IDocumentContainer container)
    {
        container.Page(page =>
        {
            page.Size(PageSizes.A4);
            page.MarginTop(20);
            page.MarginBottom(18);
            page.MarginHorizontal(20);
            page.DefaultTextStyle(t => t.FontFamily(Font).FontSize(FontBase));

            page.Header().Element(ComposeHeader);
            page.Content().PaddingTop(6).Element(ComposeContent);
            page.Footer().Element(ComposeFooter);
        });
    }

    // ── Header ────────────────────────────────────────────────────────────────
    private void ComposeHeader(IContainer c)
    {
        c.Background(Navy).Padding(6).Row(row =>
        {
            row.RelativeItem().Text(
                $"รายการคำนวณออกแบบโครงสร้างเหล็ก  |  {_proj.ProjectName}")
                .FontFamily(Font).FontSize(FontBase).Bold().FontColor(Colors.White);

            row.ConstantItem(180).AlignRight().Text(
                $"{_proj.Standard}  |  {_proj.Method}")
                .FontFamily(Font).FontSize(FontSm).FontColor(Color.FromHex("#a8d8ea"));
        });
    }

    // ── Footer ────────────────────────────────────────────────────────────────
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

    // ── Content ───────────────────────────────────────────────────────────────
    private void ComposeContent(IContainer c)
    {
        c.Column(col =>
        {
            col.Spacing(6);

            // Cover info row
            CoverBlock(col.Item());

            // 1. Section properties
            col.Item().SectionBanner("1.  คุณสมบัติหน้าตัด (Section Properties)");
            SectionPropsTable(col.Item());

            // 2. Load combinations
            col.Item().SectionBanner("2.  การรวมน้ำหนักบรรทุก (Load Combinations — ASD)");
            LoadCombTable(col.Item());

            // 3. Bending
            col.Item().SectionBanner("3.  การตรวจสอบหน่วยแรงดัด (Bending Stress Check)");
            col.Item().Text($"กรณีวิกฤต: {_data.CriticalLoadCase}")
               .FontFamily(Font).FontSize(FontBase).Italic().FontColor(Blue);
            BendingTable(col.Item());

            // 4. Shear
            col.Item().SectionBanner("4.  การตรวจสอบหน่วยแรงเฉือน (Shear Stress Check)");
            ShearTable(col.Item());

            // 5. Deflection
            col.Item().SectionBanner("5.  การตรวจสอบการแอ่นตัว (Deflection Check)");
            DeflectionTable(col.Item());

            // 6. Summary
            col.Item().SectionBanner("6.  สรุปผลการออกแบบ (Design Summary)");
            SummaryTable(col.Item());

            col.Item().Height(8);
            col.Item().PassFailBanner(_data.IsOk, _data.Status);
        });
    }

    private void CoverBlock(IContainer c)
    {
        c.Background(Light).Border(0.5f).BorderColor(Border).Padding(8).Row(row =>
        {
            row.RelativeItem().Column(col =>
            {
                col.Item().Text($"ออกแบบคานเหล็ก: {_data.SectionName}")
                   .FontFamily(Font).FontSize(FontLg).Bold().FontColor(Navy);
                col.Item().Text($"L = {Fmt(_data.Span)} m   |   {_proj.ProjectName}")
                   .FontFamily(Font).FontSize(FontBase).FontColor(Blue);
            });
            row.ConstantItem(120).Column(col =>
            {
                col.Item().AlignRight().Text(_proj.Date).FontFamily(Font).FontSize(FontSm).FontColor(Blue);
                col.Item().AlignRight().Text($"วิศวกร: {_proj.Engineer}").FontFamily(Font).FontSize(FontSm).FontColor(Blue);
            });
        });
    }

    // ── Section properties ────────────────────────────────────────────────────
    private void SectionPropsTable(IContainer c)
    {
        var items = new (string Key, string Value)[]
        {
            ("หน้าตัด (Section)",           _data.SectionName),
            ("ช่วงคาน L",                   $"{Fmt(_data.Span)} m"),
            ("กำลังคราก Fy",                $"{Fmt(_data.Fy, 0)} MPa"),
            ("โมดูลัสหน้าตัด Sx",           $"{Fmt(_data.Sx / 1e3, 0)} × 10³ mm³"),
            ("โมเมนต์อินีเชีย Ix",          $"{Fmt(_data.Ix / 1e6, 2)} × 10⁶ mm⁴"),
            ("E (เหล็ก)",                   "200,000 MPa"),
            ("หน่วยแรงดัดที่ยอมให้ Fb",    $"{Fmt(_data.Fb)} MPa"),
            ("หน่วยแรงเฉือนที่ยอมให้ Fv",  $"{Fmt(_data.Fv)} MPa"),
        };
        PropsGrid(c, items);
    }

    // ── Load combinations ─────────────────────────────────────────────────────
    private void LoadCombTable(IContainer c)
    {
        if (_data.LoadCases.Count == 0) { c.Text("(ไม่มีข้อมูล)").FontFamily(Font); return; }

        c.Table(table =>
        {
            table.ColumnsDefinition(cols =>
            {
                cols.RelativeColumn(2.2f); // name
                cols.RelativeColumn();     // w
                cols.RelativeColumn();     // M
                cols.RelativeColumn();     // V
                cols.RelativeColumn();     // fb
                cols.RelativeColumn();     // fv
                cols.RelativeColumn();     // fb/Fb
                cols.RelativeColumn();     // fv/Fv
            });

            // Header
            var hdrs = new[] { "กรณีน้ำหนัก", "w (kN/m)", "M (kN-m)", "V (kN)",
                               "fb (MPa)", "fv (MPa)", "fb/Fb", "fv/Fv" };
            foreach (var h in hdrs)
                table.Header(hdr => hdr.Cell().Background(Blue).Padding(3)
                    .Text(h).FontFamily(Font).FontSize(FontSm).Bold().FontColor(Colors.White));

            // Rows
            foreach (var lc in _data.LoadCases)
            {
                Color bg = lc.StressRatio > 1.0 ? FailBg : lc.StressRatio > 0.9 ? WarnBg : Colors.White;
                void Cell(string v, bool right = false) =>
                    table.Cell().Background(bg).Border(0.3f).BorderColor(Border).Padding(3)
                         .Text(v).FontFamily(Font).FontSize(FontSm)
                         .With(t => { if (right) t.AlignRight(); });

                Cell(lc.Name);
                Cell(Fmt(lc.W_kNm), true);
                Cell(Fmt(lc.M_kNm), true);
                Cell(Fmt(lc.V_kN),  true);
                Cell(Fmt(lc.Fb_MPa), true);
                Cell(Fmt(lc.Fv_MPa), true);
                Cell(Fmt(lc.StressRatio, 3), true);
                Cell(Fmt(lc.ShearRatio, 3), true);
            }
        });
    }

    // ── Bending check ─────────────────────────────────────────────────────────
    private void BendingTable(IContainer c)
    {
        double wCrit = _data.Span > 0 ? _data.MaxMoment * 8 / (_data.Span * _data.Span) : 0;
        var rows = new (string Var, string Formula, string Sub, string Result)[]
        {
            ("M_max",
             "M = w·L²/8",
             $"= {Fmt(wCrit)}×{Fmt(_data.Span)}²/8",
             $"{Fmt(_data.MaxMoment)} kN-m"),
            ("fb = M/Sx",
             "fb = M×10⁶/Sx",
             $"= {Fmt(_data.MaxMoment * 1e6 / (_data.Sx > 0 ? _data.Sx : 1), 1)}",
             $"{Fmt(_data.Fb_actual)} MPa"),
            ("Fb (ยอมให้)",
             "Fb = 0.66·Fy",
             $"= 0.66×{Fmt(_data.Fy, 0)}",
             $"{Fmt(_data.Fb)} MPa"),
            ("fb/Fb ≤ 1.0",
             "อัตราส่วนการใช้งาน",
             $"= {Fmt(_data.Fb_actual)}/{Fmt(_data.Fb)}",
             FmtRatio(_data.StressRatio)),
        };
        FormulaTable(c, rows);
    }

    // ── Shear check ───────────────────────────────────────────────────────────
    private void ShearTable(IContainer c)
    {
        double wCrit = _data.Span > 0 ? _data.MaxMoment * 8 / (_data.Span * _data.Span) : 0;
        var rows = new (string, string, string, string)[]
        {
            ("V_max",
             "V = w·L/2",
             $"= {Fmt(wCrit)}×{Fmt(_data.Span)}/2",
             $"{Fmt(_data.MaxShear)} kN"),
            ("fv = V/(d·tw)",
             "fv = V×10³/(d·tw)",
             "จากหน้าตัด",
             $"{Fmt(_data.Fv_actual)} MPa"),
            ("Fv (ยอมให้)",
             "Fv = 0.40·Fy",
             $"= 0.40×{Fmt(_data.Fy, 0)}",
             $"{Fmt(_data.Fv)} MPa"),
            ("fv/Fv ≤ 1.0",
             "อัตราส่วนการใช้งาน",
             $"= {Fmt(_data.Fv_actual)}/{Fmt(_data.Fv)}",
             FmtRatio(_data.ShearRatio)),
        };
        FormulaTable(c, rows);
    }

    // ── Deflection check ──────────────────────────────────────────────────────
    private void DeflectionTable(IContainer c)
    {
        double E = 2e5;
        double EI = _data.Ix > 0 ? E * _data.Ix / 1e12 : 0;
        var rows = new (string, string, string, string)[]
        {
            ("δ_max",
             "δ = 5wL⁴/384EI",
             $"EI = {Fmt(EI, 0)} kN·m²",
             $"{Fmt(_data.DeltaMax)} mm"),
            ("δ_allow",
             "δ = L/360",
             $"= {Fmt(_data.Span * 1000, 0)}/360",
             $"{Fmt(_data.DeltaAllow)} mm"),
            ("δ/δ_allow ≤ 1.0",
             "อัตราส่วนการแอ่นตัว",
             $"= {Fmt(_data.DeltaMax)}/{Fmt(_data.DeltaAllow)}",
             FmtRatio(_data.DeflectionRatio)),
        };
        FormulaTable(c, rows);
    }

    // ── Design summary ────────────────────────────────────────────────────────
    private void SummaryTable(IContainer c)
    {
        var checks = new (string Label, double Ratio)[]
        {
            ("หน่วยแรงดัด (fb/Fb)",        _data.StressRatio),
            ("หน่วยแรงเฉือน (fv/Fv)",      _data.ShearRatio),
            ("การแอ่นตัว (δ/δ_allow)",      _data.DeflectionRatio),
        };
        SummaryGrid(c, checks);
    }

    // ── Shared table builders ─────────────────────────────────────────────────

    private static void PropsGrid(IContainer c, (string Key, string Value)[] items)
    {
        c.Table(table =>
        {
            table.ColumnsDefinition(cols =>
            {
                cols.RelativeColumn(1.8f);
                cols.RelativeColumn(1.2f);
                cols.RelativeColumn(1.8f);
                cols.RelativeColumn(1.2f);
            });

            for (int i = 0; i < items.Length; i += 2)
            {
                Color bg = i % 4 == 0 ? Colors.White : RowAlt;
                (string k1, string v1) = items[i];
                (string k2, string v2) = i + 1 < items.Length ? items[i + 1] : ("", "");

                void KCell(string t) =>
                    table.Cell().Background(Light).Border(0.3f).BorderColor(Border)
                         .Padding(3).Text(t).FontFamily(Font).FontSize(FontSm).Bold().FontColor(Navy);
                void VCell(string t) =>
                    table.Cell().Background(bg).Border(0.3f).BorderColor(Border)
                         .Padding(3).AlignRight().Text(t).FontFamily(Font).FontSize(FontSm).FontColor(Navy);

                KCell(k1); VCell(v1); KCell(k2); VCell(v2);
            }
        });
    }

    private static void FormulaTable(IContainer c, (string Var, string Formula, string Sub, string Result)[] rows)
    {
        c.Table(table =>
        {
            table.ColumnsDefinition(cols =>
            {
                cols.RelativeColumn(1.8f); // var
                cols.RelativeColumn(1.8f); // formula
                cols.RelativeColumn(2.2f); // sub
                cols.RelativeColumn(0.9f); // result
            });

            // Header
            foreach (var h in new[] { "ตัวแปร", "สูตร", "แทนค่า", "ผลลัพธ์" })
                table.Header(hdr => hdr.Cell().Background(Blue).Padding(3)
                    .Text(h).FontFamily(Font).FontSize(FontSm).Bold().FontColor(Colors.White));

            foreach (var (variable, formula, sub, result) in rows)
            {
                void FC(string t, bool right = false, bool bold = false) =>
                    table.Cell().Border(0.3f).BorderColor(Border).Padding(3)
                         .Text(t).FontFamily(Font).FontSize(FontSm).FontColor(Navy)
                         .With(tx => { if (bold) tx.Bold(); if (right) tx.AlignRight(); });

                FC(variable, bold: true);
                FC(formula);
                FC(sub);
                FC(result, right: true, bold: true);
            }
        });
    }

    private static void SummaryGrid(IContainer c, (string Label, double Ratio)[] checks)
    {
        c.Table(table =>
        {
            table.ColumnsDefinition(cols =>
            {
                cols.RelativeColumn(3f);
                cols.RelativeColumn(1.2f);
                cols.RelativeColumn(1.2f);
                cols.RelativeColumn(1.3f);
            });

            foreach (var h in new[] { "การตรวจสอบ", "อัตราส่วน", "เกณฑ์", "ผล" })
                table.Header(hdr => hdr.Cell().Background(Navy).Padding(3)
                    .Text(h).FontFamily(Font).FontSize(FontSm).Bold().FontColor(Colors.White));

            foreach (var (label, ratio) in checks)
            {
                bool ok  = ratio <= 1.0;
                Color bg  = ok ? PassBg  : FailBg;
                Color clr = ok ? PassGrn : FailRed;

                void SC(string t, bool right = false, Color? color = null, bool bold = false) =>
                    table.Cell().Background(bg).Border(0.3f).BorderColor(Border).Padding(3)
                         .Text(t).FontFamily(Font).FontSize(FontSm)
                         .With(tx =>
                         {
                             if (right) tx.AlignRight();
                             if (bold)  tx.Bold();
                             if (color.HasValue) tx.FontColor(color.Value);
                         });

                SC(label);
                SC(Fmt(ratio, 3), right: true);
                SC("≤ 1.00", right: true);
                SC(ok ? "✓ ผ่าน" : "✗ ไม่ผ่าน", color: clr, bold: true);
            }
        });
    }
}
