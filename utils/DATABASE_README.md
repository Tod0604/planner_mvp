# Study Planner Database Persistence Layer

A production-ready SQLite persistence layer for the Study Planner application, providing robust database management, CRUD operations, analytics, and comprehensive error handling.

## Features

✅ **Complete CRUD Operations** - Create, read, update, delete for all entities  
✅ **Thread-Safe Operations** - Lock-based concurrency control  
✅ **Connection Pooling** - Efficient database connection management  
✅ **Query Optimization** - Strategic indexing on frequently queried fields  
✅ **Schema Versioning** - Migration support for future schema changes  
✅ **Analytics Support** - Built-in productivity statistics calculation  
✅ **Error Handling** - Comprehensive logging and error management  
✅ **Type Hints** - Full type annotations for IDE support  
✅ **Comprehensive Tests** - 30+ unit tests covering all functionality  

## File Structure

```
utils/
├── __init__.py              # Package exports
├── database.py              # Main DatabaseManager class (450+ lines)
├── models.py                # TypedDict data models
├── init_db.py               # Database initialization utilities
├── test_database.py         # Comprehensive test suite
├── examples.py              # Usage examples and quick start
└── DATABASE_README.md       # This file
```

## Database Schema

### Tables

#### 1. **deadlines** - Task deadlines and assignments
```sql
CREATE TABLE deadlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'assignment', 'exam', 'project', 'other'
    due_date TEXT NOT NULL,
    estimated_time INTEGER NOT NULL,  -- in minutes
    description TEXT,
    status TEXT DEFAULT 'not_started',  -- 'not_started', 'in_progress', 'completed', 'overdue'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. **study_sessions** - Daily study activity records
```sql
CREATE TABLE study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    tasks TEXT NOT NULL,  -- comma-separated or JSON
    energy_level INTEGER NOT NULL,  -- 1-10
    completion_rate REAL NOT NULL,  -- 0.0-1.0
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. **task_history** - Detailed task completion logs
```sql
CREATE TABLE task_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,
    deadline_id INTEGER,  -- Foreign key to deadlines
    time_spent INTEGER NOT NULL,  -- in minutes
    difficulty_actual INTEGER NOT NULL,  -- 1-10
    completed_date TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deadline_id) REFERENCES deadlines(id) ON DELETE SET NULL
);
```

#### 4. **schema_version** - Migration tracking
```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    migration_date TEXT DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL
);
```

### Indexes

Strategic indexes are created on frequently queried fields:

- `idx_deadlines_due_date` - Deadline ordering queries
- `idx_deadlines_status` - Status filtering
- `idx_deadlines_type` - Type filtering
- `idx_deadlines_created_at` - Date range queries
- `idx_sessions_date` - Session lookup by date
- `idx_task_history_task_name` - Task name searches
- `idx_task_history_deadline_id` - Deadline-related queries
- `idx_task_history_completed_date` - Date range queries

## DatabaseManager API

### Initialization and Connection

```python
from utils.database import DatabaseManager

# Create manager instance
db = DatabaseManager("study_planner.db")

# Connect to database
db.connect()

# Create tables (idempotent)
db.create_tables()

# Disconnect when done
db.disconnect()
```

### Deadline Operations

#### Add Deadline
```python
from utils.models import DeadlineDict
from datetime import datetime, timedelta

deadline: DeadlineDict = {
    'title': 'Math Midterm',
    'type': 'exam',  # 'assignment', 'exam', 'project', 'other'
    'due_date': (datetime.now() + timedelta(days=14)).isoformat(),
    'estimated_time': 180,  # minutes
    'description': 'Covers chapters 1-6',
    'status': 'not_started'  # optional
}

deadline_id = db.add_deadline(deadline)
```

#### Get Deadline
```python
# Get specific deadline
deadline = db.get_deadline(deadline_id)

# Get all deadlines (with optional filters)
all_deadlines = db.get_all_deadlines()

deadlines_not_started = db.get_all_deadlines(status='not_started')
assignments = db.get_all_deadlines(deadline_type='assignment')
limited = db.get_all_deadlines(limit=10)
```

#### Update Deadline
```python
updates = {
    'status': 'in_progress',
    'estimated_time': 200,
    'description': 'Updated description'
}

success = db.update_deadline(deadline_id, updates)
```

#### Delete Deadline
```python
success = db.delete_deadline(deadline_id)
# Associated task_history records will have deadline_id set to NULL
```

### Study Session Operations

#### Add Study Session
```python
from utils.models import StudySessionDict

session: StudySessionDict = {
    'date': datetime.now().isoformat(),
    'tasks': 'Math, Physics, Chemistry',
    'energy_level': 8,  # 1-10 scale
    'completion_rate': 0.92  # 0.0-1.0
}

session_id = db.add_study_session(session)
```

