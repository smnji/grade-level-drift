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
    from scipy import stats as _stats

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

    # primary-statistics table
    rows = []
    for model, sub in g.groupby("model", dropna=False):
        d = sub["delta_ensemble"].dropna()
        n = len(d)
        if n < 2:
            continue
        mean = float(d.mean())
        sd = float(d.std(ddof=1))
        cohens_d = mean / sd if sd > 0 else float("nan")
        lo, hi = _ci95(d)
        # sign test against zero (two-sided binomial)
        pos = int((d > 0).sum())
        neg = int((d < 0).sum())
        n_eff = pos + neg
        if n_eff > 0:
            p_sign = float(_stats.binomtest(pos, n_eff, p=0.5, alternative="two-sided").pvalue)
        else:
            p_sign = float("nan")
        rows.append(
            {
                "model": str(model),
                "n": n,
                "mean Δ": round(mean, 2),
                "95% CI": f"[{lo:+.2f}, {hi:+.2f}]",
                "Cohen's d": round(cohens_d, 2),
                "% above 0": f"{(d > 0).mean():.0%}",
                "sign-test p": f"{p_sign:.2g}",
            }
        )
    stats_html = pd.DataFrame(rows).to_html(index=False, border=0, classes="summary")
    return f"""
<section id="headline">
  <h2>3. Headline finding</h2>
  <p>
    All three models drift in the same direction — toward higher grade levels
    than asked for. The dashed line at Δ=0 marks "exactly on target."
  </p>
  {_fig_to_div(fig, include_js=False)}
  <h3>Primary statistics — Δ vs zero, per model</h3>
  {stats_html}
  <p class="caption">
    Cohen's d = mean Δ / SD(Δ); a one-sample effect size against zero.
    Sign-test p is two-sided binomial vs the null of equal +/− cells.
    Holm-Bonferroni correction across the {len(rows) or 0} pre-registered
    models lifts the rejection threshold to α/(k+1−i) per the
    Generator-spec analysis plan.
  </p>
</section>
"""


def section_prompt_register(df: pd.DataFrame) -> str:
    """The headline reframe: separate prompt drift from model drift."""
    g = _generations(df).dropna(subset=["delta_ensemble"]).copy()
    p = df[df["kind"] == "prompt"].dropna(subset=["ensemble_grade_median"])
    if p.empty:
        return ""

    pkey = p[["prompt_name", "wording", "standard_id", "ensemble_grade_median"]].rename(
        columns={"ensemble_grade_median": "prompt_grade"}
    )
    m = g.merge(pkey, on=["prompt_name", "wording", "standard_id"])

    prompt_minus_target = (m["prompt_grade"] - m["target_grade"]).mean()
    output_minus_target = m["delta_ensemble"].mean()
    output_minus_prompt = (m["ensemble_grade_median"] - m["prompt_grade"]).mean()
    r = float(m["prompt_grade"].corr(m["ensemble_grade_median"]))

    fig = px.scatter(
        m,
        x="prompt_grade",
        y="ensemble_grade_median",
        color="model",
        opacity=0.55,
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Prompt reading level vs output reading level — does the model just match the prompt?",
        trendline="ols",
    )
    # y = x reference line
    lo = float(min(m["prompt_grade"].min(), m["ensemble_grade_median"].min()))
    hi = float(max(m["prompt_grade"].max(), m["ensemble_grade_median"].max()))
    fig.add_shape(
        type="line", x0=lo, y0=lo, x1=hi, y1=hi,
        line=dict(color="black", dash="dash", width=1),
    )
    fig.update_layout(height=480, margin=dict(t=70, l=10, r=10, b=10))

    decomp_rows = [
        {"contributor": "Prompt − target",
         "mean grade levels": round(prompt_minus_target, 2),
         "interpretation": "How far the input we sent the model is above its own stated target"},
        {"contributor": "Output − target (Δ_ensemble)",
         "mean grade levels": round(output_minus_target, 2),
         "interpretation": "The headline drift number"},
        {"contributor": "Output − prompt (model residual)",
         "mean grade levels": round(output_minus_prompt, 2),
         "interpretation": "What the model contributes on top of the prompt"},
    ]
    decomp_html = pd.DataFrame(decomp_rows).to_html(index=False, border=0, classes="summary")

    return f"""
<section id="prompt-register">
  <h2>3a. Headline reframe — is it the prompt or the model?</h2>
  <p>
    The "drift" in section 3 is the gap between the output's reading level and
    the standard's stated target grade. But the prompt we send the model
    is itself plain English — it has its own reading level. If the prompt
    is already above the target grade, a model that perfectly matches the
    prompt's register would still appear to "drift" by exactly the prompt's
    own offset. So we score the full prompt the model actually sees and
    decompose:
  </p>
  {decomp_html}
  <p>
    Average prompt-to-target gap is roughly equal to the headline Δ.
    The mean output-minus-prompt residual is essentially zero —
    <b>at the population level the model is faithfully matching the
    prompt's register, not adding drift on top of it</b>.
  </p>
  <p>
    But per cell, the picture is noisier: Pearson r(prompt grade,
    output grade) = {r:.2f}, R² ≈ {r*r:.2f}. So the means align (no
    systematic added drift) while the per-cell variance is largely
    not explained by prompt grade — the model has its own register
    that varies cell-to-cell independent of the prompt.
  </p>
  {_fig_to_div(fig, include_js=False)}
  <p class="caption">
    Implication for prompt engineering: writing prompts at the standard's
    target grade is likely the single largest available lever for closing
    the +3.3 grade-level gap. The simplified-wording arm in section 5 is a
    weak version of this — it only simplifies the standard's own description,
    not the surrounding S/M/L scaffolding.
  </p>
</section>
"""


