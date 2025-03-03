# S.W.A.P. (Shift-Workers Arrangement Platform) - Technical README

## Project Structure

This project is structured to be modular, scalable, and maintainable. Here's a breakdown of the directory structure:

```
swap_project/
├── app/                 # Core application code
│   ├── __init__.py      # Makes 'app' a package
│   ├── main.py          # Main application entry point (FastAPI app)
│   ├── api/             # API endpoints
│   │   ├── __init__.py
│   │   ├── v1/          # Versioning your API is a good practice
│   │   │   ├── __init__.py
│   │   │   ├── calendar.py   # Google Calendar integration
│   │   │   ├── rota.py       # Rota management endpoints
│   │   │   └── users.py      # User management endpoints
│   ├── core/            # Core business logic
│   │   ├── __init__.py
│   │   ├── calendar_sync.py   # Logic for syncing with Google Calendar
│   │   ├── rota_logic.py      # Logic for rota creation, swapping, etc.
│   │   └── user_manager.py   # User management and authentication
│   ├── models/          # Data models (SQLModel)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── shift.py
│   │   └── notification.py
│   ├── schemas/         # Pydantic schemas for request/response validation
│   │   ├── __init__.py
│   │   ├── calendar.py
│   │   ├── rota.py
│   │   └── user.py
│   ├── services/        # External service integrations (e.g., Telegram)
│   │   ├── __init__.py
│   │   └── telegram_service.py
│   ├── utils/           # Utility functions
│   │   ├── __init__.py
│   │   ├── database.py   # Database connection and setup
│   │   └── helpers.py    # Miscellaneous helper functions
│   ├── scheduler/       # Scheduled tasks
│   │   ├── __init__.py
│   │   └── tasks.py     # Tasks like periodic calendar sync
│   ├── streamlit/       # Streamlit application
│   │   ├── __init__.py
│   │   └── main.py      # Streamlit app entry point
│   └── config.py        # Configuration settings
├── cli/                 # Command-line interface
│   ├── __init__.py
│   └── main.py          # CLI entry point and commands
├── tests/               # Unit and integration tests
│   ├── __init__.py
│   ├── conftest.py      # Pytest configuration and fixtures
│   ├── test_api.py
│   ├── test_core.py
│   ├── test_models.py
│   └── test_utils.py
├── migrations/          # Alembic database migrations
│   ├── env.py
│   └── versions/
│       └── ...          # Migration scripts
├── .gitignore           # Specifies intentionally untracked files to ignore
├── requirements.txt     # Project dependencies
├── requirements-dev.txt # Development dependencies (testing, linting)
└── README.md            # Your project's README file
```

## Technology Stack

This project utilizes the following technologies:

*   **Backend:**
    *   **Python 3.10+:** The primary programming language.
    *   **FastAPI:** A high-performance web framework for building APIs.
    *   **SQLModel:** For defining database models and interacting with the database.
    *   **PostgreSQL 15+:** The relational database management system.
    *   **Pydantic:** For data validation and settings management.
    *   **Alembic:** For database migrations.
    *   **APScheduler:** For scheduling tasks within the FastAPI application.
*   **Frontend (Future):**
    *   **React:** A JavaScript library for building user interfaces.
    *   **Material UI:** A popular React component library.
    *   **Redux/Zustand:** For state management.
    *   **HTML, CSS, JavaScript:** The fundamental web technologies.
*   **Notifications:**
    *   **Telegram API:** For sending real-time notifications.
    *   **`python-telegram-bot`:** Library that interfaces with the Telegram API.
*   **Calendar Integration:**
    *   **Google Calendar API:** For synchronizing with Google Calendar.
    *   **`google-api-python-client`:** The official Google API client library for Python.
    *   **`google-auth-oauthlib`:** For handling OAuth 2.0 flows.
*   **Deployment (Future):**
    *   **Docker:** For containerization.
    *   **Kubernetes:** For container orchestration and scaling.
    *   **Cloud Platform:** AWS, Google Cloud, or Azure (to be decided).

## Development Setup

1. **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd swap_project
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Linux/macOS
    .venv\Scripts\activate    # On Windows
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```

4. **Database Setup:**

    *   Install **PostgreSQL 15+** on your system or use a Docker container.
    *   Create a database for the project.
    *   Configure the database connection in `app/config.py`.

5. **Run database migrations:**

    ```bash
    alembic upgrade head
    ```

6. **Run the FastAPI application:**

    ```bash
    uvicorn app.main:app --reload
    ```

    The `--reload` flag will automatically restart the server when you make changes to the code. The scheduler will start automatically with the application.

7. **Run the tests:**

    ```bash
    pytest
    ```

## API Endpoints (Examples)

*   **`/api/v1/calendar/sync` (POST):** Initiates a manual synchronization with Google Calendar. (You might want to remove or restrict this in production since the scheduler handles it automatically).
*   **`/api/v1/rota` (GET):** Retrieves the current rota.
*   **`/api/v1/rota/swap` (POST):** Creates a new rota swap request.
*   **`/api/v1/users` (POST):** Creates a new user.
*   **`/api/v1/users/me` (GET):** Retrieves the current user's information.

(These are just examples, and the actual endpoints will be defined as you develop the API.)

## Scheduler

The project uses **APScheduler** to run scheduled tasks within the FastAPI application. The primary scheduled task is the periodic synchronization with Google Calendar.

*   **Scheduler Library:** APScheduler
*   **Schedule:** The synchronization task is scheduled to run at a configurable interval (default: every 30 minutes). The interval can be adjusted in `app/config.py` using the `CALENDAR_SYNC_INTERVAL_MINUTES` setting.
*   **Task Implementation:** The synchronization logic is implemented in `app/core/calendar_sync.py`.
*   **Error Handling:** The `sync_calendar` function includes error handling and logging to ensure that any issues during synchronization are captured and reported.
*   **Integration:** The scheduler is initialized and started within the `app/main.py` file, making it an integral part of the FastAPI application.

**Note:** The scheduler runs in a separate thread within the FastAPI process. Be mindful of long-running or blocking operations within scheduled tasks to avoid impacting the main application thread.

## CLI

The `cli/` directory contains the command-line interface for the project. You can add commands for various administrative tasks or other operations that are best performed from the command line.

## Streamlit App

The `streamlit_app/` directory will contain a Streamlit application for data visualization or other interactive features. This is an optional component and can be developed as needed.

## Contributing

We welcome contributions to S.W.A.P.! If you'd like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and write tests.
4. Commit your changes with clear commit messages.
5. Submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.