#### Get Study Sessions
```python
# Get all sessions
all_sessions = db.get_study_sessions()

# Get sessions within date range
sessions = db.get_study_sessions(
    start_date='2024-01-01T00:00:00',
    end_date='2024-01-31T23:59:59'
)

# Limit results
recent = db.get_study_sessions(limit=10)
```

#### Get Specific Session
```python
session = db.get_study_session(session_id)
```

### Task History Operations

#### Add Task History
```python
from utils.models import TaskHistoryDict

task: TaskHistoryDict = {
    'task_name': 'Algebra Problem Set',
    'deadline_id': deadline_id,  # optional
    'time_spent': 90,  # minutes
    'difficulty_actual': 7,  # 1-10
    'completed_date': datetime.now().isoformat()
}

history_id = db.add_task_history(task)
```

#### Get Task History
```python
# Get all history
all_history = db.get_task_history()

# Get by task name
math_tasks = db.get_task_history(task_name='Algebra Problem Set')

# Get by date range
weekly_tasks = db.get_task_history(
    start_date='2024-01-01T00:00:00',
    end_date='2024-01-07T23:59:59'
)

# Get by deadline
deadline_tasks = db.get_task_history_by_deadline(deadline_id)
```

### Analytics Operations

#### Productivity Statistics
```python
stats = db.get_productivity_stats(
    start_date='2024-01-01T00:00:00',
    end_date='2024-01-31T23:59:59'
)

# Returns:
# {
#     'study_sessions': {
#         'total_sessions': 15,
#         'avg_energy': 7.2,
#         'avg_completion': 0.88
#     },
#     'task_history': {
#         'total_tasks': 42,
#         'total_time': 5400,  # minutes
#         'avg_difficulty': 6.1
#     },
#     'deadlines': {
#         'total_deadlines': 8,
#         'completed_deadlines': 6
#     }
# }
```

### Database Maintenance

#### Get Database Info
```python
info = db.get_database_info()
# Returns: {
#     'deadlines_count': 10,
#     'sessions_count': 25,
#     'task_history_count': 150,
#     'schema_version': 1,
#     'db_file_size_bytes': 32768
# }
```

#### Clear All Data
```python
success = db.clear_all_data()  # For testing only
```

## Initialization

### Using init_db.py

```bash
# Initialize schema only
python utils/init_db.py init

# Initialize and seed with sample data
python utils/init_db.py seed

# Clear all data
python utils/init_db.py reset

# Use custom database path
python utils/init_db.py init /path/to/custom.db
```

### Programmatic Initialization

```python
from utils.init_db import init_database, seed_sample_data

init_database("study_planner.db")
seed_sample_data("study_planner.db")
```

## Running Tests

```bash
# Run all tests
python -m pytest utils/test_database.py -v

# Or using unittest
python utils/test_database.py

# Run specific test class
python -m pytest utils/test_database.py::TestDatabaseManager -v

# Run with coverage
python -m pytest utils/test_database.py --cov=utils.database
```

## Quick Start Examples

### Example 1: Basic Setup
```python
from utils.database import DatabaseManager
from utils.models import DeadlineDict
from datetime import datetime, timedelta

db = DatabaseManager("study_planner.db")
db.connect()
db.create_tables()

# Add a deadline
deadline: DeadlineDict = {
    'title': 'Python Project',
    'type': 'project',
    'due_date': (datetime.now() + timedelta(days=10)).isoformat(),
    'estimated_time': 240
}
deadline_id = db.add_deadline(deadline)

# Retrieve and update
deadline = db.get_deadline(deadline_id)
db.update_deadline(deadline_id, {'status': 'in_progress'})

db.disconnect()
```

### Example 2: Track Study Sessions and Tasks
```python
from utils.database import DatabaseManager
from utils.models import StudySessionDict, TaskHistoryDict
from datetime import datetime

db = DatabaseManager("study_planner.db")
db.connect()

# Record study session
session: StudySessionDict = {
    'date': datetime.now().isoformat(),
    'tasks': 'Python, Database Design',
    'energy_level': 8,
    'completion_rate': 0.95
}
db.add_study_session(session)

# Log completed task
task: TaskHistoryDict = {
    'task_name': 'Implement database class',
    'time_spent': 120,
    'difficulty_actual': 7,
    'completed_date': datetime.now().isoformat()
}
db.add_task_history(task)

db.disconnect()
```

### Example 3: Analytics
```python
from utils.database import DatabaseManager
from datetime import datetime, timedelta

db = DatabaseManager("study_planner.db")
db.connect()

# Get weekly stats
now = datetime.now()
week_ago = (now - timedelta(days=7)).isoformat()

stats = db.get_productivity_stats(week_ago, now.isoformat())

print(f"Sessions: {stats['study_sessions']['total_sessions']}")
print(f"Tasks completed: {stats['task_history']['total_tasks']}")
print(f"Total time: {stats['task_history']['total_time']} minutes")

db.disconnect()
```

