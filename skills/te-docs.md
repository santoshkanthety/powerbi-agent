---
name: te-docs
version: 0.2.0
description: Look up Tabular Editor (TE2 / TE3) documentation — C# scripting cookbook, BPA rule reference, CLI flags, dynamic format strings, calculation groups, TOM/TMSL APIs. Automatically invoke when the user asks about a Tabular Editor feature, scripting recipe, BPA rule, CLI flag, calculation group syntax, dynamic format string, or quotes a TE error message; or mentions Tabular Editor, TE2, TE3, ScriptHelper, Model.Tables, Selected.Measures, or TOMWrapper.
---

# Tabular Editor documentation lookup

Tabular Editor has two distributions and two doc sites; pick the right one before quoting features or syntax.

## Distributions

| | TE2 | TE3 |
|---|---|---|
| Origin | Open source (MIT) | Commercial |
| Docs root | https://docs.tabulareditor.com/te2/ | https://docs.tabulareditor.com/te3/ |
| GitHub | https://github.com/TabularEditor/TabularEditor | closed source |
| TOMWrapper | https://github.com/TabularEditor/TOMWrapper | shared abstraction layer |
| Best fit | CI, free scripting, BPA in pipelines | Daily authoring, DAX debugging, calculation-group editor, TMDL, advanced UX |
| CLI | `TabularEditor.exe` | `TabularEditor3.exe` |

If the user runs `te2-cli` or invokes `pbi-agent` skills that shell out to the CLI, default to TE2 unless they specify TE3 — TE2 is what we install and what runs in CI.

## Where to look up what

| Question | Section | URL |
|---|---|---|
| C# scripting recipe (e.g. "how do I bulk-add measures") | Advanced Scripting | https://docs.tabulareditor.com/te2/Advanced-Scripting.html |
| `Selected.Measures`, `Selected.Tables` etc. | Selection helpers | https://docs.tabulareditor.com/te2/Useful-script-snippets.html |
| BPA rule expressions (`Expression`, `Severity`) | Best Practice Analyzer | https://docs.tabulareditor.com/te2/Best-Practice-Analyzer.html |
| BPA standard ruleset | Microsoft Analysis Services GitHub | https://github.com/microsoft/Analysis-Services/tree/master/BestPracticeRules |
| CLI flags (`-D`, `-B`, `-S`, `-V`) | Command-line | https://docs.tabulareditor.com/te2/Command-line-Options.html |
| TMSL deploy gotchas (PartitionTableMismatch etc.) | Deploy & Save | https://docs.tabulareditor.com/te2/Save-Options.html |
| Dynamic format strings | TE3 only — feature page | https://docs.tabulareditor.com/te3/dynamic-format-strings/ |
| Calculation groups | both, but TE3 has the editor | https://docs.tabulareditor.com/te3/calculation-groups/ |
| TOMWrapper API surface (`Model`, `Table`, `Measure`, `Hierarchy` …) | inline IntelliSense + source on GitHub | https://github.com/TabularEditor/TOMWrapper/tree/master/TOMWrapper |

## Common scripting recipes

```csharp
// Bulk-create measures from a list of (name, expression) pairs
var pairs = new[] {
    new { Name = "Total Sales",   Expr = "SUM('Sales'[Amount])" },
    new { Name = "Total Qty",     Expr = "SUM('Sales'[Quantity])" },
};
foreach (var p in pairs) {
    var m = Model.Tables["Sales"].AddMeasure(p.Name, p.Expr);
    m.FormatString = "#,0.00";
    m.DisplayFolder = "Core";
}
```

```csharp
// Apply a measure prefix to all measures in a table
foreach (var m in Model.Tables["Sales"].Measures) {
    if (!m.Name.StartsWith("[fact] "))
        m.Name = "[fact] " + m.Name;
}
```

```csharp
// Hide all FK columns (named "*Key" or "*ID") on dim tables
foreach (var t in Model.Tables.Where(x => x.Name.StartsWith("dim"))) {
    foreach (var c in t.Columns.Where(c => c.Name.EndsWith("Key") || c.Name.EndsWith("ID")))
        c.IsHidden = true;
}
```

## Common BPA expression idioms

```csharp
// Measures must have a format string
Measure: string.IsNullOrWhiteSpace(FormatString)

// Tables must not be hidden if they have visible measures
Table: !IsHidden && Measures.Any(m => !m.IsHidden) && Columns.All(c => c.IsHidden)

// Date table must have IsDateTable flag
Table: Name.ToLower().Contains("date") && !IsDateTable
```

## CLI batch deploy pattern

```powershell
TabularEditor.exe `
    "model.bim" `
    -D "Provider=MSOLAP;Data Source=powerbi://api.powerbi.com/v1.0/myorg/MyWorkspace;Initial Catalog=MyModel" `
    "MyModel" `
    -O `
    -B "rules.json"
```

Flags worth knowing:

| Flag | Effect |
|---|---|
| `-D <conn> <db>` | Deploy to AS / Power BI |
| `-B <bpa.json>` | Run BPA against the supplied ruleset before deploy |
| `-S <script.csx>` | Run a C# script |
| `-O` | Overwrite existing database on deploy |
| `-V` | Verbose log to stdout |
| `-T <output>` | TMSL output file (for review/CI artifacts) |

## When to escalate to TOM directly

TOMWrapper covers ~95% of model operations. Drop to raw TOM (`Microsoft.AnalysisServices.Tabular`) when:

- Tweaking annotations not surfaced by the wrapper
- Reading `RequestedTimeout`, `ImpersonationMode` and other connection properties
- Inspecting `Database.Model.SerializeOptions` before TMSL export
- Iterating refresh policy partition templates

For TOM reference, the canonical source is the SDK: https://learn.microsoft.com/en-us/dotnet/api/microsoft.analysisservices.tabular.

## Pairs well with

- `bpa-rules` skill — for authoring rule files
- `c-sharp-scripting` skill — for executing scripts in TE2
- `te2-cli` skill — for CLI invocation patterns from `pbi-agent`
