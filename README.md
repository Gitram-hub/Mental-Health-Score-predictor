# AI Text-to-SQL Clarification Engine

Ask questions about a PostgreSQL dataset in plain English. The application
inspects the live database schema, detects ambiguous questions, asks for the
missing clarification, generates a read-only SQL query, executes it, and
returns a short natural-language answer.

This repository contains:

- A FastAPI backend
- A React/Vite chat frontend
- A PostgreSQL schema and sample dataset
- A command-line pipeline for local testing
- Groq-powered language-model services

## Why this project exists

A question such as **"Who is the best customer?"** has more than one valid
interpretation. It could mean the customer with the highest spending, the most
orders, or the highest average order value.

Instead of silently guessing, this project:

1. Detects ambiguity.
2. Asks a targeted clarification question.
3. Builds a resolved intent from the user's answers.
4. Generates a PostgreSQL `SELECT` query.
5. Validates that the query is read-only.
6. Executes it and explains the result.

## Features

- Live PostgreSQL schema introspection
- Sample values for low-cardinality text columns
- Multi-step clarification sessions persisted in PostgreSQL
- Groq LLM integration using `openai/gpt-oss-120b`
- Pydantic validation for structured LLM responses
- SQL parsing with `sqlglot`
- `SELECT`-only query validation
- Automatic SQL repair after database errors, with a retry limit
- FastAPI REST API
- React chat interface
- CLI workflow for quick local testing

## Architecture

```text
Question
   |
   v
Read PostgreSQL schema
   |
   v
Ambiguity detection -------- clear question --------+
   |                                                |
   v                                                v
Save clarification session                  Generate SQL
   |                                                |
   v                                                v
Answer clarification(s)                     Validate SELECT-only SQL
   |                                                |
   +---------------------> Generate SQL <------------+
                                                        |
                                                        v
                                                  Execute query
                                                        |
                                                        v
                                           Natural-language response
```

### Backend responsibilities

| Path | Responsibility |
| --- | --- |
| `app/api/routes.py` | FastAPI endpoints |
| `app/services/schema_service.py` | Reads tables, columns, types, and sample values |
| `app/services/ambiguity_service.py` | Detects missing intent details |
| `app/services/conversation_service.py` | Handles CLI clarification state |
| `app/services/session_service.py` | Persists API sessions in PostgreSQL |
| `app/services/sql_generator.py` | Generates and repairs SQL |
| `app/services/sql_validator.py` | Allows only parsed `SELECT` statements |
| `app/services/query_executor.py` | Executes validated SQL |
| `app/services/response_generator.py` | Converts query results to an answer |
| `app/services/db_connection.py` | Central PostgreSQL connection configuration |
| `app/services/llm_client.py` | Central Groq client configuration |

## Requirements

- Python 3.10 or newer
- PostgreSQL 14 or newer recommended
- Node.js 18 or newer for the frontend
- A Groq API key

## Installation on Windows

Open PowerShell in the repository root:

```powershell
cd "C:\Users\Byte_Ram\Desktop\projectss\mental health prediction"

py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation, you can skip activation and use the
interpreter directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configure environment variables

Copy [.env.example](./.env.example) to `.env` in the repository root.

Recommended format:

```env
DATABASE_URL=postgresql://postgres:<your_password>@localhost:5432/sql_query
GROQ_API_KEY=<your_groq_api_key>
```

The application also supports separate PostgreSQL variables:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sql_query
DB_USER=postgres
DB_PASSWORD=<your_password>
```

Use either `DATABASE_URL` or all five `DB_*` variables. Do not commit `.env`
or place `GROQ_API_KEY` in the frontend.

If an API key has been exposed, revoke it in the Groq console and create a
replacement.

## Create the database tables and seed data

Create the database once if it does not already exist:

```powershell
psql -U postgres -c "CREATE DATABASE sql_query;"
```

Run the SQL files in this order:

```powershell
psql -U postgres -d sql_query -f app\database\schema.sql
psql -U postgres -d sql_query -f app\database\sessions_schema.sql
psql -U postgres -d sql_query -f app\database\seed_data.sql
```

Then add the additional sample records:

```powershell
.\venv\Scripts\python.exe app\database\seed_v2.py
```

The schema creates:

```text
customers
orders
products
order_items
payments
```

The sessions schema creates:

```text
conversation_sessions
```

### Important seeding note

`seed_v2.py` is currently not idempotent. Running it again inserts duplicate
products, orders, order items, and payments. Run it once, or make the inserts
idempotent before using it in an automated deployment.

Verify the tables with:

```powershell
psql -U postgres -d sql_query -c "\dt"
```

## Run the backend

### FastAPI web API

```powershell
.\venv\Scripts\python.exe -m uvicorn app.api.routes:app --reload
```

