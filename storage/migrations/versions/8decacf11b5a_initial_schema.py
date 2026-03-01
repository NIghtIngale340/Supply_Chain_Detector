"""initial_schema

Revision ID: 8decacf11b5a
Revises:
Create Date: 2026-03-01 17:50:32.022777
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8decacf11b5a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scan_jobs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.String(128), unique=True, index=True, nullable=False),
        sa.Column("package_name", sa.String(255), index=True, nullable=False),
        sa.Column("registry", sa.String(16), index=True, nullable=False),
        sa.Column("status", sa.String(32), index=True, nullable=False, server_default="queued"),
        sa.Column("final_score", sa.Float, nullable=True),
        sa.Column("metadata_score", sa.Float, nullable=True),
        sa.Column("embedding_score", sa.Float, nullable=True),
        sa.Column("static_score", sa.Float, nullable=True),
        sa.Column("llm_score", sa.Float, nullable=True),
        sa.Column("graph_score", sa.Float, nullable=True),
        sa.Column("classifier_score", sa.Float, nullable=True),
        sa.Column("llm_triggered", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("result_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("scan_jobs")
