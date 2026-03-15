# Python/Django Test Writer - Agent Memory

## Project: mezivus-directory

- Django 6.0.2, SQLite, USE_TZ=True
- App: `tracker`, model: `Package`
- Test runner: `python manage.py test` (Django built-in, no pytest configured)
- No factory_boy installed; use `Package.objects.create()` helper functions instead

## Key Patterns Confirmed in This Project

### max_length validation requires full_clean()
Django's `CharField(max_length=...)` is NOT enforced by SQLite on `save()`.
Always call `instance.full_clean()` in max_length tests and assert `ValidationError`.
Never call `save()` to test max_length — it will silently succeed on SQLite.

### Uniqueness IS enforced at the DB layer
`unique=True` on a CharField raises `IntegrityError` on `save()` (not `full_clean()`).
Test uniqueness by calling `objects.create()` inside `assertRaises(IntegrityError)`.

### Testing auto_now vs auto_now_add
- `auto_now_add`: set once on INSERT, never updated. Check `created_at` is unchanged after `save()`.
- `auto_now`: updated on every `save()`. Use `time.sleep(0.05)` + `refresh_from_db()` to observe change.
- `refresh_from_db()` is required after `save()` to read the DB-side updated timestamp.

### USE_TZ=True means datetimes are timezone-aware
Assert `instance.created_at.tzinfo is not None` when USE_TZ=True.

### make_package() helper pattern
Define a module-level `make_package(**kwargs)` with sensible defaults. Tests override only the field they care about. Keeps tests focused and DRY without requiring factory_boy.

### Boundary tests for max_length
Always write both the "over limit raises error" test AND the "at exact limit passes" test.
The at-limit test guards against off-by-one errors in field definitions.