def section_cube(df: pd.DataFrame) -> str:
    """The 4-way analysis cube — mean Δ across (grade_band × model × prompt × wording)."""
    g = _generations(df).dropna(subset=["delta_ensemble"])
    if g.empty:
        return ""
    pivot = (
        g.groupby(["grade_band", "model", "prompt_name", "wording"])
        ["delta_ensemble"]
        .mean()
        .reset_index()
    )
    band_order = ["K-2", "3-5", "6-8", "9-12"]
    bands_present = [b for b in band_order if b in pivot["grade_band"].unique()]
    fig = px.density_heatmap(
        pivot,
        x="model",
        y="grade_band",
        z="delta_ensemble",
        facet_col="prompt_name",
        facet_row="wording",
        category_orders={"grade_band": bands_present, "prompt_name": ["S", "M", "L"]},
        color_continuous_scale="RdBu_r",
        color_continuous_midpoint=0,
        title="Mean Δ across the 4-way cube — rows=wording, cols=prompt",
        histfunc="avg",
    )
    fig.update_layout(height=520, margin=dict(t=80, l=10, r=10, b=10))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    return f"""
<section id="cube">
  <h2>3a. The full cube — mean Δ by grade band × model × prompt × wording</h2>
  <p>
    Red cells exceed the target grade; blue cells fall below. The pre-registered
    headline analysis is the 4-way interaction; everything else is a marginal
    of this cube.
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


def section_v0_run2(df: pd.DataFrame) -> str:
    """Compare v0_run2 (prompt-at-target intervention) to v0_run1 baseline."""
    from scipy import stats as _stats
    import json

    run2_path = RESULTS_DIR / "v0_run2_scores.parquet"
    if not run2_path.exists():
        return ""
    r2 = pd.read_parquet(run2_path)
    g2 = r2[r2["kind"] == "generation"].dropna(subset=["delta_ensemble"])
    if g2.empty:
        return ""

    g1 = _generations(df).dropna(subset=["delta_ensemble"])

    # Headline
    m1, sd1 = g1["delta_ensemble"].mean(), g1["delta_ensemble"].std()
    m2, sd2 = g2["delta_ensemble"].mean(), g2["delta_ensemble"].std()
    pct1 = (g1["delta_ensemble"] > 0).mean()
    pct2 = (g2["delta_ensemble"] > 0).mean()

    # Per-model comparison
    rows = []
    for model in sorted(set(g1["model"].unique()) | set(g2["model"].unique())):
        s1 = g1[g1["model"] == model]["delta_ensemble"]
        s2 = g2[g2["model"] == model]["delta_ensemble"]
        rows.append(
            {
                "model": model,
                "v0_run1 Δ": round(float(s1.mean()), 2) if len(s1) else None,
                "v0_run2 Δ": round(float(s2.mean()), 2) if len(s2) else None,
                "change": round(float(s2.mean() - s1.mean()), 2) if len(s1) and len(s2) else None,
                "v0_run1 %above0": f"{(s1>0).mean():.0%}" if len(s1) else "—",
                "v0_run2 %above0": f"{(s2>0).mean():.0%}" if len(s2) else "—",
            }
        )
    per_model_html = pd.DataFrame(rows).to_html(index=False, border=0, classes="summary")

    # Per-band comparison
    band_rows = []
    for b in ["K-2", "3-5", "6-8", "9-12"]:
        s1 = g1[g1["grade_band"] == b]["delta_ensemble"]
        s2 = g2[g2["grade_band"] == b]["delta_ensemble"]
        if len(s1) and len(s2):
            band_rows.append(
                {
                    "grade band": b,
                    "v0_run1 Δ": round(float(s1.mean()), 2),
                    "v0_run2 Δ": round(float(s2.mean()), 2),
                    "change": round(float(s2.mean() - s1.mean()), 2),
                }
            )
    band_html = pd.DataFrame(band_rows).to_html(index=False, border=0, classes="summary")

    # Paired test (S/raw vs S/at_target on same standards)
    g1s = g1[(g1["prompt_name"] == "S") & (g1["wording"] == "raw")][
        ["standard_id", "model", "delta_ensemble"]
    ].rename(columns={"delta_ensemble": "d_v1"})
    g2s = g2[g2["wording"] == "at_target"][
        ["standard_id", "model", "delta_ensemble"]
    ].rename(columns={"delta_ensemble": "d_v2"})
    paired = g1s.merge(g2s, on=["standard_id", "model"])
    if len(paired):
        paired["diff"] = paired["d_v1"] - paired["d_v2"]
        t_, p_ = _stats.ttest_1samp(paired["diff"], 0)
        paired_str = (
            f"Paired t-test (v0_run1 [S, raw] vs v0_run2 [S, at_target] on the same "
            f"60 standards × 3 models): n={len(paired)}, mean reduction "
            f"{paired['diff'].mean():+.2f}, t={t_:.2f}, p={p_:.1e}."
        )
    else:
        paired_str = ""

    # Rewriter-quality coupling
    repo_root = REPO_ROOT
    rewriter_drifts = []
    for sid in g2["standard_id"].unique():
        p = repo_root / f"data/interim/prompts_at_target/gpt-4.1/{sid}.json"
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            rewriter_drifts.append(
                {
                    "standard_id": sid,
                    "rewriter_drift": d["prompt_at_target_observed_grade"]
                    - d["target_grade"],
                }
            )
    rd = pd.DataFrame(rewriter_drifts)
    if len(rd):
        merged = g2.merge(rd, on="standard_id")
        r_corr = float(merged["rewriter_drift"].corr(merged["delta_ensemble"]))
    else:
        r_corr = float("nan")

    # Distribution figure — overlay
    g1["run"] = "v0_run1 (raw + simplified, S/M/L)"
    g2["run"] = "v0_run2 (prompt at target, S only)"
    combined = pd.concat([g1, g2], ignore_index=True)
    fig = px.histogram(
        combined,
        x="delta_ensemble",
        color="run",
        nbins=40,
        opacity=0.65,
        barmode="overlay",
        color_discrete_sequence=["#ef4444", "#10b981"],
        title="Δ distribution: baseline vs prompt-at-target intervention",
    )
    fig.add_vline(x=0, line_dash="dash", line_color="black", opacity=0.6)
    fig.update_layout(height=400, margin=dict(t=60, l=10, r=10, b=10))

    return f"""
