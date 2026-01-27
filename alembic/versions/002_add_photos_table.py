"""add photos table

Revision ID: 002_add_photos_table
Revises: 001_initial_schema
Create Date: 2024-01-02 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002_add_photos_table"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create photos table
    op.create_table(
        "photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create indexes for photos table
    op.create_index(op.f("ix_photos_id"), "photos", ["id"], unique=False)
    op.create_index(op.f("ix_photos_user_id"), "photos", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_photos_created_at"), "photos", ["created_at"], unique=False
    )


def downgrade() -> None:
    # Drop indexes for photos table
    op.drop_index(op.f("ix_photos_created_at"), table_name="photos")
    op.drop_index(op.f("ix_photos_user_id"), table_name="photos")
    op.drop_index(op.f("ix_photos_id"), table_name="photos")
    # Drop photos table
    op.drop_table("photos")
