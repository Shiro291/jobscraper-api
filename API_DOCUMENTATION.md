# Job Scraper API - Documentation

Comprehensive API documentation for all available job scraping endpoints.

## Base URL

```
http://localhost:8000
```

## Response Format

All endpoints return JSON responses in the following format:

### Success Response
```json
{
  "status": "success",
  "message": "Success message",
  "data": {
    // Response data here
  }
}
```

### Error Response
```json
{
  "status": "failed",
  "message": "Error message"
}
```

---

## Endpoints

### 1. Glints

Scrape job listings from Glints Indonesia.

**Endpoint:** `GET /api/glints`

**Query Parameters:**

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `work` | string | "Programmer" | No | Job title or keywords to search |
| `job_type` | string | "FULL_TIME" | No | Employment type |
| `option_work` | string | "ONSITE" | No | Work arrangement |
| `location_id` | string | "" | No | Location ID |
| `location_name` | string | "All+Cities/Provinces" | No | Location name |
| `page` | string | "1" | No | Page number |

**Valid Values:**

- `job_type`: `FULL_TIME`, `PART_TIME`, `CONTRACT`, `INTERNSHIP`
- `option_work`: `ONSITE`, `HYBRID`, `REMOTE`
- `location_name`: `All+Cities/Provinces`, `Jabodetabek`, `Banten`, `Jawa Barat`, `DKI Jakarta`, etc.

**Example Request:**
```bash
GET /api/glints?work=Software+Engineer&job_type=FULL_TIME&option_work=REMOTE&page=1
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Success find job",
  "data": {
    "jobs": [
      {
        "title": "Senior Software Engineer",
        "salary": "Rp 10.000.000 - Rp 15.000.000",
        "location": "Jakarta Selatan, DKI Jakarta",
        "company_name": "Tech Indonesia",
        "company_logo": "https://example.com/logo.png",
        "link": "https://glints.com/opportunities/jobs/123456"
      }
    ],
    "total_jobs": 25
  }
}
```

---

### 2. JobStreet

Scrape job listings from JobStreet (supports multiple countries).

**Endpoint:** `GET /api/jobstreet`

**Query Parameters:**

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `work` | string | "Programmer" | No | Job title or keywords |
| `location` | string | "" | No | City or region |
| `country` | string | "id" | No | Country code |
| `page` | string | "1" | No | Page number |

**Supported Countries:**
- `id` - Indonesia
- `my` - Malaysia
- `sg` - Singapore
- `th` - Thailand
- `hk` - Hong Kong
- `nz` - New Zealand
- `au` - Australia

**Example Request:**
```bash
GET /api/jobstreet?work=Flutter+Developer&location=Jakarta&country=id&page=1
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Success find job",
  "data": {
    "total_jobs": "150",
    "jobs": [
      {
        "title": "Flutter Developer",
        "company_name": "PT Tech Solutions",
        "company_logo": "https://example.com/logo.png",
        "salary": "Rp 8.000.000 - Rp 12.000.000",
        "location": "Jakarta Pusat, DKI Jakarta",
        "link": "https://id.jobstreet.com/id/job/123456"
      }
    ],
    "pagination": {
      "current_page": 1,
      "last_page": 15,
      "has_next": true
    },
    "suggestion_location": [
      {
        "location_name": "Jakarta Selatan",
        "url": "https://id.jobstreet.com/..."
      }
    ]
  }
}
```

---

### 3. RemoteOK

Scrape remote job listings from RemoteOK.

**Endpoint:** `GET /api/remoteok`

**Query Parameters:**

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `keywords` | string | "engineer" | No | Job keywords to search |
| `page` | string | "1" | No | Page number |

**Example Request:**
```bash
GET /api/remoteok?keywords=javascript&page=1
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Success scraping RemoteOK jobs",
  "data": {
    "jobs": [
      {
        "title": "Senior JavaScript Developer",
        "company_name": "Remote Tech Inc",
        "location": "🌏 Worldwide",
        "salary": "💰 $80k - $120k",
        "company_logo": "https://remoteok.com/assets/logo.png",
        "link": "https://remoteok.com/remote-jobs/123456"
      }
    ],
    "pagination": {
      "current_page": 1
    }
  }
}
```

---

### 4. Indeed

Scrape job listings from Indeed (supports multiple countries).

**Endpoint:** `GET /api/indeed`

**Query Parameters:**

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `keyword` | string | "programmer" | No | Job keywords |
| `location` | string | "" | No | Job location |
| `country` | string | "id" | No | Country code |
| `page` | string | "" | No | Page offset (multiples of 10) |