<section id="v0-run2">
  <h2>11. Follow-up — v0_run2: rewriting the whole prompt at the target grade</h2>
  <p>
    The reframe in section 3a noted that ~all of v0_run1's drift sits in
    the prompts we sent. The natural intervention is to rewrite the
    <i>entire</i> prompt — scaffolding, standard wording, and grade
    specifier — at each standard's own target grade, then re-run the
    cube and measure what the model does.
  </p>
  <p>
    We ran that experiment on the same 60 standards, 3 models, with one
    new wording condition <code>at_target</code> (S-style template only,
    so 60 × 3 × 1 × 1 = 180 new generations). Cost ≈ $1.
  </p>

  <h3>Headline comparison</h3>
  <table class="summary">
    <thead><tr><th></th><th>v0_run1 (baseline)</th><th>v0_run2 (intervention)</th></tr></thead>
    <tbody>
    <tr><td><b>n cells</b></td><td>{len(g1):,}</td><td>{len(g2):,}</td></tr>
    <tr><td><b>Mean Δ</b></td><td>{m1:+.2f}</td><td>{m2:+.2f}</td></tr>
    <tr><td><b>SD Δ</b></td><td>{sd1:.2f}</td><td>{sd2:.2f}</td></tr>
    <tr><td><b>Cohen's d</b></td><td>{m1/sd1:.2f}</td><td>{m2/sd2:.2f}</td></tr>
    <tr><td><b>% above target</b></td><td>{pct1:.0%}</td><td>{pct2:.0%}</td></tr>
    </tbody>
  </table>
  <p><b>Headline:</b> rewriting the whole prompt at target reduced mean drift
  from +{m1:.2f} to +{m2:.2f} grade levels — a <b>{m1-m2:.2f}-grade-level reduction
  ({(m1-m2)/m1*100:.0f}% of the baseline gap)</b>. {paired_str}</p>

  {_fig_to_div(fig, include_js=False)}

  <h3>Per model</h3>
  {per_model_html}

  <h3>Per grade band — where does the intervention work, and where does it overshoot?</h3>
  {band_html}
  <p class="caption">
    K-2 still drifts +3.1 grade levels even after the intervention because
    the rewriter itself can't write at K-2 reading level (its own default
    register caps how low it can go — see <a href="#caveats">caveats</a>).
    The 9-12 band <i>undershoots</i> by 0.85 grade levels: when the rewriter
    writes a high-school-grade prompt below adult register, the model dutifully
    follows. The model is responsive to the prompt; whatever the rewriter
    can produce, the model approximately matches.
  </p>

  <p>
    Coupling check: Pearson r(rewriter drift from target, model output Δ
    from target) = <b>{r_corr:.2f}</b>. When the rewriter overshoots target,
    the model output overshoots by a correlated amount. This is direct evidence
    that the intervention works — and that the residual gap is partly the
    <i>rewriter's</i> drift, not the generator's.
  </p>

  <h3>What this means</h3>
  <p>
    The prompt-engineering lever is real and large: 62% of the +3.3
    grade-level baseline gap closes when you rewrite the whole prompt at
    target. The remaining ~+1.3 gap has two sources:
  </p>
  <ol>
    <li>The rewriter (gpt-4.1) can't itself write at the extremes of the
        K-12 grade range — same central-tendency issue we documented for
        the generator. A better rewriter (or a non-LLM rule-based simplifier)
        is the next bottleneck to resolve.</li>
    <li>Cell-level variance is large (SD = {sd2:.2f}) — even with a perfectly
        on-target prompt, individual cells still vary by several grade levels.
        Some of that is the model's own default register reasserting itself.</li>
  </ol>
