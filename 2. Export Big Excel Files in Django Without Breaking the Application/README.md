# Export Large CSV Files in Django Without Breaking the Application

This demonstration project compares two approaches to exporting millions of rows from Django and PostgreSQL:

- **V1 — in-memory export:** loads the `QuerySet` and builds the complete CSV in a `StringIO` before returning the response.
- **V2 — memory-efficient export:** reads PostgreSQL in chunks, writes the CSV to temporary storage, and returns it through `FileResponse`.

The goal is to show how an apparently simple implementation can work for an isolated request and still bring down the workers when several exports run concurrently.

## Main result

The benchmark used 5,000,000 rows, four simultaneous requests, four Gunicorn workers, and a shared 4 GB memory limit for the web container.

| Metric | V1: in memory | V2: bounded memory |
|---|---:|---:|
| Simultaneous requests | 4 | 4 |
| Completed exports | **0/4** | **4/4** |
| Peak memory | **4,096 MiB (100%)** | **213.30 MiB (5.21%)** |
| Average memory | 3,254.20 MiB | 208.68 MiB |
| Peak CPU | 389.11% | 160.38% |
| Average CPU | 44.81% | 99.08% |
| Total observed duration | 304.80 s | **153.83 s** |
| OOM kill | **Yes** | **No** |
| Workers lost | 4 | 0 |
| Client errors | 4 | 0 |

V2 reduced peak memory by approximately **94.8%**. Each resulting V2 CSV was 345,000,028 bytes, or about 329 MiB.

![Peak and average memory used by V1 and V2](docs/images/benchmark-memory.svg)

![Completed requests and observed duration for V1 and V2](docs/images/benchmark-outcomes.svg)

## How it works

### V1: build everything in RAM

V1 calls `values_list()`, passes the `QuerySet` directly to `writerows()`, and stores the result in a `StringIO`. It then calls `getvalue()` to build the HTTP response.

This keeps several large structures in memory at the same time:

1. Materialized rows stored in the `QuerySet` cache.
2. The Python objects associated with those rows.
3. The complete CSV contents.
4. Additional copies created while building the HTTP response.

One isolated request with 5 million rows reached a peak of **3,550.21 MiB**, or 86.7% of the container limit. With four concurrent requests, the container reached 4,096 MiB and Linux began killing workers.

### V2: iterate and write in chunks

V2 uses:

```python
queryset.values_list(*EXPORT_COLUMNS).iterator(chunk_size=5_000)
```

Rows are read in chunks and written directly to a temporary file. The process does not need to retain the complete dataset or CSV in RAM. Once generation finishes, Django returns a `FileResponse` that streams the file to the client.

Every export receives a unique `BucketLocal` key, so concurrent requests can write independently without overwriting one another.

## Architecture

```text
HTTP client
    │
    ▼
Gunicorn: 4 workers, 1 thread per worker
    │
    ▼
Django REST Framework
    ├── V1 → complete QuerySet → StringIO → HttpResponse
    └── V2 → iterator(5,000) → BucketLocal → FileResponse
                    │
                    ▼
                PostgreSQL

Redis ── Celery worker
```

The synchronous V2 endpoint remains available for a direct benchmark against V1. The production-oriented V2 flow submits the same memory-efficient export function to Celery, returns HTTP 202 immediately, exposes job status through Redis, and provides a download endpoint when the file is ready.

## Project structure

```text
.
├── config/
│   ├── celery.py                  # Celery initialization and configuration
│   ├── settings.py                # Django, PostgreSQL, DRF, and Celery
│   ├── test_settings.py           # SQLite and eager Celery tests
│   ├── urls.py                    # Root URL configuration
│   └── wsgi.py                    # WSGI entry point for Gunicorn
├── core/
│   └── bucket/
│       ├── bucketBase/            # Abstract storage contract
│       └── bucketLocal/           # Local-disk implementation
├── csv_export/
│   ├── management/commands/
│   │   └── seed_examples.py       # Creates 5 million rows through COPY
│   ├── constants.py               # Columns, filenames, and content type
│   ├── models.py                  # Models used by the benchmarks
│   ├── serializers.py             # Filter and filename validation
│   ├── services.py                # Shared memory-efficient export service
│   ├── tasks.py                   # Celery export and health-check tasks
│   ├── urls.py                    # Export endpoints
│   └── views.py                   # V1 and V2 implementations
├── scripts/
│   └── ...                        # Internal helpers used by run_stress_test.bat
├── compose.yaml                   # Redis, Gunicorn, and Celery worker
├── Dockerfile
├── manage.py
├── run_stress_test.bat            # Single entry point for V1/V2 stress tests
├── start_services.bat             # Starts the Docker Compose services
├── requirements.txt
└── README.md
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/csv/examples/export/v1/` | Complete in-memory export |
| `GET` | `/csv/examples/export/v2/` | Temporary-file export |
| `POST` | `/csv/examples/export/v2/jobs/` | Queue a memory-efficient Celery export |
| `GET` | `/csv/examples/export/v2/jobs/{task_id}/` | Check export status |
| `GET` | `/csv/examples/export/v2/jobs/{task_id}/download/` | Download a completed export |
| `GET` | `/csv/examples/lightweight/v1/` | Small control export |