## Error Handling

The DatabaseManager includes comprehensive error handling:

```python
from utils.database import DatabaseManager

db = DatabaseManager("study_planner.db")

# Connect returns False on failure
if not db.connect():
    print("Connection failed")
    
# Operations return None or False on failure
deadline_id = db.add_deadline(deadline)
if deadline_id is None:
    print("Failed to add deadline")

# Missing required fields raise ValueError
try:
    db.add_deadline({'title': 'Incomplete'})
except ValueError as e:
    print(f"Validation error: {e}")
```

All errors are logged using Python's logging module at appropriate levels (DEBUG, INFO, WARNING, ERROR).

## Thread Safety

The DatabaseManager uses a `threading.Lock` to ensure thread-safe operations. Multiple threads can safely:

- Add/update/delete records simultaneously
- Query different tables concurrently
- Access the same database file

Lock contention is minimized by only holding locks during actual database operations.

## Data Types and Validation

### Deadline Types
Valid values: `'assignment'`, `'exam'`, `'project'`, `'other'`

### Deadline Status
Valid values: `'not_started'`, `'in_progress'`, `'completed'`, `'overdue'`

### Energy Level
Range: 1-10 (integer)

### Completion Rate
Range: 0.0-1.0 (float, represents percentage)

### Difficulty Rating
Range: 1-10 (integer)

### Date Format
ISO 8601 format: `'YYYY-MM-DDTHH:MM:SS'`
Example: `'2024-01-15T14:30:00'`

## Best Practices

### 1. Always Use Context Managers
```python
db = DatabaseManager("study_planner.db")
try:
    db.connect()
    # Your operations
finally:
    db.disconnect()
```

### 2. Validate Input Before Adding
```python
from datetime import datetime, timedelta

if estimated_time > 0:
    deadline = {
        'title': title,
        'type': deadline_type,
        'due_date': due_date,
        'estimated_time': estimated_time
    }
    db.add_deadline(deadline)
```

### 3. Check Return Values
```python
deadline_id = db.add_deadline(deadline)
if deadline_id:
    print(f"Created deadline: {deadline_id}")
else:
    print("Failed to create deadline")
```

### 4. Use Specific Queries
```python
# Good - specific filter
not_started = db.get_all_deadlines(status='not_started')

# Avoid - get all and filter in code
all_deadlines = db.get_all_deadlines()
filtered = [d for d in all_deadlines if d['status'] == 'not_started']
```

### 5. Handle Foreign Keys Properly
```python
# When deleting a deadline, associated task_history is updated
success = db.delete_deadline(deadline_id)
# task_history records with this deadline_id will have deadline_id set to NULL
```

## Performance Characteristics

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Add deadline | O(1) | Constant time insert |
| Get deadline by ID | O(log n) | Indexed on primary key |
| Get all deadlines | O(n) | Filtered by indexes when possible |
| Update deadline | O(log n) | Indexed lookup + update |
| Delete deadline | O(m) | m = related task_history records |
| Get task history | O(n) | Where n = task_history size |

## Logging

All database operations are logged with appropriate levels:

- **DEBUG**: Detailed query information and results
- **INFO**: Connection events, successful operations
- **WARNING**: Non-critical issues, missing data
- **ERROR**: Failed operations, connection issues

Access logs via Python's logging module:

```python
import logging

logger = logging.getLogger('utils.database')
logger.setLevel(logging.DEBUG)
```

## Future Enhancements

Planned improvements for future versions:

- [ ] Advanced query builder for complex filtering
- [ ] Batch operations for bulk inserts
- [ ] Automatic backups and archiving
- [ ] Query result caching
- [ ] Database migration framework
- [ ] Export/import functionality (CSV, JSON)
- [ ] Async/await support
- [ ] Connection pooling for multi-process scenarios

## Troubleshooting

### Issue: "Database connection not established"
**Solution**: Call `db.connect()` before other operations

### Issue: "UNIQUE constraint failed"
**Solution**: Ensure you're not inserting duplicate values where constraints exist

### Issue: Slow queries on large datasets
**Solution**: Use specific filters (`status`, `type`, date ranges) instead of `limit`

### Issue: "database is locked"
**Solution**: Ensure only one writer at a time; use connection timeouts for reads

## Contributing

When adding new features:

1. Add corresponding methods to `DatabaseManager`
2. Update `models.py` with new TypedDict if needed
3. Add tests to `test_database.py`
4. Update examples in `examples.py`
5. Document in this README

## License

Part of the Study Planner MVP project.
