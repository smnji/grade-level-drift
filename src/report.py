"""Build the v0 interactive HTML report from a scored parquet.

The report is a single self-contained HTML file: plotly is bundled inline so
the artifact opens correctly from the file system without a network round
trip. Story arc follows `methodology.md §6` and the Phase-D outline:

1. Hook — headline mean Δ per model
2. The data — n=60 standards composition
3. Headline finding — Δ distribution per model
4. Prompt sensitivity — Δ density per (model × prompt)
5. Wording intervention — Δ(raw) vs Δ(simplified), paired
6. Per-standard drift — top + bottom by mean |Δ|
7. Cross-model agreement — Δ scatter matrix, Pearson r
8. Convergent validity — Δ for each formula vs ensemble
9. Caveats and what we did not measure
10. Reproduce — the single command

Run:

    python -m src.report --run-id v0_run1
    # writes reports/v0_run1_report.html
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.io import to_html
from plotly.subplots import make_subplots

from src.openai_helpers import REPO_ROOT


def _ci95(series: pd.Series) -> tuple[float, float]:
    """Normal-approximation 95% CI for the mean. Returns (lo, hi)."""
    s = series.dropna()
    n = len(s)
    if n < 2:
        return (float("nan"), float("nan"))
    m = float(s.mean())
    se = float(s.std(ddof=1)) / (n ** 0.5)
    return (m - 1.96 * se, m + 1.96 * se)


def _icc2_one_way(matrix: pd.DataFrame) -> float:
    """ICC(2,1) for a (subjects × raters) matrix. Subjects = rows.

    Two-way random-effects, single-rater, absolute-agreement. Returns NaN if
    the matrix has fewer than 2 subjects or 2 raters or any missing data.
    """
    m = matrix.dropna()
    n, k = m.shape
    if n < 2 or k < 2:
        return float("nan")
    grand = m.values.mean()
    ssb = k * ((m.mean(axis=1) - grand) ** 2).sum()
    ssw = ((m.values - m.mean(axis=1).values[:, None]) ** 2).sum()
    ssr = n * ((m.mean(axis=0) - grand) ** 2).sum()
    sse = ssw - ssr
    msb = ssb / (n - 1)
    msr = ssr / (k - 1)
    mse = sse / ((n - 1) * (k - 1))
    denom = msb + (k - 1) * mse + (k * (msr - mse) / n)
    if denom <= 0:
        return float("nan")
    return float((msb - mse) / denom)

RESULTS_DIR = REPO_ROOT / "data" / "results"
REPORTS_DIR = REPO_ROOT / "reports"
GENERATED_DIR = REPO_ROOT / "data" / "generated"

FORMULAS = [
    "flesch_kincaid_grade",
    "smog_index",
    "coleman_liau_index",
    "automated_readability_index",
    "gunning_fog",
    "dale_chall_readability_score",
]


def _fig_to_div(fig: go.Figure, *, include_js: bool) -> str:
    return to_html(
        fig,
        include_plotlyjs="inline" if include_js else False,
        full_html=False,
        config={"displaylogo": False, "responsive": True},
    )


def _generations(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["kind"] == "generation"].copy()


def section_hook(df: pd.DataFrame) -> str:
    g = _generations(df).dropna(subset=["delta_ensemble"])
    rows = []
    for model, sub in g.groupby("model", dropna=False):
        mean_d = sub["delta_ensemble"].mean()
        median_d = sub["delta_ensemble"].median()
        lo, hi = _ci95(sub["delta_ensemble"])
        n = len(sub)
        rows.append(
            f"<tr><td><b>{html.escape(str(model))}</b></td>"
            f"<td>{mean_d:+.2f}</td>"
            f"<td>[{lo:+.2f}, {hi:+.2f}]</td>"
            f"<td>{median_d:+.2f}</td>"
            f"<td>{n:,}</td></tr>"
        )
    table = (
        "<table class='hook'><thead><tr>"
        "<th>Model</th><th>Mean Δ</th><th>95% CI</th><th>Median Δ</th><th>n cells</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )
    overall_mean = g["delta_ensemble"].mean()
    above = (g["delta_ensemble"] > 0).mean()
    direction = "above" if overall_mean > 0 else "below"
    return f"""
