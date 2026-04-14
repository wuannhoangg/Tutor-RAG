from alembic import op

revision = "add_folders_id"
down_revision = "60eea1376a29"
branch_labels = None
depends_on = None


def upgrade():
    # No-op:
    # folders + documents.folder_id have been merged into the initial migration.
    pass


def downgrade():
    # No-op
    pass