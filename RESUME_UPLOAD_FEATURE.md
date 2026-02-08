# Resume Upload & Matching Feature

## Overview

The resume upload endpoint allows you to upload your resume file (PDF, DOCX, or TXT) and automatically get matched with relevant jobs from the database.

## New Endpoint

**`POST /match/resume/upload`**

Upload a resume file and get AI-powered job matches.

## Features

- ✅ **Multiple Format Support**: PDF, DOCX, and TXT files
- ✅ **Automatic Text Extraction**: Intelligently parses resume content
- ✅ **Smart Matching**: Uses existing AI matching service
- ✅ **Flexible Filters**: Location, job level, salary, internship options
- ✅ **Fast Processing**: Typically processes in under 1 second

## Quick Start

### 1. Install New Dependencies

First, install the resume parsing libraries:

```bash
pip install -r requirements.txt
```

This adds:
- `pypdf2==3.0.1` - For PDF parsing
- `python-docx==1.1.0` - For DOCX parsing

### 2. Start the API

```bash
python quickstart.py
# or
./run.sh
```

### 3. Test with Your Resume

Using the test script:

```bash
python test_resume_upload.py /path/to/your/resume.pdf
```

Using curl:

```bash
curl -X POST http://localhost:8000/match/resume/upload \
  -F "file=@/path/to/your/resume.pdf"
```

Using Python:

```python
import requests

with open('resume.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/match/resume/upload',
        files=files
    )
    print(response.json())
```

## API Usage

### Basic Upload

```bash
curl -X POST http://localhost:8000/match/resume/upload \
  -F "file=@resume.pdf"
```

### With Filters

```bash
curl -X POST "http://localhost:8000/match/resume/upload?location=San%20Francisco&job_level=ENTRY_LEVEL&stipend_min=80000" \
  -F "file=@resume.pdf"
```

### Query Parameters (All Optional)

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `location` | string | Preferred job location | `San Francisco, CA`, `Remote` |
| `internship_only` | boolean | Filter for internships only | `true`, `false` (default) |
| `job_level` | enum | Preferred job level | `ENTRY_LEVEL`, `MID_LEVEL`, `SENIOR_LEVEL`, `EXECUTIVE` |
| `stipend_min` | float | Minimum salary/stipend (USD) | `80000`, `120000` |

## Supported File Formats

| Format | Extension | Max Size |
|--------|-----------|----------|
| PDF | `.pdf` | 10MB |
| Word Document | `.docx` | 10MB |
| Plain Text | `.txt` | 10MB |

## Response Format

```json
{
  "total_matches": 12,
  "search_time_ms": 523.8,
  "jobs": [
    {
      "job_id": "65f1a2b3c4d5e6f7g8h9i0j1",
      "adzuna_id": "4567890",
      "title": "Software Engineer - Python",
      "company": "Tech Company",
      "location": "San Francisco, CA",
      "employment_type": "FULL_TIME",
      "salary_min": 110000,
      "salary_max": 150000,
      "description": "...",
      "redirect_url": "https://adzuna.com/job/...",
      "relevance_score": 0.92,
      "is_internship": false
    }
  ],
  "metadata": {
    "filename": "resume.pdf",
    "file_type": "application/pdf",
    "location": "San Francisco, CA",
    "internship_only": false,
    "job_level": "ENTRY_LEVEL",
    "stipend_min": 80000
  }
}
```

## Error Handling

The endpoint provides clear error messages:

### Invalid File Format
```json
{
  "detail": "Invalid file extension. Allowed: .pdf, .docx, .txt"
}
```

### File Too Large
```json
{
  "detail": "File too large. Maximum size is 10.0MB"
}
```

### Empty Resume
```json
{
  "detail": "Resume text is too short or empty. Please upload a valid resume with at least 50 characters."
}
```

## Architecture

The implementation consists of three main components:

### 1. Resume Parser (`app/utils/resume_parser.py`)
- Validates file type and size
- Extracts text from PDF, DOCX, and TXT files
- Handles multiple text encodings
- Provides detailed error messages

### 2. API Endpoint (`app/api/jobs.py`)
- New endpoint: `POST /match/resume/upload`
- Accepts file uploads via multipart/form-data
- Supports optional query parameters
- Returns job matches with metadata

### 3. Matching Service (Existing)
- Reuses existing `MatchingService`
- AI-powered job matching
- Relevance scoring
- Smart filtering

## Testing

### Test Script

Use the provided test script:

```bash
python test_resume_upload.py /path/to/resume.pdf
```

### Manual Testing

1. **PDF Resume**:
   ```bash
   curl -X POST http://localhost:8000/match/resume/upload \
     -F "file=@resume.pdf"
   ```

2. **DOCX Resume with Filters**:
   ```bash
   curl -X POST "http://localhost:8000/match/resume/upload?location=Remote&internship_only=true" \
     -F "file=@resume.docx"
   ```

3. **TXT Resume**:
   ```bash
   curl -X POST http://localhost:8000/match/resume/upload \
     -F "file=@resume.txt"
   ```

## Interactive API Documentation

View and test the endpoint in the Swagger UI:

1. Start the API: `python quickstart.py`
2. Open browser: http://localhost:8000/docs
3. Find "POST /match/resume/upload" endpoint
4. Click "Try it out"
5. Upload your resume file
6. Execute and see results

## Postman Collection

The endpoint is included in the Postman collection. Import:
- `Job_Matching_API.postman_collection.json`

Add a new request:
- Method: POST
- URL: `{{base_url}}/match/resume/upload?location=San Francisco&job_level=ENTRY_LEVEL`
- Body: form-data
  - Key: `file`
  - Type: File
  - Value: Select your resume file

## Tips for Best Results

1. **Use detailed resumes**: More content = better matching
2. **Include keywords**: Skills, technologies, job titles
3. **Specify location**: Get more relevant local jobs
4. **Set filters**: Use `job_level` and `stipend_min` to narrow results
5. **Try different formats**: PDF usually works best for formatted resumes

## Troubleshooting

### Problem: "Cannot connect to API"
**Solution**: Make sure the API is running on port 8000
```bash
python quickstart.py
```

### Problem: "Failed to parse PDF"
**Solution**: Try converting to DOCX or TXT format

### Problem: "No matches found"
**Solution**: 
- Remove filters to see more results
- Make sure your resume has relevant content
- Check if jobs are available in the database

### Problem: "File too large"
**Solution**: Compress your PDF or remove images/graphics

## Next Steps

- See [API_EXAMPLES.md](API_EXAMPLES.md) for more usage examples
- Check [QUICKSTART.md](QUICKSTART.md) for API setup
- View [ARCHITECTURE.md](ARCHITECTURE.md) for technical details

## Support

For issues or questions:
1. Check the error message in the API response
2. Review logs in the terminal where API is running
3. Test with the provided test script
4. Try the interactive docs at http://localhost:8000/docs
