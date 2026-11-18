from datetime import UTC, datetime

from app.extensions import db


class IngestionRun(db.Model):
    __tablename__ = "ingestion_runs"

    id = db.Column(db.Integer, primary_key=True)
    data_source_id = db.Column(db.Integer, db.ForeignKey("data_sources.id"), nullable=False)
    command = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="running")  # running/success/failed
    started_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))
    completed_at = db.Column(db.DateTime(timezone=True))
    records_retrieved = db.Column(db.Integer, default=0)
    records_loaded = db.Column(db.Integer, default=0)
    validation_failures = db.Column(db.Integer, default=0)
    raw_file_path = db.Column(db.String(500))
    error_message = db.Column(db.Text)

    data_source = db.relationship("DataSource")
