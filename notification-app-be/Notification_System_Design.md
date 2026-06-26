# Stage 1 - Notification API Design

## Objective

Design a scalable notification system for campus students that supports placement updates, exam results, events, and announcements.

---

## API Endpoints

### 1. Get All Notifications

**Endpoint**

```http
GET /api/v1/notifications
```

**Query Parameters**

| Parameter | Description                |
| --------- | -------------------------- |
| page      | Page number                |
| limit     | Number of records per page |
| type      | Placement, Result, Event   |
| isRead    | true/false                 |

Example:

```http
GET /api/v1/notifications?page=1&limit=20&type=Placement
```

Example Response:

```json
{
  "notifications": [
    {
      "id": "1",
      "title": "Microsoft Hiring Drive",
      "message": "Microsoft has opened registrations for SDE roles.",
      "type": "Placement",
      "priority": 1,
      "isRead": false,
      "createdAt": "2026-06-26T12:00:00Z"
    }
  ],
  "page": 1,
  "totalPages": 5
}
```

---

### 2. Create Notification

```http
POST /api/v1/notifications
```

Request Body:

```json
{
  "title": "Amazon Hiring Drive",
  "message": "Applications are open for 2027 batch.",
  "type": "Placement",
  "priority": 1
}
```

Response:

```json
{
  "message": "Notification created successfully"
}
```

---

### 3. Mark Notification as Read

```http
PATCH /api/v1/notifications/{id}/read
```

Response:

```json
{
  "message": "Notification marked as read"
}
```

---

### 4. Get Unread Notifications

```http
GET /api/v1/notifications/unread
```

---

### 5. Delete Notification

```http
DELETE /api/v1/notifications/{id}
```

---

### 6. Notification Preferences

```http
PUT /api/v1/preferences
```

Request:

```json
{
  "placement": true,
  "results": true,
  "events": false
}
```

---

## Real-Time Notification Mechanism

The system will use **WebSockets** to provide instant notifications to students.

### Workflow

1. Admin creates a notification.
2. Notification is stored in the database.
3. Notification service publishes the event.
4. WebSocket server pushes the notification to connected clients instantly.
5. Offline users receive pending notifications after reconnecting.

### Why WebSockets?

* Low latency communication.
* Eliminates unnecessary polling requests.
* Supports real-time updates efficiently.
* Reduces server load compared to frequent API polling.

# Stage 2 - Database Design

## Selected Database: PostgreSQL

PostgreSQL was chosen because:

* Supports ACID transactions.
* Excellent support for indexing and query optimization.
* Handles large datasets efficiently.
* Supports JSON fields if notification metadata changes in future.
* Highly reliable for production applications.

---

## Notification Table Schema

| Column     | Type         | Description                    |
| ---------- | ------------ | ------------------------------ |
| id         | UUID         | Unique notification identifier |
| student_id | BIGINT       | Student receiving notification |
| title      | VARCHAR(255) | Notification title             |
| message    | TEXT         | Notification content           |
| type       | VARCHAR(50)  | Placement, Result, Event       |
| priority   | INTEGER      | 1 = High, 2 = Medium, 3 = Low  |
| is_read    | BOOLEAN      | Read status                    |
| created_at | TIMESTAMP    | Creation time                  |

---

## SQL Schema

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    student_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    priority INTEGER NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Indexes

```sql
CREATE INDEX idx_student_notifications
ON notifications(student_id);

CREATE INDEX idx_unread_notifications
ON notifications(student_id, is_read);

CREATE INDEX idx_created_at
ON notifications(created_at DESC);
```

---

## Relationships

If user management exists:

```text
students (1) -------- (N) notifications
```

One student can receive multiple notifications, while each notification belongs to one student.

# Stage 3 - Query Optimization

## Problem Query

```sql
SELECT *
FROM notifications
WHERE student_id = 1042
AND is_read = false
ORDER BY created_at DESC;
```

---

## Why Does This Become Slow?

As the number of notifications grows to millions of records, the database performs a full table scan to find unread notifications for a student.

This increases:

* Query execution time
* CPU usage
* Disk I/O operations

---

## Optimization Strategy

Create a composite index:

```sql
CREATE INDEX idx_student_read_created
ON notifications(student_id, is_read, created_at DESC);
```

This allows PostgreSQL to:

1. Filter by `student_id`
2. Filter by `is_read`
3. Return already sorted records using the index

without scanning the entire table.

---

## Should Every Column Be Indexed?

No.

Excessive indexing causes:

* Slower INSERT operations
* Slower UPDATE operations
* Increased storage consumption
* Additional maintenance overhead

Indexes should only be created on frequently filtered, joined, or sorted columns.

---

## Query to Fetch Placement Notifications from Last 7 Days

