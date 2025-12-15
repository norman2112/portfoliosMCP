# How to Anonymize your data

## Summary

1. Install `pganonymize`.
2. Dump relevant data from your origin database.
3. Restore that data from above to a temporary (new) database.
4. Run `pganonymize` against the temporary database.
5. Dump the temporary database to an sql file.

## Just get the tables and schema we want

We don't need all the tables from the original database.
Use the following command to dump just the tables we need from the origin database.

```bash
pg_dump --clean --schema=public --disable-triggers \
    -t objectives -t key_results -t progress_points \
    -t work_item_containers -t settings \
    postgres://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/postgres \
    > /tmp/production_dump.sql
```

## Create a temporary database

Create a temporary database, say `pg_copy`.

```bash
createdb pg_copy
```

## Load up the temporary database with the pared down sql

Restore the data in the dump file to the `pg_copy` database.

```bash
psql -f /tmp/production_dump.sql pg_copy
```

Note: Don't worry about any errors about missing triggers or functions.
We don't want them in the new database.

`pg_copy` is now the pared-down database. Now that we have this
pared-down database, we can create an anonymized dump of this new database.

## Anonymize the `pg_copy` database

The anonymizer chosen is a python package called`pganonymize`.

### Install `pganonymize`

```bash
pip install pganonymize
```

### Anonymize `pg_copy`

**WARNING**:
`pganonymize` will anonymize/alter the database _directly_.
After which, we can finally create a dump file of our new, anonymized database.
Make sure you're anonymizing the temporary database, and not the original one!

```bash
pganonymize --schema=tools/anonymizer/config.yml \
    --dbname=pg_copy --user=${PGUSER} --password=${PGPASSWORD} \
    --host=${PGHOST} --port=${PGPORT}
```

## Dump `pg_copy` to an sql file

```bash
pg_dump postgres://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPASSWORD}/pg_copy \
  > /tmp/anonymous.sql
```
