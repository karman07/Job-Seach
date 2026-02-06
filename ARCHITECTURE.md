# System Architecture & Design Decisions

## Architecture Overview

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ Jobs API     │  │ Matching API │  │  Admin API  │  │
│  │ /jobs        │  │ /match/*     │  │ /admin/*    │  │
│  └──────────────┘  └──────────────┘  └─────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                  │
│  ┌──────────────┐         ┌──────────────────────────┐ │
│  │ JobService   │         │  MatchingService         │ │
│  │ - Sync jobs  │         │  - Resume matching       │ │
│  │ - CRUD ops   │         │  - JD matching           │ │
│  └──────────────┘         │  - Result caching        │ │
│                           └──────────────────────────┘ │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                    DATA ACCESS LAYER                    │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌─────────┐ │
│  │PostgreSQL│  │  Redis   │  │ Adzuna  │  │   CTS   │ │
│  │  (Jobs)  │  │ (Cache)  │  │   API   │  │   API   │ │
│  └──────────┘  └──────────┘  └─────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Why FastAPI?
- **High Performance**: Async support, fast request handling
- **Auto Documentation**: OpenAPI/Swagger built-in
- **Type Safety**: Pydantic models for validation
- **Modern Python**: Async/await, type hints
- **Production Ready**: Used by Netflix, Microsoft, Uber

### 2. Database Schema Design

**Jobs Table**:
- `adzuna_id`: External source ID (unique constraint)
- `cts_job_name`: Full CTS path for updates/deletes
- `requisition_id`: CTS requirement (globally unique)
- `status`: Soft delete pattern (active/expired/deleted)
- `expires_at`: Automatic job expiry tracking

**Indexes**:
- Composite index on (location, status) for filtered searches
- Index on expires_at for cleanup queries
- Index on adzuna_id for deduplication

**Why this approach?**:
- Prevents duplicate job insertions
- Enables incremental updates vs full refresh
- Tracks sync status for debugging
- Supports multi-tenancy if needed later

### 3. Scheduler: APScheduler vs Celery

**APScheduler (Default)**:
- ✅ Simpler setup
- ✅ In-process (no extra services)
- ✅ Perfect for single-server deployments
- ❌ No distributed task queue
- ❌ Loses tasks on crash

**Celery (Production)**:
- ✅ Distributed task queue
- ✅ Worker pooling and scaling
- ✅ Task retry and persistence
- ✅ Priority queues
- ❌ Requires Redis/RabbitMQ
- ❌ More complex setup

**Decision**: Provide both options, use APScheduler by default for simplicity.

### 4. Caching Strategy

**What to cache**:
- Resume search results (24-hour TTL)
- Reason: Same resume often searched multiple times
- Cache key: SHA256(resume + filters)

**What NOT to cache**:
- Job listings (data changes frequently)
- Admin operations
- Health checks

**Implementation**:
- Database-backed cache (resume_search_cache table)
- Scheduled cleanup of expired entries
- Consider Redis for high-traffic scenarios

### 5. Error Handling & Retries

**Adzuna API**:
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
```
- 3 attempts with exponential backoff
- Handles rate limits and transient failures

**CTS API**:
- Same retry logic
- Handles AlreadyExists gracefully
- Falls back on NotFound during updates

**Database**:
- Connection pooling with auto-reconnect
- Transaction isolation for sync operations

### 6. Job Matching Flow

```
Resume Text
    │
    ▼
┌─────────────────┐
│ Check Cache     │
│ (SHA256 hash)   │
└────┬────────────┘
     │
     ▼ Cache miss
┌─────────────────────────┐
│ CTS Search with Resume  │
│ - Profile-based ranking │
│ - Location filters      │
│ - Employment type       │
└────┬────────────────────┘
     │
     ▼
┌─────────────────────────┐
│ Map to Database Jobs    │
│ - Match requisition_id  │
│ - Filter by status      │
└────┬────────────────────┘
     │
     ▼
┌─────────────────────────┐
│ Apply Additional Filters│
│ - Job level             │
│ - Salary range          │
│ - Internship flag       │
└────┬────────────────────┘
     │
     ▼
┌─────────────────────────┐
│ Cache Results           │
│ Save for 24 hours       │
└────┬────────────────────┘
     │
     ▼
Return Ranked Jobs
```

### 7. Daily Refresh Idempotency

**Problem**: What if the daily refresh runs twice?

**Solution**:
1. Use `adzuna_id` as unique key
2. Upsert pattern: Create if not exists, update if exists
3. CTS handles duplicates via `requisition_id`
4. Sync log tracks each run separately

**Code**:
```python
existing_job = db.query(Job).filter(
    Job.adzuna_id == parsed_job["adzuna_id"]
).first()

if existing_job:
    update_job(existing_job, parsed_job)
else:
    create_job(parsed_job)
```

### 8. Job Expiry Strategy

**Options Considered**:

1. **Delete expired jobs**
   - ❌ Loses historical data
   - ✅ Smaller database

2. **Archive to separate table**
   - ✅ Preserves history
   - ❌ More complex queries

3. **Soft delete with status flag** ✅ CHOSEN
   - ✅ Simple queries with status filter
   - ✅ Can resurrect if job reappears
   - ✅ Historical analytics possible
   - ❌ Database growth over time

**Mitigation**: Add cleanup job to hard-delete jobs older than 90 days.

## Scaling Considerations

### 5,000 jobs/day → 50,000 jobs/day

**Bottlenecks**:

1. **Adzuna API Rate Limits**
   - Current: 50 results/page, ~1 request/second
   - Solution: Parallel fetching with rate limiting
   - Use multiple API keys if available

2. **CTS API Rate Limits**
   - Quota: 10,000 requests/day (default)
   - Solution: Batch job creation (100 at a time)
   - Request quota increase from Google

3. **Database Write Performance**
   - Current: Single-threaded inserts
   - Solution: Batch inserts with executemany()
   - Use COPY for bulk loads
   - Add read replicas for queries

4. **Search Performance**
   - CTS search: ~200-500ms per query
   - Solution: Aggressive caching
   - Pre-compute popular searches
   - Use cursor-based pagination

### Horizontal Scaling

**API Layer**:
```
         Load Balancer
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
  API-1     API-2     API-3
```

**Worker Layer** (Celery):
```
         Redis Queue
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
Worker-1  Worker-2  Worker-3
```

**Database**:
```
   Primary (writes)
        │
   ┌────┴────┐
   ▼         ▼
Replica-1 Replica-2 (reads)
```

## Edge Cases & Solutions

### 1. Job Posted to Multiple Locations
**Problem**: Same job, different locations in Adzuna
**Solution**: Each location = separate job entry (different adzuna_id)

### 2. Company Changes Name
**Problem**: CTS company lookup fails
**Solution**: Fallback to default company, log for manual review

### 3. Invalid Salary Data
**Problem**: Adzuna returns salary_min > salary_max
**Solution**: Validate and swap if needed, or set both to None

### 4. CTS Quota Exhausted
**Problem**: Daily quota limit reached
**Solution**: 
- Queue jobs for next day
- Prioritize high-quality jobs first
- Request quota increase

### 5. Database Connection Lost During Sync
**Problem**: Mid-sync crash leaves partial data
**Solution**:
- Use transactions for batch operations
- Sync log tracks progress
- Resume from last successful page

### 6. Duplicate Jobs from Adzuna
**Problem**: Same job appears multiple times
**Solution**: `adzuna_id` unique constraint prevents duplicates

### 7. Clock Skew in Scheduler
**Problem**: Servers in different timezones
**Solution**: All times in UTC, configure timezone in .env

## Monitoring & Alerts

### Key Metrics to Track

1. **Sync Metrics**:
   - Jobs fetched per sync
   - Success/failure ratio
   - Sync duration
   - API error rates

2. **API Metrics**:
   - Request latency (p50, p95, p99)
   - Error rate by endpoint
   - Cache hit ratio
   - Active connections

3. **Database Metrics**:
   - Connection pool usage
   - Query duration
   - Table sizes
   - Index usage

4. **Business Metrics**:
   - Total active jobs
   - Jobs by category/location
   - Search requests per day
   - Match quality (CTR on redirects)

### Alert Thresholds

- ⚠️  Warning: Sync takes >30 minutes
- 🚨 Critical: Sync fails 2 times in a row
- ⚠️  Warning: API latency >1 second (p95)
- 🚨 Critical: API error rate >5%
- ⚠️  Warning: Database connections >80% of pool
- 🚨 Critical: Database unreachable

## Security Best Practices

1. **API Keys**: Store in environment variables, never commit
2. **Database**: Use SSL connections, rotate passwords
3. **CTS**: Service account with minimal permissions
4. **Admin Endpoints**: Add authentication middleware
5. **Rate Limiting**: Implement per-IP rate limits
6. **Input Validation**: Pydantic models validate all inputs
7. **SQL Injection**: SQLAlchemy ORM prevents this
8. **CORS**: Configure allowed origins for production

## Cost Optimization

### Database
- Use connection pooling (reduces overhead)
- Index only necessary columns
- Archive old jobs to cold storage (S3/GCS)
- Use smaller instance during off-peak

### CTS API
- Batch operations
- Cache search results aggressively
- Use job expiry to auto-delete
- Consider search result size limits

### Adzuna API
- Fetch only changed jobs (if API supports)
- Use filters to reduce irrelevant jobs
- Cache category/location metadata

### Compute
- Auto-scale based on traffic
- Use spot/preemptible instances for workers
- Shutdown dev environments when not in use

## Future Enhancements

1. **Machine Learning**:
   - Train custom matching model
   - Personalized job recommendations
   - Salary prediction

2. **Real-time Updates**:
   - WebSocket for live job notifications
   - Server-sent events for match updates

3. **Advanced Search**:
   - Elasticsearch for full-text search
   - Faceted search (filters by category, etc.)
   - Geospatial search by distance

4. **Analytics**:
   - User behavior tracking
   - A/B testing for matching algorithms
   - Job market insights dashboard

5. **Multi-source**:
   - Support multiple job boards (LinkedIn, Indeed)
   - Unified job schema
   - Source ranking/quality scores
