using System.Text.Json.Serialization;

namespace PurlinPdfService.Models;

public class InputModel
{
    [JsonPropertyName("module")]
    public string Module { get; set; } = "";

    [JsonPropertyName("project")]
    public ProjectModel Project { get; set; } = new();

    [JsonPropertyName("data")]
    public DataModel Data { get; set; } = new();
}

public class ProjectModel
{
    [JsonPropertyName("project_name")]  public string ProjectName { get; set; } = "โครงการ";
    [JsonPropertyName("project_no")]    public string ProjectNo   { get; set; } = "";
    [JsonPropertyName("engineer")]      public string Engineer    { get; set; } = "";
    [JsonPropertyName("checker")]       public string Checker     { get; set; } = "";
    [JsonPropertyName("date")]          public string Date        { get; set; } = "";
    [JsonPropertyName("standard")]      public string Standard    { get; set; } = "วสท. 011038-22";
    [JsonPropertyName("method")]        public string Method      { get; set; } = "ASD";
    [JsonPropertyName("client")]        public string Client      { get; set; } = "";
    [JsonPropertyName("location")]      public string Location    { get; set; } = "";
}

public class DataModel
{
    // ── Common ────────────────────────────────────────────────────────────────
    [JsonPropertyName("section_name")]       public string SectionName      { get; set; } = "";
    [JsonPropertyName("is_ok")]              public bool   IsOk              { get; set; }
    [JsonPropertyName("status")]             public string Status            { get; set; } = "";
    [JsonPropertyName("critical_load_case")] public string CriticalLoadCase { get; set; } = "";

    // ── Material ──────────────────────────────────────────────────────────────
    [JsonPropertyName("Fy")] public double Fy { get; set; }

    // ── Beam ──────────────────────────────────────────────────────────────────
    [JsonPropertyName("span")]             public double Span            { get; set; }
    [JsonPropertyName("Fb")]              public double Fb              { get; set; }
    [JsonPropertyName("Fv")]              public double Fv              { get; set; }
    [JsonPropertyName("fb")]              public double Fb_actual       { get; set; }
    [JsonPropertyName("fv")]              public double Fv_actual       { get; set; }
    [JsonPropertyName("max_moment")]       public double MaxMoment       { get; set; }
    [JsonPropertyName("max_shear")]        public double MaxShear        { get; set; }
    [JsonPropertyName("stress_ratio")]     public double StressRatio     { get; set; }
    [JsonPropertyName("shear_ratio")]      public double ShearRatio      { get; set; }
    [JsonPropertyName("delta_max")]        public double DeltaMax        { get; set; }
    [JsonPropertyName("delta_allowable")]  public double DeltaAllow      { get; set; }
    [JsonPropertyName("deflection_ratio")] public double DeflectionRatio { get; set; }
    [JsonPropertyName("Sx")]              public double Sx              { get; set; }
    [JsonPropertyName("Ix")]              public double Ix              { get; set; }
    [JsonPropertyName("load_cases")]       public List<LoadCaseModel> LoadCases { get; set; } = [];

    // ── Column ────────────────────────────────────────────────────────────────
    [JsonPropertyName("height")]               public double Height              { get; set; }
    [JsonPropertyName("Fa")]                   public double Fa                  { get; set; }
    [JsonPropertyName("fa")]                   public double Fa_actual           { get; set; }
    [JsonPropertyName("KLx")]                  public double KLx                 { get; set; }
    [JsonPropertyName("KLy")]                  public double KLy                 { get; set; }
    [JsonPropertyName("slenderness_x")]        public double SlendernessX        { get; set; }
    [JsonPropertyName("slenderness_y")]        public double SlendernessY        { get; set; }
    [JsonPropertyName("critical_slenderness")] public double CriticalSlenderness { get; set; }
    [JsonPropertyName("max_axial_load")]       public double MaxAxialLoad        { get; set; }
    [JsonPropertyName("allowable_axial_load")] public double AllowableAxialLoad  { get; set; }
    [JsonPropertyName("axial_ratio")]          public double AxialRatio          { get; set; }
    [JsonPropertyName("interaction_ratio")]    public double InteractionRatio    { get; set; }
    [JsonPropertyName("A")]                    public double A                   { get; set; }
    [JsonPropertyName("rx")]                   public double Rx                  { get; set; }
    [JsonPropertyName("ry")]                   public double Ry                  { get; set; }
}

public class LoadCaseModel
{
    [JsonPropertyName("name")]         public string Name        { get; set; } = "";
    [JsonPropertyName("w_kN_m")]       public double W_kNm       { get; set; }
    [JsonPropertyName("M_kNm")]        public double M_kNm       { get; set; }
    [JsonPropertyName("V_kN")]         public double V_kN        { get; set; }
    [JsonPropertyName("fb_MPa")]       public double Fb_MPa      { get; set; }
    [JsonPropertyName("fv_MPa")]       public double Fv_MPa      { get; set; }
    [JsonPropertyName("stress_ratio")] public double StressRatio { get; set; }
    [JsonPropertyName("shear_ratio")]  public double ShearRatio  { get; set; }
}