The main endpoints accept:

- `filename`: optional CSV filename.
- `col_a`, `col_b`, `col_c`, `col_d`: optional exact-match filters.

Examples:

```text
http://localhost:8000/csv/examples/export/v1/?filename=examples.csv
http://localhost:8000/csv/examples/export/v2/?filename=examples.csv
http://localhost:8000/csv/examples/export/v2/?col_a=abc&filename=filtered.csv
```

### Asynchronous Celery flow

Queue an export. Filters and `filename` use the same validation as the synchronous endpoints:

```bash
curl -X POST http://localhost:8000/csv/examples/export/v2/jobs/ \
  -H "Content-Type: application/json" \
  -d '{"filename":"examples.csv","col_a":"abc"}'
```

The API responds immediately with HTTP 202:

```json
{
  "id": "682daa1c-89a1-4a2e-ae90-19a1db2ff14b",
  "state": "PENDING",
  "status_url": "http://localhost:8000/csv/examples/export/v2/jobs/682daa1c-89a1-4a2e-ae90-19a1db2ff14b/"
}
```

Poll `status_url`. A successful job includes `download_url`:

```json
{
  "id": "682daa1c-89a1-4a2e-ae90-19a1db2ff14b",
  "state": "SUCCESS",
  "download_url": "http://localhost:8000/csv/examples/export/v2/jobs/682daa1c-89a1-4a2e-ae90-19a1db2ff14b/download/"
}
```

The download streams the completed CSV and removes the temporary file when the response closes.

## Requirements

- Docker Desktop and Docker Compose.
- A PostgreSQL server accessible from the host.
- Windows PowerShell to run `run_stress_test.bat`.

The `compose.yaml` file runs Redis, Django/Gunicorn, and Celery. PostgreSQL is not created by Compose: the container reaches the host database through `host.docker.internal`.

## Configuration

Copy `.env.example` to `.env` and update the credentials:

```powershell
Copy-Item .env.example .env
```

Main variables:

```dotenv
DJANGO_SECRET_KEY=change-me
POSTGRES_DB=big_excel
POSTGRES_USER=big_excel_user
POSTGRES_PASSWORD=change-me
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_CONNECT_TIMEOUT=5
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

Docker overrides the PostgreSQL host with `host.docker.internal` and points the Redis URLs at the `redis` service.

## Running the project

Build and start the services:

```powershell
docker compose up -d --build redis web worker
```

Apply the migrations:

```powershell
docker compose exec web python manage.py migrate
```

Generate the reproducible 5-million-row dataset:

```powershell
docker compose exec web python manage.py seed_examples
```

The command uses PostgreSQL `COPY`, seed 42, and replaces the existing data. A different row count can be supplied:

```powershell
docker compose exec web python manage.py seed_examples --count 1000000
```

Run the isolated test suite without requiring PostgreSQL database-creation privileges:

```powershell
.\.venv\Scripts\python.exe manage.py test csv_export --settings=config.test_settings
```

## Running the benchmarks

`run_stress_test.bat` is the single entry point for both stress scenarios. Run it without arguments to open an interactive menu:

```bat
run_stress_test.bat
```

You can also select the endpoint directly.

Run the in-memory V1 stress test:

```bat
run_stress_test.bat v1
```

Run the memory-efficient V2 stress test:

```bat
run_stress_test.bat v2
```

The launcher performs the complete workflow automatically:

1. Checks that Docker is installed and Docker Desktop is running.
2. Validates the selected endpoint version.
3. Restarts the web container to clear memory retained by previous runs.
4. Waits until Gunicorn responds successfully.
5. Starts four concurrent export requests.
6. Samples CPU, memory, network I/O, and process counts with `docker stats`.
7. Records one output file and error log per request.
8. Prints a summary with peak and average resource usage.
9. Reports completed exports, OOM state, exit code, and restart count.
10. Shows only the relevant Gunicorn events generated during the current test.

The batch file delegates concurrent execution to `scripts/stress_concurrent.ps1` and summary generation to `scripts/summarize_stress_metrics.ps1`. These PowerShell scripts are implementation details and normally do not need to be called directly.

### Generated artifacts

Each run replaces artifacts from an earlier run of the same version:

```text
v1-5m-concurrent-metrics.csv
v1-5m-concurrent-1.csv ... v1-5m-concurrent-4.csv
v1-5m-concurrent-1-error.log ... v1-5m-concurrent-4-error.log

