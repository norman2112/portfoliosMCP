"""parent_objective access insert trigger

Revision ID: 20210604071422
Revises: 20210603151014
Create Date: 2021-06-04 07:14:28.195890

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210604071422"
down_revision = "20210603151014"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE OR REPLACE FUNCTION check_parent_objective_insert_access_function() "
        "RETURNS TRIGGER "
        "LANGUAGE PLPGSQL "
        "AS $$ "
        "DECLARE "
        "access_denied boolean; "
        "parent_work_item_container_id int; "
        "BEGIN "
        "IF NEW.parent_objective_id IS NOT NULL THEN "
        "SELECT EXISTS INTO access_denied ( "
        "SELECT o.work_item_container_id "
        "FROM objectives o "
        "LEFT JOIN work_item_container_roles w ON o.work_item_container_id = w.work_item_container_id "
        "WHERE o.id = NEW.parent_objective_id "
        "AND w.app_created_by = NEW.app_created_by "
        "AND w.okr_role = 'none' "
        "); "
        "IF access_denied THEN "
        "SELECT work_item_container_id INTO parent_work_item_container_id "
        "FROM objectives "
        "WHERE id = NEW.parent_objective_id; "
        "RAISE EXCEPTION "
        "'Cannot save parent_objective_id: %. No access to parent objective work_item_container: %', "
        "NEW.parent_objective_id, parent_work_item_container_id; "
        "END IF; "
        "END IF; "
        "RETURN NEW; "
        "END; "
        "$$;"
    )
    op.execute(
        "CREATE TRIGGER check_parent_objective_insert_access "
        "BEFORE INSERT ON objectives "
        "FOR EACH ROW "
        "EXECUTE PROCEDURE check_parent_objective_insert_access_function();"
    )
    op.execute(
        "ALTER TABLE objectives ENABLE TRIGGER check_parent_objective_insert_access;"
    )


def downgrade():
    op.execute(
        "ALTER TABLE objectives DISABLE TRIGGER check_parent_objective_insert_access;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS check_parent_objective_insert_access ON objectives;"
    )
    op.execute("DROP FUNCTION IF EXISTS check_parent_objective_insert_access_function;")
