from pathlib import Path

import click
from flask.cli import AppGroup

from app.ingestion.pipeline import run_wfp_prices

ingest_cli = AppGroup("ingest", help="Data ingestion commands.")


@ingest_cli.command("wfp-prices")
@click.option(
    "--file", "file_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Load a local CSV instead of downloading from HDX.",
)
def wfp_prices(file_path):
    """Ingest WFP Kenya food prices."""
    try:
        run = run_wfp_prices(file_path)
    except Exception as exc:
        raise click.ClickException(f"Ingestion failed: {exc}") from exc
    click.echo(
        f"Run {run.id} {run.status}: retrieved={run.records_retrieved} "
        f"loaded={run.records_loaded} validation_failures={run.validation_failures}"
    )
    click.echo(f"Raw file: {run.raw_file_path}")
