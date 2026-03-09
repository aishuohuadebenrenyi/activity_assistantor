# Backend for Activity Assistant

## Prerequisites
- Python 3.9+
- MySQL (Optional, defaults to SQLite for dev)

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Mac/Linux
   # venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configuration:
   - Copy `config.py` if needed or set environment variables.
   - Default uses SQLite `app.db`.

## Running

Run from the project root:
```bash
python run.py
```

The API will be available at `http://localhost:9000`.

## API Endpoints

- **Auth**:
  - `POST /api/auth/login`
  - `POST /api/auth/send-code`

- **Activities**:
  - `GET /api/activities`
  - `POST /api/activities`
  - `GET /api/activities/<id>`
  - `PUT /api/activities/<id>`
  - `DELETE /api/activities/<id>`

- **Participants**:
  - `GET /api/<id>/participants`
  - `POST /api/<id>/register`
  - `POST /api/<id>/checkin`
  - `DELETE /api/<id>/checkin/<record_id>`

- **User**:
  - `GET /api/user/profile`
  - `PUT /api/user/profile`
