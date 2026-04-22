# Internal Recruitment System

## Tech Stack
- Python 3.10.x
- Postgres
- Redis
- Celery


**These are the minimum required version in order to run this project**


## Initial Setup
Clone the code, Install the required technologies with required version and do following in sequence

### Python Setup
- Install pip using [guide](https://pip.pypa.io/en/stable/installation/)
- Install virtual enviornment using this [guide](https://virtualenv.pypa.io/en/latest/index.html)
- Create and Activate virtual envoirnment
- Run `pip install -r requirements.txt`

### Redis Setup
- Install Redis using [Redis installation guide](https://redis.io/docs/getting-started/installation/)
- Start Redis server:
  ```bash
  redis-server
  ```
- Verify Redis is running:
  ```bash
  redis-cli ping
  ```
  (Should return "PONG")

### Celery Setup
- Start Celery worker in a separate terminal:
  ```bash
  celery -A edjobster worker --loglevel=info
  ```
- Start Celery beat scheduler (if using periodic tasks) in another terminal:
  ```bash
  celery -A edjobster beat --loglevel=info
  ```

### Running the Application
The application should be accessible at (http://localhost:8000) when you run:
```bash
python manage.py runserver
```

**Note:** Make sure Redis is running before starting Celery workers, as Celery uses Redis as its message broker.