```sql
SELECT *
FROM notifications
WHERE type = 'Placement'
AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

Recommended index:

```sql
CREATE INDEX idx_type_created
ON notifications(type, created_at DESC);
```

This ensures efficient retrieval of recent placement notifications.


# Stage 4 - Reducing Database Load

## Problem Statement

The application currently fetches notifications from the database every time a student opens the application.

With thousands of students opening the application simultaneously, this causes:

* High database load
* Increased response time
* Reduced scalability

---

## Proposed Solutions

### 1. Redis Caching

Frequently accessed notifications are stored in Redis.

Flow:

```text
Application → Redis Cache → PostgreSQL
```

If notifications exist in cache:

* Return cached data immediately.

Otherwise:

* Fetch from PostgreSQL.
* Store in Redis with expiration time.
* Return response.

---

### 2. Pagination

Instead of loading all notifications:

```http
GET /notifications?page=1&limit=20
```

Benefits:

* Smaller response size
* Reduced memory usage
* Faster queries

---

### 3. WebSockets

Instead of polling every few seconds:

```text
Client ---- WebSocket ---- Server
```

The server pushes new notifications instantly.

Benefits:

* Real-time updates
* Reduced API calls
* Lower database traffic

---

### 4. Background Processing

Heavy operations such as:

* Sending emails
* Push notifications
* SMS delivery

should be processed asynchronously using background workers.

---

### 5. CDN for Static Assets

Images and attachments associated with notifications should be stored in:

* AWS S3
* CloudFront
* CDN

This reduces load on the application server.

---

## Final Architecture

```text
Client
   ↓
Load Balancer
   ↓
Application Server
   ↓
Redis Cache
   ↓
PostgreSQL Database
```

This architecture provides high availability and scalability for large campus deployments.


# Stage 5 - Handling 50,000 Simultaneous Notifications

## Existing Implementation

```python
for student in students:
    send_email(student)
    save_to_db(student)
    push_to_app(student)
```

Problems:

* Sequential execution
* Slow response time
* Application server becomes blocked
* Cannot scale for thousands of users

---

## Proposed Architecture

```text
Admin
  ↓
Notification Service
  ↓
Message Queue (Kafka/RabbitMQ)
  ↓
------------------------------------
| Email Worker                     |
| Push Notification Worker         |
| Database Worker                  |
------------------------------------
  ↓
Students
```

---

## Why Message Queues?

Message queues allow asynchronous processing.

Benefits:

* High throughput
* Fault tolerance
* Retry mechanism
* Horizontal scaling

---

## Processing Flow

### Step 1

Admin creates notification.

### Step 2

Notification service publishes message to Kafka topic.

Example:

```json
{
  "type": "Placement",
  "title": "Google Hiring Drive",
  "priority": 1
}
```

### Step 3

Workers consume messages independently:

* Email Worker → sends emails
* Push Worker → sends mobile notifications
* Database Worker → stores notification records

---

## Retry Mechanism

If a worker fails:

```text
Attempt 1 → Fail
Attempt 2 → Fail
Attempt 3 → Fail
```

The message is moved to:

```text
Dead Letter Queue (DLQ)
```

for later investigation.

---

## Horizontal Scaling

During placement season:

```text
Email Workers:
2 → 20 instances

Push Workers:
2 → 30 instances
```

This enables the system to support tens of thousands of students simultaneously.

---

## Final Result

The system becomes:

* Highly scalable
* Fault tolerant
* Asynchronous
* Production ready

```
```



# Stage 6 - Priority Inbox Implementation

## Priority Rules

| Notification Type | Priority |
| ----------------- | -------- |
| Placement         | 1        |
| Results           | 2        |
| Events            | 3        |

Lower priority number means higher importance.

---

## Python Implementation

```python
PRIORITY_MAP = {
    "Placement": 1,
    "Result": 2,
    "Event": 3
}


def get_top_notifications(notifications):
    """
    Returns top 10 notifications based on:
    1. Priority
    2. Recency
    """

    sorted_notifications = sorted(
        notifications,
        key=lambda x: (
            PRIORITY_MAP.get(x["type"], 999),
            -x["created_at_timestamp"]
        )
    )

    return sorted_notifications[:10]
```

---

## Example Input

```python
notifications = [
    {
        "title": "Google Hiring Drive",
        "type": "Placement",
        "created_at_timestamp": 1719387000
    },
    {
        "title": "Mid Sem Result Published",
        "type": "Result",
        "created_at_timestamp": 1719387100
    },
    {
        "title": "Hackathon Registration Open",
        "type": "Event",
        "created_at_timestamp": 1719387200
    }
]
```

---

## Example Output

```python
[
    {
        "title": "Google Hiring Drive",
        "type": "Placement"
    },
    {
        "title": "Mid Sem Result Published",
        "type": "Result"
    },
    {
        "title": "Hackathon Registration Open",
        "type": "Event"
    }
]
```

---

## Time Complexity

Sorting complexity:

```text
O(n log n)
```

Space complexity:

```text
O(n)
```

This approach is efficient for campus-scale notification systems.
