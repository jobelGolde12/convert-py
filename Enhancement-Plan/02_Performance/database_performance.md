# Database Performance

## Scope

SQLAlchemy/SQLite performance improvements applied during the enhancement cycle. No schema migrations were run — changes are to ORM definitions and query patterns.

## Changes Made

### 1. Removed Unused Indexes

**File**: `app/models/models.py`

Removed indexes that referenced deleted columns:

| Index | Table | Column Removed |
|-------|-------|----------------|
| `idx_files_user_created` | files | `user_id` |
| `idx_jobs_user_created` | jobs | `user_id` |

These indexes were never used in queries (no code ever filtered by `user_id`). Removing them reduces write overhead on INSERT/UPDATE.

### 2. Removed Unused Foreign Keys

**File**: `app/models/models.py`

- `File.user_id` FK -> `users.id` (never set)
- `Job.user_id` FK -> `users.id` (never set)
- `Conversion.user_id` FK -> `users.id` (never set)

Foreign keys require index maintenance on write. Removing unused FKs reduces INSERT cost and eliminates referential integrity checks against a table (`users`) that is no longer created.

### 3. selectinload for Job Queries

**File**: `app/api/routes/jobs.py:106-108`

```python
query = (
    db.query(Job)
    .options(selectinload(Job.tasks))
    .filter(Job.guest_id == identity)
)
```

Avoids N+1 lazy loads when iterating `job.tasks` during serialization.

**File**: `app/services/job_service.py:339-343`

```python
stmt = (
    select(Job)
    .options(selectinload(Job.tasks).selectinload(Task.output))
    .where(Job.id == job_id)
)
```

Eagerly loads the full task->output chain for `get_job_for_api`.

### 4. Removed Unused Base

**File**: `app/core/database.py`

Removed `Base = declarative_base()` — models define their own `Base` in `models.py`. The unused import of `declarative_base` from `sqlalchemy.orm` was also removed.

## No Schema Changes

All changes are to ORM Python code only. The `init_db()` function calls `create_all()` which only creates tables that don't exist — removing columns from Python models does not drop columns from the SQLite database. A migration would be needed for that, but is out of scope since the removed columns were never populated.
