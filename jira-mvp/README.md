# Tracker MVP

A small Jira-style issue tracker: Django + Django REST Framework backend and a
single-page Kanban board (vanilla JS, no build step).

## Features
- Register / log in (token auth)
- Projects with a key (`PROJ`) and members; issues are numbered `PROJ-1`, `PROJ-2`, …
- Issues: type (task/bug/story), priority, assignee, reporter, description, labels
- Workflow: To Do ⇄ In Progress ⇄ Done (To Do → Done directly is rejected)
- Drag-and-drop Kanban board
- Comments and a per-issue change history
- Filters (type, priority, assignee) and free-text search

Not included: sprints/backlog, custom workflows, JQL, notifications, attachments, roles.

## Run locally (SQLite)
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver        # http://localhost:8000
```

## Run with Docker (Postgres)
```bash
docker compose up --build         # http://localhost:8000
```

## Tests
```bash
python manage.py test
```

## API (all under `/api/`, header `Authorization: Token <token>`)
| Method | Path | Purpose |
|---|---|---|
| POST | `auth/register/`, `auth/login/` | get a token |
| GET/POST | `projects/` | list your projects / create one |
| GET/PATCH | `projects/<KEY>/` | project detail (edit: owner only) |
| POST | `projects/<KEY>/members/` | add member by `username` (owner only) |
| GET/POST | `projects/<KEY>/issues/` | list (`?status&type&priority&assignee&q`) / create |
| GET/PATCH/DELETE | `projects/<KEY>/issues/<n>/` | issue detail |
| GET/POST | `projects/<KEY>/issues/<n>/comments/` | comments |
| GET | `projects/<KEY>/issues/<n>/activity/` | change history |

Non-members get 404 for a project's resources.

## Notes
Dev defaults only (`SECRET_KEY`, `DEBUG=1`, `ALLOWED_HOSTS=*`); set the env vars
`SECRET_KEY`, `DEBUG=0`, `ALLOWED_HOSTS` before any real deployment.
