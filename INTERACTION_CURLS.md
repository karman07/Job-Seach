# User Interaction API CURLs

This document provides CURL commands for Managing **Bookmarks** and **Favorites**.

## Base URL
```bash
http://localhost:8000
```

---

## 1. Favorites

### Toggle Favorite
Add or remove a job from a user's favorites. This is a toggle endpoint; if the job is already a favorite, it will be removed.
```bash
curl -X POST http://localhost:8000/69987b7ef0d8faf4cdc83809/favorite \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123"
  }'
```
**Success Response:**
```json
{
  "message": "Job added to favorites",
  "status": "success",
  "is_active": true
}
```

### Get User Favorites
Retrieve all jobs favorited by a specific user.
```bash
curl -X GET "http://localhost:8000/favorites?user_id=user_123"
```
**Success Response:**
```json
{
  "total": 1,
  "jobs": [
    {
      "job_id": "69987b7ef0d8faf4cdc83809",
      "adzuna_id": "5637855679",
      "title": "Senior Software Engineer",
      "company": "Endian AI",
      "location": "Hyderabad, Telangana",
      "employment_type": "FULL_TIME",
      "description": "...",
      "redirect_url": "...",
      "relevance_score": 0.0,
      "is_internship": false
    }
  ]
}
```

---

## 2. Bookmarks

### Toggle Bookmark
Add or remove a job from a user's bookmarks. This is a toggle endpoint; if the job is already bookmarked, it will be removed.
```bash
curl -X POST http://localhost:8000/69987b7ef0d8faf4cdc83809/bookmark \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123"
  }'
```
**Success Response:**
```json
{
  "message": "Job added to bookmarks",
  "status": "success",
  "is_active": true
}
```

### Get User Bookmarks
Retrieve all jobs bookmarked by a specific user.
```bash
curl -X GET "http://localhost:8000/bookmarks?user_id=user_123"
```
**Success Response:**
```json
{
  "total": 1,
  "jobs": [
    {
      "job_id": "69987b7ef0d8faf4cdc83809",
      "adzuna_id": "5637855679",
      "title": "Senior Software Engineer",
      "company": "Endian AI",
      "location": "Hyderabad, Telangana",
      "employment_type": "FULL_TIME",
      "description": "...",
      "redirect_url": "...",
      "relevance_score": 0.0,
      "is_internship": false
    }
  ]
}
```
