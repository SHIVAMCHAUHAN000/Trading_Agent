"""Stage 10 dashboard renderer tests."""

from __future__ import annotations

from pathlib import Path

from reports_ui.render_dashboard import render_dashboard_html, write_dashboard


def test_render_dashboard_contains_conclusion(tmp_path: Path):
    report = {
        "experiment_id": "EXP-000099",
        "strategy_name": "demo_strategy",
        "created_at": "2026-03-29T00:00:00Z",
        "simple_report": {
            "what_is_the_strategy": "A demo strategy.",
            "why_might_it_work": "Momentum persistence.",
            "how_did_it_perform": "CAGR ok.",
            "how_risky_is_it": "DD exists.",
            "what_breaks_it": "Costs.",
            "is_result_robust": "Mixed.",
            "major_warnings": ["Survivorship bias"],
            "research_conclusion_summary": "PROMISING. constructive but biased.",
        },
        "technical_report": {
            "backtest_results": {"performance": {"cagr": 0.2, "sharpe": 1.1, "max_drawdown": -0.3}},
            "trade_statistics": {"win_rate": 0.55},
            "benchmark_comparison": {"information_ratio": 0.8, "excess_cagr": 0.1},
            "out_of_sample": {"out_of_sample": {"metrics": {"sharpe": 1.2, "win_rate": 0.6}}},
            "walk_forward": {"summary": {"positive_sharpe_folds": 3, "n_folds": 4, "mean_test_sharpe": 0.9}},
            "parameter_sensitivity": {"robustness": "ROBUST_REGION"},
            "cost_sensitivity": {"verdict": "SURVIVES_COST_STRESS"},
            "bias_checks": {"flags": [{"severity": "critical", "code": "SURVIVORSHIP", "message": "bias"}]},
        },
        "conclusion": {"status": "PROMISING", "rationale": "ok"},
    }
    html = render_dashboard_html(report)
    assert "EXP-000099" in html
    assert "PROMISING" in html
    assert "Survivorship" in html

    path = tmp_path / "research_report.json"
    path.write_text(__import__("json").dumps(report), encoding="utf-8")
    out = write_dashboard(path)
    assert out.exists()
    assert "demo_strategy" in out.read_text(encoding="utf-8")
