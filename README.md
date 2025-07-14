# URL Shortener Microservice

A minimal Flask-based URL shortener microservice with SQLite storage and automatic expiration.

## Design Decisions

### Technology Stack
- **Framework**: Flask - lightweight, fast, minimal overhead
- **Database**: SQLite - embedded, no external dependencies, perfect for microservices
- **Storage**: File-based SQLite database (`urls.db`)

### Data Model
```sql
CREATE TABLE urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    long_url TEXT NOT NULL,
    shortcode TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
)
```

### Key Features
- 6-character alphanumeric shortcodes (62^6 = ~56 billion combinations)
- Automatic expiration with configurable validity
- Custom shortcode support
- Unique constraint enforcement
- Proper HTTP status codes for different scenarios

### Logging Strategy
- No console logging as per requirements
- Assumes custom logging middleware exists
- Clean error responses with appropriate HTTP codes

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Start the server
```bash
python app.py
```

Server runs on `http://localhost:5000`

### API Endpoints

#### POST /shorten
Create a shortened URL

```bash
curl -X POST http://localhost:5000/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "long_url": "https://example.com/very/long/url",
    "validity_in_minutes": 60,
    "custom_shortcode": "abc123"
  }'
```

Response:
```json
{
  "short_url": "http://localhost:5000/abc123",
  "shortcode": "abc123"
}
```

#### GET /:shortcode
Redirect to original URL

```bash
curl -L http://localhost:5000/abc123
```

#### GET /health
Health check endpoint

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00"
}
```

## Error Handling

- **400**: Missing required fields or invalid shortcode format
- **404**: Shortcode not found
- **409**: Custom shortcode already exists
- **410**: URL has expired

## Assumptions

- All users are authorized (no authentication required)
- Custom logging middleware handles application logging
- SQLite database is sufficient for the use case
- 6-character shortcodes provide adequate uniqueness
- 30-minute default expiration is reasonable

## Folder Structure

```
url-shortener/
├── app.py              # Main application
├── requirements.txt    # Dependencies
├── README.md          # Documentation
└── .gitignore         # Git ignore rules
```

## Development

The application automatically creates the SQLite database on first run. The database file (`urls.db`) is ignored by git to avoid committing test data. 