v2-5m-concurrent-metrics.csv
v2-5m-concurrent-1.csv ... v2-5m-concurrent-4.csv
v2-5m-concurrent-1-error.log ... v2-5m-concurrent-4-error.log
```

The metrics CSV contains one sample per monitoring interval:

```csv
timestamp,cpu_percent,memory_usage,net_io,pids
```

Generated CSV files, metrics, and request logs match `/v*-5m*.csv` and `/v*-5m*.log` in `.gitignore`, so benchmark artifacts are not committed accidentally.

## Benchmark methodology

- Host machine: 12 visible logical processors.
- Web container: hard 4 GB memory limit.
- Gunicorn: 4 synchronous workers and 1 thread per worker.
- Timeout: 300 seconds.
- Dataset: 5,000,000 rows.
- Exported columns: four pseudorandom 16-character strings.
- Concurrency: four `curl` clients started at nearly the same time, one for each Gunicorn worker.
- Isolation: the web container is restarted before every scenario.
- Metrics: `docker stats` samples throughout execution, individual client results, container state, and Gunicorn logs.

## Benchmark observations

The single result table and charts at the top of this README come from the latest complete run of `run_stress_test.bat`. Execution time depends on PostgreSQL, host load, Docker, and disk performance. Memory behavior is the important invariant: V1 reaches the container limit, while V2 remains close to 200 MiB with the same concurrency and dataset.

### Observed V1 failure

V1 reached the complete 4 GB container limit. All four clients received:

```text
curl: (52) Empty reply from server
```

No CSV was completed. Gunicorn reported worker timeouts and workers terminated with `SIGKILL`, while Docker recorded `oom_killed=true`. The master process survived and created replacement workers, but that recovery did not rescue the failed user requests.

### Observed V2 behavior

V2 completed all four requests without client errors. Every downloaded CSV was 345,000,028 bytes, and each error log was empty. The container remained healthy:

```text
status=running
oom_killed=false
exit_code=0
restart_count=0
```

The three-byte difference compared with the V1 CSV size comes from the UTF-8 BOM written by V2 through `utf-8-sig`.

## Reading the metrics

The console summary is intended to answer four questions immediately:

- **Did all requests complete?** Check `Completed exports` and the per-request table.
- **Did memory remain bounded?** Compare `Peak memory` with the 4,096 MiB limit.
- **Did Docker kill a process?** Check `oom_killed` and the Gunicorn event section.
- **Were output files valid?** Successful requests have a non-zero byte count and an empty error field.

CPU percentages can exceed 100% because Docker reports usage across multiple logical processors. For example, 389% represents approximately 3.89 fully utilized logical CPU cores.

## Production considerations

V2 solves the memory problem, and the Celery API removes long-running generation from the HTTP request. Several operational decisions remain:

- **File cleanup:** downloaded files are removed when the response closes. A periodic expiration policy is still required for completed jobs that users never download.
- **HTTP timeout:** benchmark duration varies with host and storage load. Large synchronous exports can still approach the configured 300-second timeout.
- **Result retention:** align Celery result expiration with temporary-file retention so job status and file availability expire together.
- **Shared storage:** local disk works on one host. Multiple replicas should use object storage such as S3, Azure Blob Storage, or an equivalent service.
- **Concurrency limits:** even with stable memory, PostgreSQL and the disk must handle four large concurrent reads and writes.
- **Disk capacity:** four successful V2 requests create roughly 1.38 GB in `BucketLocal`, in addition to the four client downloads.
- **Security:** configure `DEBUG`, `ALLOWED_HOSTS`, secrets, and credentials appropriately outside a demonstration environment.

## Conclusion

Adding more workers does not fix an export that materializes the complete dataset. It only allows several copies of the same memory usage to occur simultaneously.

Combining `QuerySet.iterator()`, incremental file writing, and `FileResponse` keeps memory nearly constant and allows four concurrent exports to complete within the same 4 GB limit. The full comparison can be reproduced from a clean container with `run_stress_test.bat v1` followed by `run_stress_test.bat v2`.
