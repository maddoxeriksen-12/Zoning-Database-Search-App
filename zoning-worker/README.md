# Zoning PDF Worker (Supabase)

This worker pulls queued PDF ingestion jobs, extracts zoning tables, normalizes headers, parses values, and ingests rows via the `admin_ingest_zone_payload` RPC.

## Prereqs
- Supabase project with:
  - Tables: `ingestion_jobs`, `raw_extractions`, `review_tasks` (from earlier SQL)
  - Functions: `admin_ingest_zone_payload(jsonb)` and your schema/RLS
- Service Role key (for server-side writes)

## Configure
1) Copy `.env.example` → `.env` and fill `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
2) (Optional) Customize profiles in `worker/profiles/*.yml`.

## Run locally (Docker)
```bash
cd docker
docker compose build
docker compose up -d
docker compose logs -f
