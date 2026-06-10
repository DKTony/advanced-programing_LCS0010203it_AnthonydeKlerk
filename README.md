# NamLog Freight Tracker

NamLog is a Python desktop logistics management system for a Namibian freight company managing truck routes from Walvis Bay to SADC destinations. It demonstrates OOP, SQLAlchemy ORM persistence, a Flask REST API, threading, and a Tkinter GUI.

Author: Anthony de Klerk

GitHub repository URL: `https://github.com/DKTony/advanced-programing_LCS0010203it_AnthonydeKlerk`

## Setup

Prerequisites:

- Python 3.10 or newer
- Git
- Internet access for `pip install`

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the full desktop application:

```bash
python main.py
```

Run tests:

```bash
pytest
```

## Architecture

- `models.py` defines the OOP model hierarchy and SQLAlchemy ORM mappings.
- `api.py` exposes the REST API and owns all database access used by the GUI.
- `gui.py` implements a Tkinter dashboard that uses `requests` to call the API only.
- `main.py` starts Flask in a background thread and launches Tkinter on the main thread.
- `test_models.py` contains pytest coverage for model validation, persistence, singleton behavior, and API endpoints.

The GUI does not import or call the repository. This keeps the desktop interface decoupled from persistence and forces all data access through the Flask API.

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/trucks` | List all trucks |
| GET | `/api/trucks/<id>` | Fetch one truck |
| DELETE | `/api/trucks/<id>` | Delete one truck |
| GET | `/api/deliveries` | List deliveries |
| POST | `/api/deliveries` | Create a delivery |
| PUT | `/api/deliveries/<id>` | Update delivery status |

## Threading and Race Condition Note

`api.py` uses a module-level `threading.Lock` called `database_write_lock`. The Flask request handlers and the background manifest worker both acquire this lock before writing to SQLite.

If the lock is removed, a GUI user could submit a delivery at the same time the manifest worker inserts imported delivery records. In the NamLog context, those simultaneous commits could double-book the same truck, violate capacity checks, or trigger SQLite write-lock errors because two threads are trying to write through the same database file at once.

## GitHub Workflow Evidence

This is an individual submission by Anthony de Klerk because no group was available to join. The repository still follows the assignment's branch and Pull Request workflow as far as possible for an individual project:

- `main`: production-ready code only.
- `develop`: integration branch.
- Feature branches: `feature/orm-models`, `feature/api`, `feature/gui`.
- Code changes should enter through Pull Requests from feature branches into `develop`, then from `develop` into `main`.
- Because this is a single-member submission, reviewer comments may be replaced by self-review notes explaining the purpose and correctness of each PR.
- Add a `.gitignore` to the repository containing `__pycache__/`, `*.db`, `*.pyc`, and `.env`.

## Written Reflection

All reflection answers were authored by Anthony de Klerk.

### Threading vs Flask REST API Difficulty

Author: Anthony de Klerk. Threading was more difficult than the Flask REST API because errors can happen depending on timing rather than a fixed input. The API endpoints follow a clear request-response pattern, so they are easier to test with Flask's test client. The worker thread required more careful thinking because it runs while users may also be creating deliveries from the GUI. The lock was important because SQLite allows only controlled write access, and without it the application could fail under concurrent delivery creation. This made threading the part that required the most defensive design.

### GitHub Merge Conflicts

Author: Anthony de Klerk. Even though this became an individual submission, merge conflicts can still happen when work is split across multiple feature branches and the same files are edited in different branches. The feature branch workflow reduces this risk because each branch focuses on a smaller area, such as ORM models, API routes, or GUI work. If a conflict occurs, the best approach is to read both versions carefully and keep the code that preserves the agreed architecture. In a single-member project, self-review notes can replace group reviewer comments by explaining why each Pull Request is correct before merge. This workflow also makes it easier to trace which part of the system changed at each stage.

### ORM Architecture Decisions

Author: Anthony de Klerk. SQLAlchemy was used because it lets the Python classes remain close to the database tables while still supporting object-oriented validation. The repository class separates CRUD operations from Flask routes, which keeps the API handlers short and easier to test. Private attributes with property setters were used so invalid trucks and deliveries are rejected before they are committed. The singleton database manager keeps one shared engine configuration for the application lifetime. This structure makes it easier to add new domain classes later without rewriting the GUI.

### Namibian Community Impact

Author: Anthony de Klerk. NamLog can support Namibian logistics businesses by giving dispatchers a simple view of trucks, routes, and deliveries. Walvis Bay is an important freight gateway, so better tracking can help companies coordinate shipments into SADC countries more reliably. A small desktop system is also practical for businesses that do not yet need a large enterprise platform. By reducing manual tracking, the company can lower mistakes in truck assignment and delivery status updates. This can improve service reliability for importers, exporters, and communities that depend on regional freight movement.

### Scalability and Future-Proofing

Author: Anthony de Klerk. The current application uses SQLite because it is simple for a desktop assignment, but the repository pattern makes it possible to move to PostgreSQL later. The Flask API boundary is also useful because a future web or mobile frontend could call the same endpoints. More endpoints could be added for driver management, route pricing, maintenance records, and customer notifications. For larger usage, the background worker should move to a proper task queue and the API should use authentication. These changes would let NamLog grow from a class project into a more realistic logistics platform.