<section id="hook">
  <h2>1. Hook</h2>
  <p class="lead">
    When asked to teach a K-12 standard, frontier OpenAI models drift
    <b>{abs(overall_mean):.1f} grade levels {direction}</b> the target reading
    level, on average across {len(g):,} generations. <b>{above:.0%}</b> of
    generated explanations land above their target grade.
  </p>
  {table}
  <p class="caption">
    Δ = ensemble grade-level estimate − the standard's target grade.
    Positive Δ means the explanation is harder than the standard expects.
    95% CI uses the normal approximation (n is large per cell).
  </p>
</section>
"""


def section_data(df: pd.DataFrame) -> str:
    g = _generations(df)
    by_subject = g.drop_duplicates("standard_id")["subject"].value_counts()
    by_band = g.drop_duplicates("standard_id")["grade_band"].value_counts().sort_index()
    fig = make_subplots(rows=1, cols=2, subplot_titles=("By subject", "By grade band"))
    fig.add_trace(
        go.Bar(x=list(by_subject.index), y=list(by_subject.values), marker_color="#3a86ff"),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(x=list(by_band.index), y=list(by_band.values), marker_color="#8338ec"),
        row=1,
        col=2,
    )
    fig.update_layout(showlegend=False, height=320, margin=dict(t=40, l=10, r=10, b=10))
    n_models = g["model"].nunique()
    n_prompts = g["prompt_name"].nunique()
    n_wordings = g["wording"].nunique()
    return f"""
<section id="data">
  <h2>2. The data</h2>
  <p>
    n = {g['standard_id'].nunique()} CCSS standards (Multi-State Common Core),
    drawn by simple random sampling from a parent pool of 200. Each
    standard goes through {n_models} models × {n_prompts} prompts × {n_wordings} wordings,
    for a total of {len(g):,} generations. Run manifest pins the seed,
    sample SHA, and tool versions.
  </p>
  {_fig_to_div(fig, include_js=False)}
</section>
"""


def section_headline(df: pd.DataFrame) -> str:
    g = _generations(df).dropna(subset=["delta_ensemble"])
    fig = px.histogram(
        g,
        x="delta_ensemble",
        color="model",
        facet_col="model",
        nbins=40,
        barmode="overlay",
        opacity=0.85,
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Δ distribution per model — positive = above target grade",
    )
    fig.add_vline(x=0, line_dash="dash", line_color="black", opacity=0.6)
    fig.update_layout(height=380, margin=dict(t=60, l=10, r=10, b=10), showlegend=False)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    return f"""
<section id="headline">
  <h2>3. Headline finding</h2>
  <p>
    All three models drift in the same direction — toward higher grade levels
    than asked for. The dashed line at Δ=0 marks "exactly on target."
  </p>
  {_fig_to_div(fig, include_js=False)}
</section>
"""


def section_prompt(df: pd.DataFrame) -> str:
    g = _generations(df).dropna(subset=["delta_ensemble"])
    fig = px.box(
        g,
        x="prompt_name",
        y="delta_ensemble",
        color="model",
        category_orders={"prompt_name": ["S", "M", "L"]},
        points=False,
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Δ by prompt variant — does extra prompt engineering close the gap?",
    )
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.6)
    fig.update_layout(height=380, margin=dict(t=60, l=10, r=10, b=10))
    return f"""
<section id="prompt">
  <h2>4. Does it depend on the prompt?</h2>
  <p>
    S/M/L vary the prompt's input-token budget (zero-shot → role+format →
    one-shot exemplar). If drift is prompt-driven, longer prompts should
    push Δ closer to zero. If drift is robust, the boxes line up.
  </p>
  {_fig_to_div(fig, include_js=False)}
