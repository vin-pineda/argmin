"""Argmin command-line interface (Typer).

Commands:
    argmin snapshot          Build & freeze the price snapshot (needs network, run once).
    argmin info              Print the snapshot manifest.
    argmin version           Print engine version + source hash.
    argmin backtest          Walk-forward backtest → figures + tearsheet.csv (M5).
    argmin default-scenario  Precompute the default web scenario JSON (M5).
    argmin openapi           Dump the OpenAPI schema for TS type generation (M5).
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from argmin import __version__, engine_hash
from argmin.config import ArgminConfig, engine_root, get_settings, load_default_config
from argmin.logging import configure_logging

app = typer.Typer(add_completion=False, help="Argmin — portfolio optimization engine")


def _default_output_dir() -> Path:
    """``engine/outputs/`` (created on demand) — where CLI artifacts are written."""
    out = engine_root() / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _load_config(config: str | None) -> ArgminConfig:
    return ArgminConfig.load(config) if config else load_default_config()


@app.command()
def version() -> None:
    """Print engine version + source hash."""
    typer.echo(f"argmin {__version__} (engine_hash={engine_hash()})")


@app.command()
def snapshot(
    config: str = typer.Option(None, help="Path to a scenario YAML (default: bundled)."),
) -> None:
    """Fetch and freeze the committed price snapshot (requires network)."""
    from argmin.data import build_snapshot  # noqa: PLC0415 (lazy: skip heavy imports at CLI start)

    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    cfg = _load_config(config)
    path = build_snapshot(cfg, settings)
    typer.echo(f"✓ Snapshot written: {path}")


@app.command()
def info(
    config: str = typer.Option(None, help="Path to a scenario YAML (default: bundled)."),
) -> None:
    """Print the snapshot manifest."""
    from argmin.data.loader import snapshot_manifest_path  # noqa: PLC0415 — lazy import

    settings = get_settings()
    path = snapshot_manifest_path(settings)
    if not path.exists():
        typer.echo("No snapshot manifest found. Run `argmin snapshot` first.")
        raise typer.Exit(code=1)
    typer.echo(json.dumps(json.loads(path.read_text()), indent=2))


_TEARSHEET_FIELDS = (
    "strategy",
    "total_return",
    "cagr",
    "ann_return",
    "ann_vol",
    "sharpe",
    "sortino",
    "max_drawdown",
    "calmar",
    "var_95",
    "cvar_95",
    "hit_rate",
    "avg_turnover",
    "psr",
    "dsr",
    "sharpe_ci_low",
    "sharpe_ci_high",
)


def _write_tearsheet_csv(resp: object, csv_path: Path) -> None:
    """Write one tearsheet row per strategy + benchmark (metrics + PSR/DSR)."""
    import csv  # noqa: PLC0415

    from argmin.api.models import BacktestResponse  # noqa: PLC0415

    assert isinstance(resp, BacktestResponse)
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(_TEARSHEET_FIELDS))
        writer.writeheader()
        for name, strat in resp.strategies.items():
            row = strat.metrics.model_dump()
            row["strategy"] = name
            writer.writerow({k: row.get(k) for k in _TEARSHEET_FIELDS})


def _write_backtest_figures(resp: object, chosen_method: str, out_dir: Path) -> None:
    """Render the equity / drawdown / rolling-Sharpe / weights PNGs (Agg backend)."""
    import matplotlib  # noqa: PLC0415

    matplotlib.use("Agg")  # headless backend; safe for CI / servers
    import matplotlib.pyplot as plt  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    from argmin.api.models import BacktestResponse  # noqa: PLC0415

    assert isinstance(resp, BacktestResponse)
    dates = np.array(resp.dates, dtype="datetime64[D]")
    window = 252

    def _curve_fig(filename: str, title: str, ylabel: str, attr: str) -> None:
        fig, ax = plt.subplots(figsize=(10, 5))
        for name, strat in resp.strategies.items():
            ax.plot(dates, getattr(strat, attr), label=name, linewidth=1.1)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(out_dir / filename, dpi=120)
        plt.close(fig)

    _curve_fig(
        "equity.png",
        "Equity curve (growth of $1, OOS, net of costs)",
        "Equity",
        "equity_curve",
    )
    _curve_fig("drawdown.png", "Drawdown (underwater curve)", "Drawdown", "drawdown")

    # Rolling Sharpe (variable length per strategy → plotted on its own window).
    fig, ax = plt.subplots(figsize=(10, 5))
    for name, strat in resp.strategies.items():
        rs = np.asarray(strat.rolling_sharpe, dtype=float)
        if rs.size == 0:
            continue
        ax.plot(dates[window - 1 : window - 1 + rs.size], rs, label=name, linewidth=1.0)
    ax.axhline(0.0, color="gray", linewidth=0.6)
    ax.set_title(f"Rolling Sharpe ({window}d)")
    ax.set_ylabel("Sharpe")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "rolling_sharpe.png", dpi=120)
    plt.close(fig)

    # Weights of the chosen strategy over rebalance dates.
    strat_track = resp.strategies[chosen_method]
    weights = np.asarray(strat_track.weights_over_time, dtype=float)
    reb_dates = np.array(strat_track.rebalance_dates, dtype="datetime64[D]")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.stackplot(reb_dates, weights.T, labels=list(resp.tickers))
    ax.set_title(f"{chosen_method} target weights over time")
    ax.set_ylabel("Weight")
    ax.legend(fontsize=7, ncol=3, loc="upper center")
    fig.tight_layout()
    fig.savefig(out_dir / "weights.png", dpi=120)
    plt.close(fig)


@app.command()
def backtest(
    config: str = typer.Option(None, help="Path to a scenario YAML (default: bundled)."),
    method: str = typer.Option(None, help="Optimizer override (default: config method)."),
    out: str = typer.Option(None, help="Output directory (default: engine/outputs)."),
) -> None:
    """Run the walk-forward backtest → tearsheet.csv + figures in ``outputs/``.

    Writes one ``tearsheet.csv`` row per strategy + benchmark (metrics + PSR/DSR)
    and four matplotlib figures (equity, drawdown, rolling Sharpe, weights).
    """
    from argmin.api import service  # noqa: PLC0415
    from argmin.api.models import BacktestRequest  # noqa: PLC0415
    from argmin.data import load_returns_panel  # noqa: PLC0415

    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    cfg = _load_config(config)
    out_dir = Path(out) if out else _default_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    chosen_method = method or cfg.optimizer.method
    panel = load_returns_panel(cfg, settings)
    req = BacktestRequest(
        universe=list(cfg.universe),
        method=chosen_method,
        constraints=cfg.optimizer.constraints,
    )
    resp = service.backtest(panel, cfg, settings, req)

    csv_path = out_dir / "tearsheet.csv"
    _write_tearsheet_csv(resp, csv_path)
    _write_backtest_figures(resp, chosen_method, out_dir)

    # ── summary table ─────────────────────────────────────────────────────────
    typer.echo(f"\nBacktest: method={chosen_method}  OOS {resp.dates[0]} → {resp.dates[-1]}")
    typer.echo(f"{'strategy':<16}{'CAGR':>9}{'Sharpe':>9}{'MaxDD':>9}{'PSR':>8}{'DSR':>8}")
    typer.echo("-" * 59)
    for name, strat in resp.strategies.items():
        m = strat.metrics
        typer.echo(
            f"{name:<16}{m.cagr:>9.2%}{m.sharpe:>9.2f}{m.max_drawdown:>9.2%}"
            f"{(m.psr or 0.0):>8.2f}{(m.dsr or 0.0):>8.2f}"
        )
    typer.echo(f"\n✓ Wrote {csv_path}")
    typer.echo(f"✓ Wrote figures (equity/drawdown/rolling_sharpe/weights) → {out_dir}")


@app.command(name="default-scenario")
def default_scenario(
    config: str = typer.Option(None, help="Path to a scenario YAML (default: bundled)."),
    out: str = typer.Option(
        None, help="Output JSON path (default: outputs/default_scenario.json)."
    ),
) -> None:
    """Precompute the default web scenario JSON (optimize + frontier + backtest).

    Reuses :mod:`argmin.api.service`, so the emitted JSON shape EXACTLY matches
    the live API responses — this is what gives the web instant first paint.
    """
    from argmin.api import service  # noqa: PLC0415
    from argmin.api.models import (  # noqa: PLC0415
        BacktestRequest,
        DefaultScenario,
        OptimizeRequest,
    )
    from argmin.data import load_returns_panel  # noqa: PLC0415

    settings = get_settings()
    configure_logging(settings.log_level, settings.log_json)
    cfg = _load_config(config)
    panel = load_returns_panel(cfg, settings)

    universe = list(cfg.universe)
    optimize_resp = service.optimize(
        panel,
        cfg,
        settings,
        OptimizeRequest(
            universe=universe,
            method=cfg.optimizer.method,
            constraints=cfg.optimizer.constraints,
        ),
    )
    frontier_resp = service.frontier(panel, cfg, settings, universe, None)
    backtest_resp = service.backtest(
        panel,
        cfg,
        settings,
        BacktestRequest(
            universe=universe,
            method=cfg.optimizer.method,
            constraints=cfg.optimizer.constraints,
        ),
    )

    scenario = DefaultScenario(
        optimize=optimize_resp,
        frontier=frontier_resp,
        backtest=backtest_resp,
    )
    out_path = Path(out) if out else (_default_output_dir() / "default_scenario.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(scenario.model_dump_json(indent=2))
    typer.echo(f"✓ Wrote default scenario: {out_path}")


@app.command()
def openapi(
    out: str = typer.Option(None, help="Output JSON path (default: engine/openapi.json)."),
) -> None:
    """Dump the API OpenAPI schema to JSON (for web TS type generation)."""
    from argmin.api import app as api_app  # noqa: PLC0415

    schema = api_app.openapi()
    out_path = Path(out) if out else (engine_root() / "openapi.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(schema, indent=2))
    typer.echo(f"✓ Wrote OpenAPI schema: {out_path}")


if __name__ == "__main__":
    app()