**Supported Countries:**
`id`, `nl`, `sa`, `jp`, `cn`, `fr`, `de`, `ar`, `ca`, `pt`, `co`, `mx`, `my`, `tw`, `in`, `uk`, `ru`, `es`, `it`

**Example Request:**
```bash
GET /api/indeed?keyword=python+developer&location=Jakarta&country=id&page=0
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Success scraping Indeed jobs",
  "data": {
    "jobs": [
      {
        "title": "Python Developer",
        "company": "PT Teknologi Digital",
        "location": "Jakarta",
        "sallary": "Rp 8.000.000 - Rp 15.000.000 per bulan",
        "link": "https://id.indeed.com/viewjob?jk=123456"
      }
    ],
    "pagination": {
      "current_page": 0,
      "last_page": 10,
      "next_page": 10
    }
  }
}
```

---

### 5. Disnaker Bandung

Scrape job listings from Disnaker Bandung (Indonesia local job board).

**Endpoint:** `GET /api/disnaker_bandung`

**Query Parameters:**

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `page` | string | "1" | No | Page number |

**Example Request:**
```bash
GET /api/disnaker_bandung?page=1
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Success scraping Disnaker Bandung jobs",
  "data": {
    "jobs": [
      {
        "company_logo": "https://disnaker.bandung.go.id/logo.png",
        "company_name": "PT Bandung Tech",
        "title": "Staff IT",
        "location": "Bandung, Jawa Barat",
        "salary": "Klik open untuk info gaji",
        "link": "https://disnaker.bandung.go.id/loker/detail/123"
      }
    ],
    "total_results": 250,
    "showing_start": 1,
    "showing_end": 20,
    "total_pages": 13,
    "current_page": 1,
    "is_last_page": false
  }
}
```

---

### 6. DevJobsScanner

Scrape developer job listings from DevJobsScanner.

**Endpoint:** `GET /api/devjobscanner`

**Query Parameters:**

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `keywords` | string | "web developer" | No | Job keywords |
| `page` | string | "1" | No | Page number |

**Example Request:**
```bash
GET /api/devjobscanner?keywords=react+developer&page=1
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Success find job",
  "data": {
    "jobs": [
      {
        "title": "React Developer",
        "salary": "USD 60,000 - 100,000",
        "location": "Remote",
        "company_name": "Tech Startup",
        "company_logo": "https://devjobsscanner.com/logo.png",
        "link": "https://www.devjobsscanner.com/job/123456"
      }
    ],
    "total_jobs": 45
  }
}
```

---

### 7. Health Check

Check if the API is running.

**Endpoint:** `GET /api/health`

**Example Request:**
```bash
GET /api/health
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Job Scraper API is running",
  "version": "2.0.0",
  "endpoints": {
    "glints": "/api/glints",
    "jobstreet": "/api/jobstreet",
    "remoteok": "/api/remoteok",
    "indeed": "/api/indeed",
    "disnaker_bandung": "/api/disnaker_bandung",
    "devjobscanner": "/api/devjobscanner"
  }
}
```

---

## Error Handling

The API returns appropriate HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (invalid endpoint)
- `500` - Internal Server Error

**Example Error Response:**
```json
{
  "status": "failed",
  "message": "Invalid job_type: INVALID. Valid options: FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP"
}
```

---

## Rate Limiting

Currently, there is no rate limiting implemented. However, please be respectful and avoid making too many concurrent requests to prevent being blocked by the target websites.

---

## Cookie Configuration

Some websites (Glints, JobStreet, Indeed) may require cookies for authentication or to bypass bot detection.

**Setup:**

1. Install [Cookie Editor](https://cookie-editor.cgagnier.ca/) browser extension
2. Visit the target website
3. Export cookies as JSON
4. Save to `src/config/{platform}.json`

**Cookie File Format:**
```json
[
  {
    "name": "session_id",
    "value": "abc123...",
    "domain": ".example.com",
    "path": "/",
    "secure": true,
    "httpOnly": true
  }
]
```

---

## Tips for Best Results

1. **Use specific keywords** - More specific searches yield better results
2. **Try different locations** - Some platforms have location-specific results
3. **Pagination** - Not all platforms return the same number of results per page
4. **Cookie refresh** - Update cookies periodically if scraping stops working
5. **Error handling** - Always check the `status` field in responses

---

## Support

For issues or questions:
- Check the GitHub repository issues
- Review the README.md for setup instructions
- Ensure all dependencies are properly installed

---

**Last Updated:** 2024
**API Version:** 2.0.0
