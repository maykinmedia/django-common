from django.db import migrations, router

RESET_SQL = """
    SELECT 'SELECT SETVAL(' ||
       quote_literal(quote_ident(PGT.schemaname) || '.' || quote_ident(S.relname)) ||
       ', COALESCE(MAX(' ||quote_ident(C.attname)|| '), 1) ) FROM ' ||
       quote_ident(PGT.schemaname)|| '.'||quote_ident(T.relname)|| ';'
    FROM pg_class AS S,
         pg_depend AS D,
         pg_class AS T,
         pg_attribute AS C,
         pg_tables AS PGT
    WHERE S.relkind = 'S'
        AND S.oid = D.objid
        AND D.refobjid = T.oid
        AND D.refobjid = C.attrelid
        AND D.refobjsubid = C.attnum
        AND T.relname = PGT.tablename
    ORDER BY S.relname;
    """


class ResetSequences(migrations.RunSQL):
    """
    Run the reset_sequences SQL.

    Resetting the Postgres sequences makes sure you don't get Integrity Errors
    when creating objects because of failing unique constraints. This happens
    when you create records explicitly with PKs, bypassing the database PK
    generation. Resetting the sequences makes sure the sequences are aware of
    the used PKs.

    Usage:

        >>> from maykin_common.migration_operations import ResetSequences
        >>> class Migration(migrations.Migration):
        ...     dependencies = (...)
        ...     operations = [
        ...         ResetSequences(),
        ...     ]
    """

    def __init__(self, *args, **kwargs):
        super().__init__("", *args, **kwargs)

        self.reverse_sql = None

    def database_forwards(self, app_label, schema_editor, from_state, to_state) -> None:
        if router.allow_migrate(
            schema_editor.connection.alias, app_label, **self.hints
        ):
            with schema_editor.connection.cursor() as cursor:
                cursor.execute(RESET_SQL)
                rows = cursor.fetchall()

            sql = "\n".join(x[0] for x in rows)

            self._run_sql(schema_editor, sql)  # pyright:ignore[reportAttributeAccessIssue]

    def database_backwards(self, *args, **kwargs) -> None:
        pass
