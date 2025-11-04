# Backend: running migrations

Problem
-------
If you run the migrations file directly like:

```powershell
python .\migrations\__init__.py
```

Python will put the `migrations` folder on sys.path (the script's directory), so sibling packages such as `app` cannot be imported and you get:

    ModuleNotFoundError: No module named 'app'

Recommended ways to run migrations (from the `backend` directory)
-------------------------------------------------------------

- Preferred (module mode):

```powershell
python -m migrations
```

- Convenience script (Powershell):

```powershell
.\run_migrations.ps1
```

- Convenience script (cross-platform Python):

```powershell
python run_migrations.py
```

Why these work
---------------
Running the package with `-m` ensures Python's sys.path contains the parent directory (the `backend` folder), so imports like `from app.db import DBManager` resolve correctly.

If you prefer, you can also run migrations from the repository root using the full package path:

```powershell
python -m backend.migrations
```