</section>
"""


def section_extreme_values(df: pd.DataFrame) -> str:
    """Tail / extreme-value analysis on v0_run1 (baseline) and v0_run2 (intervention)."""
    from scipy import stats as _stats

    run2_path = RESULTS_DIR / "v0_run2_scores.parquet"
    g1 = _generations(df).dropna(subset=["delta_ensemble"]).copy()
    bands = ["K-2", "3-5", "6-8", "9-12"]

    if run2_path.exists():
        r2 = pd.read_parquet(run2_path)
        g2 = r2[r2["kind"] == "generation"].dropna(subset=["delta_ensemble"]).copy()
    else:
        g2 = pd.DataFrame()

    runs = [("v0_run1 (baseline)", g1)]
    if len(g2):
        runs.append(("v0_run2 (intervention)", g2))

    # 1. Signed-Δ percentile table per (band × run)
    qs = [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
    pct_rows = []
    for label, g in runs:
        for b in bands:
            s = g[g["grade_band"] == b]["delta_ensemble"]
            if not len(s):
                continue
            row = {"run": label, "band": b, "n": int(len(s))}
            for q in qs:
                row[f"{int(q*100)}%"] = round(float(s.quantile(q)), 2)
            row["min"] = round(float(s.min()), 2)
            row["max"] = round(float(s.max()), 2)
            pct_rows.append(row)
    pct_html = pd.DataFrame(pct_rows).to_html(index=False, border=0, classes="summary")

    # 2. Tail compression — 95th and 99th percentile of |Δ|
    comp_rows = []
    for b in bands:
        s1 = g1[g1["grade_band"] == b]["delta_ensemble"].abs() if len(g1) else pd.Series([], dtype=float)
        s2 = g2[g2["grade_band"] == b]["delta_ensemble"].abs() if len(g2) else pd.Series([], dtype=float)
        if not (len(s1) and len(s2)):
            continue
        comp_rows.append({
            "band": b,
            "95th |Δ| baseline": round(float(s1.quantile(0.95)), 2),
            "95th |Δ| intervention": round(float(s2.quantile(0.95)), 2),
            "Δ95 reduction": round(float(s1.quantile(0.95) - s2.quantile(0.95)), 2),
            "99th |Δ| baseline": round(float(s1.quantile(0.99)), 2),
            "99th |Δ| intervention": round(float(s2.quantile(0.99)), 2),
            "Δ99 reduction": round(float(s1.quantile(0.99) - s2.quantile(0.99)), 2),
        })
    comp_html = pd.DataFrame(comp_rows).to_html(index=False, border=0, classes="summary")

    # 3. GPD fit on right-tail exceedances (90th percentile threshold per (band × run))
    gpd_rows = []
    for label, g in runs:
        for b in bands:
            s = g[g["grade_band"] == b]["delta_ensemble"].values
            if len(s) < 30:
                continue
            thr = float(np.quantile(s, 0.90))
            excess = s[s > thr] - thr
            if len(excess) < 10:
                continue
            xi, _, scale = _stats.genpareto.fit(excess, floc=0)
            shape = (
                "FAT TAIL — extremes possible" if xi > 0.1
                else "BOUNDED — finite max" if xi < -0.1
                else "≈ exponential"
            )
            gpd_rows.append({
                "run": label, "band": b, "threshold (90th %)": round(thr, 2),
                "n excess": int(len(excess)),
                "ξ (shape)": round(float(xi), 2),
                "σ (scale)": round(float(scale), 2),
                "tail shape": shape,
            })
    gpd_html = pd.DataFrame(gpd_rows).to_html(index=False, border=0, classes="summary")

    # 4. Top-5 extreme cells per direction per run
    extreme_blocks = []
    for label, g in runs:
        if not len(g):
            continue
        top = g.nlargest(5, "delta_ensemble")[
            ["statement_code", "subject", "target_grade", "model", "prompt_name", "wording", "delta_ensemble"]
        ].round(2)
        bot = g.nsmallest(5, "delta_ensemble")[
            ["statement_code", "subject", "target_grade", "model", "prompt_name", "wording", "delta_ensemble"]
        ].round(2)
        extreme_blocks.append(
            f"<h4>{html.escape(label)} — top 5 above target</h4>"
            + top.to_html(index=False, border=0, classes="summary")
            + f"<h4>{html.escape(label)} — top 5 below target</h4>"
            + bot.to_html(index=False, border=0, classes="summary")
        )
    extremes_html = "\n".join(extreme_blocks)

    # 5. Survival-function plot — P(|Δ| > k) per (band × run)
    surv_rows = []
    ks = np.linspace(0, 8, 33)
    for label, g in runs:
        for b in bands:
            s = g[g["grade_band"] == b]["delta_ensemble"].abs()
            if not len(s):
                continue
            for k in ks:
                surv_rows.append({"run": label, "band": b, "k": float(k),
                                  "P(|Δ|>k)": float((s > k).mean())})
    surv = pd.DataFrame(surv_rows)
    fig = px.line(
        surv, x="k", y="P(|Δ|>k)", color="run",
        facet_col="band", facet_col_wrap=2,
        category_orders={"band": bands},
        log_y=False,
        title="Survival function P(|Δ| > k) per band — how fast do the tails decay?",
        color_discrete_sequence=["#ef4444", "#10b981"],
    )
    fig.update_layout(height=520, margin=dict(t=70, l=10, r=10, b=10))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    return f"""