</section>
"""


def section_wording(df: pd.DataFrame) -> str:
    from scipy import stats as _stats

    g = _generations(df).dropna(subset=["delta_ensemble"])
    pivot = (
        g.pivot_table(
            index=["model", "prompt_name", "standard_id"],
            columns="wording",
            values="delta_ensemble",
            aggfunc="first",
        )
        .dropna()
        .reset_index()
    )
    if "raw" not in pivot.columns or "simplified" not in pivot.columns:
        return (
            "<section id='wording'><h2>5. Wording intervention</h2>"
            "<p>(simplified arm not run — skipping)</p></section>"
        )
    pivot["paired_diff"] = pivot["raw"] - pivot["simplified"]
    fig = px.box(
        pivot,
        x="model",
        y="paired_diff",
        color="model",
        points=False,
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Δ(raw) − Δ(simplified) per (model × prompt × standard)",
    )
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.6)
    fig.update_layout(height=360, margin=dict(t=60, l=10, r=10, b=10), showlegend=False)
    diff_rows = []
    for model, sub in pivot.groupby("model"):
        d = sub["paired_diff"].dropna()
        if len(d) < 2:
            t_stat, p_val = float("nan"), float("nan")
        else:
            t_stat, p_val = _stats.ttest_1samp(d, popmean=0.0)
        diff_rows.append(
            {
                "model": model,
                "n": len(d),
                "mean_diff": float(d.mean()),
                "sd_diff": float(d.std(ddof=1)) if len(d) > 1 else float("nan"),
                "t": float(t_stat) if t_stat == t_stat else float("nan"),
                "p_value": float(p_val) if p_val == p_val else float("nan"),
            }
        )
    diff_df = pd.DataFrame(diff_rows).round(3)
    diff_summary = diff_df.to_html(index=False, border=0, classes="summary")
    return f"""
<section id="wording">
  <h2>5. Does the model mirror the standard's wording?</h2>
  <p>
    The simplified arm rewrites each standard at a 4th-grade reading level
    before generation. If the model anchors on the standard's register,
    Δ(raw) − Δ(simplified) is positive (raw wording yields a higher-grade
    explanation than simplified). Paired t-test against zero per model below;
    treat unadjusted p-values as exploratory.
  </p>
  {_fig_to_div(fig, include_js=False)}
  {diff_summary}
</section>
"""


def section_per_standard(df: pd.DataFrame, run_id: str) -> str:
    g = _generations(df).dropna(subset=["delta_ensemble"])
    by_std = (
        g.groupby(["standard_id", "statement_code", "subject", "target_grade"])
        ["delta_ensemble"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={"mean": "mean_delta", "std": "sd_delta", "count": "n"})
    )
    by_std["abs_mean"] = by_std["mean_delta"].abs()
    top = by_std.sort_values("mean_delta", ascending=False).head(10)
    bot = by_std.sort_values("mean_delta", ascending=True).head(10)
    top_html = top[["statement_code", "subject", "target_grade", "mean_delta", "sd_delta", "n"]].round(
        2
    ).to_html(index=False, border=0, classes="summary")
    bot_html = bot[["statement_code", "subject", "target_grade", "mean_delta", "sd_delta", "n"]].round(
        2
    ).to_html(index=False, border=0, classes="summary")

    # one example generation per top-drift standard, click to expand
    examples_html_parts: list[str] = []
    gen_dir = REPO_ROOT / "data" / "generated" / run_id
    for _, row in top.head(5).iterrows():
        sid = row["standard_id"]
        code = row["statement_code"] or sid
        # pick the first generation file that matches this standard
        matches = sorted(gen_dir.glob(f"*__{sid}.json"))
        if not matches:
            continue
        try:
            cell = json.loads(matches[0].read_text(encoding="utf-8"))
        except Exception:
            continue
        examples_html_parts.append(
            f"<details><summary><b>{html.escape(str(code))}</b> "
            f"(target grade {row['target_grade']:.0f}, mean Δ {row['mean_delta']:+.2f}) "
            f"— {html.escape(cell.get('model',''))} {html.escape(cell.get('prompt_name',''))}/"
            f"{html.escape(cell.get('wording',''))}</summary>"
            f"<p><i>Standard:</i> {html.escape(cell.get('description_used',''))}</p>"
            f"<p><i>Generated:</i></p>"
            f"<blockquote>{html.escape(cell.get('output_text','')).replace(chr(10), '<br>')}</blockquote>"
            f"</details>"
        )
    examples_block = (
        "<h3>Example generations from the most-above-target standards</h3>"
        + "\n".join(examples_html_parts)
    ) if examples_html_parts else ""

    return f"""
