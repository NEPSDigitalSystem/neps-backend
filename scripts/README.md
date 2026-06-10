# NEPS Backend Scripts

## Seed Database from Mock Data

This script populates the database with realistic mock data from our RedCapMockClient.

### Prerequisites
1. Database is running (e.g., via docker compose up postgres)
2. Backend dependencies are installed (`pip install -r requirements.txt`)
3. `.env` file is configured (copy from `.env.example`)

### How to Run

```bash
# From neps-backend directory
python scripts/seed_from_mock.py
```

### Notes
- This script uses the same mock data that powers our mock REDCap endpoints
- Data includes 150 participants across 3 countries, 24 months of survey data, distress screenings, and WP6 intervention sessions