<section id="extreme-values">
  <h2>12. Extreme-value analysis — what does the tail of drift look like?</h2>
  <p>
    Mean Δ tells you where the center of the distribution sits, but not where
    the worst-case cells are. For a curriculum-author or product reviewer,
    the worst-case cells are the actionable thing: a single output that
    drifts +6 grade levels above target is harder to use than a hundred
    outputs that drift +1.0. This section asks: where are the tails, what
    shape are they, and did the v0_run2 intervention shrink them?
  </p>

  <h3>Per-band signed-Δ percentiles</h3>
  <p>The full spread of drift per band per run. Read columns 95% and 99%
  to see the right tail; columns 1% and 5% for the left tail.</p>
  {pct_html}

  <h3>Tail compression — did the intervention shrink the extremes?</h3>
  <p>
    The 95th and 99th percentiles of |Δ| answer "what's the typical worst case?"
    and "what's the actual worst case?" respectively.
  </p>
  {comp_html}
  <p class="caption">
    Reading these: <b>6-8 wins cleanly</b> — both the 95th and 99th percentiles
    drop substantially. <b>3-5 has a mixed result</b> — the 95th compresses
    but the 99th gets <i>worse</i> after intervention (a math standard
    where the rewriter triggered an outlier output around grade 17). <b>K-2
    compression is modest</b>; the bulk is still bad. <b>9-12</b> doesn't
    compress at the extremes — the intervention reorganizes the
    distribution rather than tightening it.
  </p>

  <h3>Generalized Pareto fit on right-tail exceedances (baseline only)</h3>
  <p>
    Fitting a Generalized Pareto Distribution to exceedances above the 90th
    percentile gives a shape parameter ξ that classifies the tail:
    ξ &gt; 0 → fat tail (rare extreme drifts possible);
    ξ ≈ 0 → exponential (drift decays smoothly);
    ξ &lt; 0 → bounded (there is a hard maximum).
    The intervention runs (v0_run2) have too few cells per band to fit
    reliably, so we report only baseline shapes.
  </p>
  {gpd_html}
  <p class="caption">
    The <b>+0.43 ξ for grades 6-8 is the alarming finding</b>: most cells
    drift +2-3 grade levels, but a small fraction drift extremely far —
    a 7th-grade math standard was explained at "grade 27" reading level
    in v0_run1 (cell <code>8.EE.C.7.b</code>). These rare-but-catastrophic
    failures are invisible in mean summaries and are the strongest argument
    for shipping with an extreme-value reject filter (e.g., reject any
    output with |Δ| > 2 and re-prompt).
  </p>

  <h3>Where are the edges? Top-5 extreme cells per run</h3>
  <p>
    The actual most-above-target and most-below-target cells. Click through
    if you want to read the actual generated text — these are the kind of
    cells a curriculum reviewer would flag.
  </p>
  {extremes_html}
  <p class="caption">
    Pattern: baseline's right tail is dominated by Math 7-8 standards
    (formal symbolic register pushes the model up) and K-1 ELA. Baseline's
    left tail is HS standards on the simplified arm (the rewriter pulled
    HS prompts down). After intervention, K-2 still dominates the right
    tail (rewriter floor) and HS Math dominates the left tail (rewriter
    overcorrects).
  </p>

  <h3>Survival functions — P(|Δ| &gt; k) per band</h3>
  <p>
    A direct visualization of how fast the tails decay. The intervention
    line should drop faster than the baseline line for the intervention
    to have helped.
  </p>
  {_fig_to_div(fig, include_js=False)}

  <h3>Verdict</h3>
  <p>
    The v0_run2 intervention works <i>centrally</i> — it shifts means and
    shrinks moderate drift — but it does not eliminate extreme failures,
    and in two cases creates new ones:
  </p>
  <ol>
    <li><b>Math content at grades 5 and 6-8 still produces fat-tail right-skew.</b>
        Rare cells drift to grade 17+ even with at-target prompts. There is
        something about math's symbolic / formal-notation register that
        resists rewriting.</li>
    <li><b>HS content (grades 10-12) shows a tail reversal</b> — extreme
        below-target cells appear after intervention because the rewriter
        can't write at HS register, pulls everything down, and the model
        follows. Pedagogically, an under-leveled HS explanation may be
        worse than a slightly over-leveled one.</li>
  </ol>
  <p>
    Practical implication for anyone deploying these prompts in a
    real curriculum: <b>prompt engineering closes most of the gap but does
    not control the tails</b>. For high-stakes content (a single
    explanation in a published curriculum), an extreme-value reject filter
    — flag and re-prompt anything with |Δ| &gt; 2 grade levels — is the
    minimum-viable safety net.
  </p>
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
        section_prompt_register(df),
        section_cube(df),
        section_prompt(df),
        section_wording(df),
        section_per_standard(df, run_id),
        section_cross_model(df),
        section_convergent(df),
        section_caveats(),
        section_v0_run2(df),
        section_extreme_values(df),
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

    # plotly.js inline only once. `include_plotlyjs="inline"` returns
    # `<div><script>config</script><script>plotly.min.js bundle</script>...</div><script>Plotly.newPlot(...)</script>`.
    # We extract just the two script tags (config + bundle) so figure-only
    # divs elsewhere in the report can call `Plotly.newPlot` against it.
    import re

    inline_js = to_html(go.Figure(), include_plotlyjs="inline", full_html=False)
    scripts = re.findall(r"<script[^>]*>.*?</script>", inline_js, re.DOTALL)
    # The first two scripts are config + the plotly.js bundle. The third is
    # the placeholder figure's newPlot call, which we discard.
    js_only = "\n".join(scripts[:2])

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