The API is available at:

- API: <http://127.0.0.1:8000>
- Swagger UI: <http://127.0.0.1:8000/docs>

### CLI

```powershell
.\venv\Scripts\python.exe main.py
```

Then ask a question such as:

```text
Which customer spent the most on completed orders?
```

## Run the frontend

In a second PowerShell window:

```powershell
cd "C:\Users\Byte_Ram\Desktop\projectss\mental health prediction\frontend"
npm install
Copy-Item .env.example .env
npm run dev
```

Open <http://localhost:5173>.

The frontend uses `VITE_API_URL` from `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

## API reference

### `POST /ask`

Starts a question.

Request:

```json
{
  "question": "Who is the best customer?"
}
```

Possible clarification response:

```json
{
  "status": "clarification_needed",
  "session_id": "uuid",
  "aspect": "metric",
  "question": "What should define best?",
  "options": ["highest revenue", "most orders"]
}
```

If no clarification is needed, the response contains:

```json
{
  "status": "answered",
  "sql": "SELECT ...",
  "answer": "..."
}
```

### `POST /answer`

Submits an answer for a clarification session.

```json
{
  "session_id": "uuid",
  "answer": "highest revenue"
}
```

The response either asks the next clarification or returns the final answer.

### `GET /dataset-summary`

Returns counts and sample records from the dataset.

Example:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/dataset-summary
```

## Security model

The current application has a basic read-only protection layer:

- The LLM is instructed to generate `SELECT` statements only.
- `sqlglot` parses the generated SQL.
- Non-`SELECT` statements are rejected before execution.
- Database credentials and the Groq key are loaded from environment variables.

This is suitable for a controlled demo, not an unrestricted production
database. Use a PostgreSQL role with read-only permissions for the query
executor.

## Troubleshooting

### `fe_sendauth: no password supplied`

Check that `.env` contains a valid `DATABASE_URL`, or all five `DB_*`
variables. The username and password must match the PostgreSQL role.

### `relation "customers" does not exist`

The schema has not been applied to the selected database. Run:

```powershell
psql -U postgres -d sql_query -f app\database\schema.sql
```

### `GROQ_API_KEY is not configured`

Make sure `.env` is in the repository root, contains `GROQ_API_KEY`, and that
the backend is started from the project root.

### `psql is not recognized`

Run `psql.exe` using its full installation path, for example:

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d sql_query -f app\database\schema.sql
```

Change `16` to your installed PostgreSQL version.

## Testing and checks

Backend syntax check:

```powershell
.\venv\Scripts\python.exe -m compileall app main.py
```

Frontend lint and production build:

```powershell
cd frontend
npm run lint
npm run build
```

The repository currently has no dedicated automated backend test suite.

## Deployment outline

For deployment, use:

1. A managed PostgreSQL provider.
2. A Python web service running:

   ```text
   uvicorn app.api.routes:app --host 0.0.0.0 --port $PORT
   ```

3. A static frontend host running `npm run build`.
4. Environment variables configured in the hosting platform, never committed
   to Git.
5. The deployed frontend origin added to the backend CORS allowlist.

See [deployment.md](./deployment.md) for the existing deployment checklist.

## What would make this project better?

### Highest priority

1. **Add automated tests.** Test SQL validation, schema discovery, session
   progression, invalid session IDs, and API responses.
2. **Make seeding idempotent.** Use stable keys and `ON CONFLICT` or a reset
   command so deployment and local setup are repeatable.
3. **Use a read-only database role.** SQL validation is defense in depth, not a
   replacement for database permissions.
4. **Improve API error responses.** Return consistent HTTP errors instead of
   exposing raw database or provider exceptions.
5. **Remove hard-coded CORS origins.** Read allowed origins from an environment
   variable and configure them per environment.

### Production reliability

6. Add request timeouts and retry/backoff handling for Groq calls.
7. Add structured logging and request/session IDs.
8. Add rate limiting and authentication before exposing the API publicly.
9. Add a cleanup policy for old `conversation_sessions` rows.
10. Close database resources with context managers and add connection pooling.

### Query quality

11. Validate that referenced tables and columns exist before execution.
12. Add a result-size limit and query timeout.
13. Add deterministic ordering for every ranking query.
14. Add SQL-generation evaluation cases with expected intent and query
    properties.
15. Cache the schema briefly instead of introspecting PostgreSQL on every
    request.

### User experience

16. Show query execution errors as useful messages in the frontend.
17. Add loading, retry, and empty-result states.
18. Add an option to display the generated SQL with a copy button.
19. Preserve conversation history in the UI.
20. Add accessibility checks and responsive mobile layouts.

## License

Add a license before publishing or accepting external contributions.