<section id="per-standard">
  <h2>6. Which standards drift hardest?</h2>
  <p>The top 10 above-target and bottom 10 below-target standards by mean Δ.</p>
  <div class="row">
    <div class="col"><h3>Most above target</h3>{top_html}</div>
    <div class="col"><h3>Most below target</h3>{bot_html}</div>
  </div>
  {examples_block}
</section>
"""


def section_cross_model(df: pd.DataFrame) -> str:
    g = _generations(df).dropna(subset=["delta_ensemble"])
    pivot = (
        g.groupby(["standard_id", "model"])["delta_ensemble"]
        .mean()
        .unstack("model")
        .dropna()
    )
    if pivot.shape[1] < 2:
        return "<section id='cross-model'><h2>7. Cross-model agreement</h2><p>Need ≥2 models.</p></section>"
    fig = px.scatter_matrix(
        pivot.reset_index(),
        dimensions=list(pivot.columns),
        opacity=0.7,
        height=520,
        title="Per-standard mean Δ — across-model scatter matrix",
    )
    fig.update_traces(diagonal_visible=False)
    fig.update_layout(margin=dict(t=60, l=10, r=10, b=10))
    corr = pivot.corr().round(2).to_html(border=0, classes="summary")
    icc = _icc2_one_way(pivot)
    icc_str = f"{icc:.2f}" if icc == icc else "n/a"
    # direction-preservation: of standards, what fraction has all-same-sign Δ?
    sign_match = (
        ((pivot > 0).all(axis=1)) | ((pivot < 0).all(axis=1))
    ).mean()
    return f"""
<section id="cross-model">
  <h2>7. Cross-model agreement</h2>
  <p>If the three models drift the same direction on the same standards, their
  per-standard Δs are correlated.</p>
  <p>
    <b>ICC(2,1)</b> across models = {icc_str} (two-way random-effects, single-rater,
    absolute-agreement on per-standard mean Δ). <b>Direction-preservation:</b>
    {sign_match:.0%} of standards have the same sign of Δ across all models.
  </p>
  {_fig_to_div(fig, include_js=False)}
  <h3>Pearson r matrix</h3>
  {corr}
</section>
"""


def section_convergent(df: pd.DataFrame) -> str:
    g = _generations(df).copy()
    rows = []
    for f in FORMULAS:
        if f not in g.columns:
            continue
        d = g[f] - g["target_grade"]
        rows.append(
            {
                "formula": f,
                "mean_delta": float(d.mean()),
                "median_delta": float(d.median()),
                "sd_delta": float(d.std()),
            }
        )
    fdf = pd.DataFrame(rows)
    if fdf.empty:
        return "<section id='convergent'><h2>8. Convergent validity</h2><p>(no per-formula data)</p></section>"
    fig = px.bar(
        fdf,
        x="formula",
        y="mean_delta",
        error_y="sd_delta",
        color="formula",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title="Mean Δ by individual formula — does the headline depend on the ensemble choice?",
    )
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.6)
    fig.update_layout(height=380, margin=dict(t=60, l=10, r=10, b=10), showlegend=False)
    return f"""
<section id="convergent">
  <h2>8. Convergent validity</h2>
  <p>If each formula's individual prediction tells the same story as the
  ensemble median, the headline is robust to formula choice.</p>
  {_fig_to_div(fig, include_js=False)}
</section>
"""


def section_caveats() -> str:
    return """
<section id="caveats">
  <h2>9. Caveats and what we did NOT measure</h2>
  <ul>
    <li>Reading-level only. No qualitative measures of pedagogical fit,
        accuracy, or coverage.</li>
    <li>One model family (OpenAI). No cross-vendor comparison in v0.</li>
    <li>n = 60 standards. Treat as exploratory; the published study widens
        the frame.</li>
    <li>Classical readability formulas measure surface features. They do
        not capture register, abstraction, or knowledge demands.</li>
    <li>The simplified-wording arm is itself produced by an LLM; its
        register is logged as a covariate, not assumed.</li>
  </ul>
</section>
"""


def section_reproduce(run_id: str) -> str:
    return f"""
<section id="reproduce">
  <h2>10. Reproduce this</h2>
  <pre><code>git clone &lt;repo&gt; &amp;&amp; cd grade-level-drift
cp .env.example .env  # add OPENAI_API_KEY
pip install -r requirements.txt
python -m spacy download en_core_web_sm

