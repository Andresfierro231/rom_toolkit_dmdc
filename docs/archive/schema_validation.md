# Archive schema validation and human context tables

Long live runs should not be browsed by opening raw partition files first. Start
with the manifest and context tables.

```bash
dmdc validate-archive-schema --archive-root live_archive
```

This writes:

- `live_archive/schema_validation/archive_schema_validation.md`
- `live_archive/schema_validation/archive_schema_validation_summary.json`
- `live_archive/context/archive_context_index.csv`
- `live_archive/context/archive_data_kind_summary.csv`

The context CSVs are meant for humans. They summarize data kind, run id, time
range, row count, and size. This makes it much easier to navigate months of
archives before drilling into raw data.