python -m src.snapshot
python -m src.sample
python -m src.sub_sample
python -m src.rewrite
python -m src.generate --run-id {run_id}
python -m src.score --run-id {run_id}
python -m src.report --run-id {run_id}
</code></pre>
  <p>The run manifest at <code>data/processed/{run_id}_manifest.json</code>
  pins the exact tools, models, and SHAs that produced this report.</p>
</section>
"""


CSS = """
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         max-width: 980px; margin: 0 auto; padding: 24px; color: #1f2937;
         line-height: 1.5; }
  h1 { font-size: 28px; margin: 0 0 8px; }
  h2 { font-size: 22px; margin: 32px 0 8px; border-bottom: 1px solid #e5e7eb;
       padding-bottom: 6px; }
  h3 { font-size: 16px; margin: 16px 0 4px; }
  p.lead { font-size: 18px; }
  p.caption { font-size: 13px; color: #6b7280; margin-top: 4px; }
  table.hook { border-collapse: collapse; margin: 8px 0 16px; }
  table.hook td, table.hook th { padding: 6px 14px; border-bottom: 1px solid #e5e7eb; }
  table.summary { border-collapse: collapse; font-size: 13px; margin: 8px 0; width: 100%; }
  table.summary td, table.summary th { padding: 4px 8px; border-bottom: 1px solid #e5e7eb; text-align: left; }
  pre { background: #f3f4f6; padding: 12px; border-radius: 6px; font-size: 13px;
        overflow-x: auto; }
  .row { display: flex; gap: 16px; }
  .col { flex: 1; min-width: 0; }
  .meta { font-size: 12px; color: #6b7280; margin-bottom: 24px; }
</style>
"""


def build_report(scores_path: Path, run_id: str, manifest_path: Path | None) -> str:
    df = pd.read_parquet(scores_path)
    sections = [
        section_hook(df),
        section_data(df),
        section_headline(df),
        section_prompt(df),
        section_wording(df),
        section_per_standard(df, run_id),
        section_cross_model(df),
        section_convergent(df),
        section_caveats(),
        section_reproduce(run_id),
    ]

    meta_block = ""
    if manifest_path and manifest_path.exists():
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        meta_block = (
            f"<div class='meta'>run_id={html.escape(m.get('run_id',''))} "
            f"models={html.escape(','.join(m.get('generator_models', [])))} "
            f"started_at={html.escape(m.get('started_at',''))} "
            f"scoring_stack={html.escape(m.get('scoring_stack',{}).get('scoring_stack_version',''))}</div>"
        )

    # plotly.js inline only once (first figure-bearing div). Easiest: use
    # `include_plotlyjs="inline"` on the first call and False afterwards.
    # We've passed False in helpers; bundle plotly.js explicitly here.
    plotly_js = to_html(go.Figure(), include_plotlyjs="inline", full_html=False)
    # `to_html` returns "<script>..plotly..</script><div>..</div>" — extract
    # only the script tag.
    js_only = plotly_js.split("<div", 1)[0]

    body = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<title>Grade-level drift — v0 report ({html.escape(run_id)})</title>
{CSS}
{js_only}
</head><body>
<h1>Grade-level drift in LLM-generated K-12 instruction</h1>
<p class="caption">v0 report — generated from <code>{html.escape(str(scores_path.relative_to(REPO_ROOT)))}</code></p>
{meta_block}
{body}
</body></html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--scores",
        default=None,
        help="Override path to scores parquet (default: data/results/{run_id}_scores.parquet)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Override output HTML path (default: reports/{run_id}_report.html)",
    )
    args = parser.parse_args()

    scores = Path(args.scores) if args.scores else RESULTS_DIR / f"{args.run_id}_scores.parquet"
    if not scores.exists():
        raise SystemExit(f"scores parquet missing at {scores}")
    manifest = REPO_ROOT / "data" / "processed" / f"{args.run_id}_manifest.json"
    out = Path(args.out) if args.out else REPORTS_DIR / f"{args.run_id}_report.html"
    out.parent.mkdir(parents=True, exist_ok=True)

    html_text = build_report(scores, args.run_id, manifest)
    out.write_text(html_text, encoding="utf-8")
    print(f"wrote report → {out.relative_to(REPO_ROOT)} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
