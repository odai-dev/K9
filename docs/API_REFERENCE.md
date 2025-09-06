# K9 Operations Management System - API Reference

## Overview

The K9 Operations Management System provides a comprehensive REST API for managing all aspects of K9 operations. This document covers all available endpoints, authentication, and usage examples.

## Base URL

```
Development: http://localhost:5000/api
Production: https://yourdomain.com/api
```

## Authentication

All API endpoints require session-based authentication. Users must first login through the web interface or the login API endpoint.

### Session Authentication

```javascript
// Login first
const response = await fetch('/auth/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
    },
    credentials: 'include',
    body: JSON.stringify({
        username: 'admin',
        password: 'password'
    })
});

// Then use other API endpoints
const dogs = await fetch('/api/dogs', {
    credentials: 'include',  // Include session cookie
    headers: {
        'X-CSRFToken': getCSRFToken()
    }
});
```

### CSRF Protection

All state-changing requests (POST, PUT, DELETE) require a CSRF token in the `X-CSRFToken` header.

```javascript
function getCSRFToken() {
    return document.querySelector('meta[name=csrf-token]').getAttribute('content');
}
```

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
    "success": true,
    "data": {
        // Response data here
    },
    "message": "Operation completed successfully"
}
```

### Error Response
```json
{
    "success": false,
    "error": "error_code",
    "message": "Human readable error message",
    "details": {
        // Additional error details
    }
}
```

## API Endpoints

### Dogs Management

#### List Dogs
```http
GET /api/dogs
```

**Parameters:**
- `status` (optional): Filter by dog status (ACTIVE, RETIRED, DECEASED, TRAINING)
- `limit` (optional): Number of results to return (default: 50)
- `offset` (optional): Number of results to skip (default: 0)

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": "uuid-here",
            "name": "Rex",
            "microchip_id": "123456789",
            "breed": "German Shepherd",
            "status": "ACTIVE",
            "gender": "MALE",
            "birth_date": "2020-01-15",
            "created_at": "2023-01-01T00:00:00Z"
        }
    ],
    "total": 100,
    "limit": 50,
    "offset": 0
}
```

#### Get Dog Details
```http
GET /api/dogs/{id}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": "uuid-here",
        "name": "Rex",
        "microchip_id": "123456789",
        "breed": "German Shepherd",
        "status": "ACTIVE",
        "gender": "MALE",
        "birth_date": "2020-01-15",
        "color": "Brown and Black",
        "weight": 30.5,
        "height": 65.0,
        "photo_url": "/uploads/dogs/rex.jpg",
        "assignments": [
            {
                "project_id": "project-uuid",
                "project_name": "Border Patrol",
                "assignment_date": "2023-01-01",
                "role": "Detection"
            }
        ],
        "training_sessions": [
            {
                "id": "session-uuid",
                "category": "Detection",
                "date": "2023-06-01",
                "performance_rating": "EXCELLENT"
            }
        ]
    }
}
```

#### Create Dog
```http
POST /api/dogs
```

**Required Permission:** `dogs.create`

**Request Body:**
```json
{
    "name": "Max",
    "microchip_id": "987654321",
    "breed": "Belgian Malinois",
    "gender": "MALE",
    "birth_date": "2021-03-10",
    "color": "Fawn",
    "weight": 28.0,
    "height": 60.0
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": "new-uuid-here",
        "name": "Max",
        "microchip_id": "987654321",
        "status": "TRAINING"
    },
    "message": "Dog created successfully"
}
```

#### Update Dog
```http
PUT /api/dogs/{id}
```

**Required Permission:** `dogs.edit`

**Request Body:** Same as Create Dog (all fields optional)

#### Delete Dog
```http
DELETE /api/dogs/{id}
```

**Required Permission:** `dogs.delete`

### Employees Management

#### List Employees
```http
GET /api/employees
```

**Parameters:**
- `role` (optional): Filter by employee role
- `active` (optional): Filter by active status (true/false)

#### Get Employee Details
```http
GET /api/employees/{id}
```

#### Create Employee
```http
POST /api/employees
```

**Request Body:**
```json
{
    "name": "أحمد محمد",
    "role": "HANDLER",
    "phone": "+966501234567",
    "email": "ahmed@example.com",
    "hire_date": "2023-01-15",
    "national_id": "1234567890"
}
```

### Projects Management

#### List Projects
```http
GET /api/projects
```

**Parameters:**
- `status` (optional): Filter by project status
- `manager_id` (optional): Filter by project manager

#### Get Project Details
```http
GET /api/projects/{id}
```

**Response includes:**
- Project information
- Assigned dogs
- Team members
- Recent incidents
- Performance metrics

#### Create Project
```http
POST /api/projects
```

**Request Body:**
```json
{
    "name": "Airport Security Operation",
    "description": "Enhanced security screening at international airport",
    "start_date": "2023-07-01",
    "location": "King Fahd International Airport",
    "manager_id": "manager-uuid"
}
```

#### Project Assignments

##### Assign Dog to Project
```http
POST /api/projects/{project_id}/assignments
```

**Request Body:**
```json
{
    "dog_id": "dog-uuid",
    "role": "Detection",
    "assignment_date": "2023-07-01"
}
```

##### Remove Dog from Project
```http
DELETE /api/projects/{project_id}/assignments/{assignment_id}
```

### Training Management

#### Record Training Session
```http
POST /api/training
```

**Request Body:**
```json
{
    "dog_id": "dog-uuid",
    "trainer_id": "trainer-uuid",
    "category": "DETECTION",
    "date": "2023-06-15",
    "duration_minutes": 60,
    "performance_rating": "GOOD",
    "notes": "Good progress on explosive detection",
    "location": "Training Ground A"
}
```

#### Get Training Statistics
```http
GET /api/training/statistics
```

**Parameters:**
- `dog_id` (optional): Statistics for specific dog
- `trainer_id` (optional): Statistics for specific trainer
- `start_date` (optional): Start date for statistics
- `end_date` (optional): End date for statistics

**Response:**
```json
{
    "success": true,
    "data": {
        "total_sessions": 150,
        "categories": {
            "DETECTION": 50,
            "OBEDIENCE": 40,
            "AGILITY": 35,
            "ATTACK": 25
        },
        "performance_ratings": {
            "EXCELLENT": 45,
            "GOOD": 80,
            "WEAK": 25
        },
        "average_duration": 75.5
    }
}
```

### Veterinary Management

#### Record Veterinary Visit
```http
POST /api/veterinary
```

**Request Body:**
```json
{
    "dog_id": "dog-uuid",
    "vet_id": "vet-uuid",
    "visit_type": "ROUTINE",
    "date": "2023-06-20",
    "diagnosis": "Annual checkup - healthy",
    "treatment": "Vaccinations updated",
    "cost": 250.00,
    "next_visit_date": "2024-06-20"
}
```

#### Get Health Records
```http
GET /api/dogs/{id}/health
```

### Attendance Management

#### Record Attendance
```http
POST /api/attendance
```

**Request Body:**
```json
{
    "entity_type": "EMPLOYEE",
    "entity_id": "employee-uuid",
    "project_id": "project-uuid",
    "shift_id": "shift-uuid",
    "date": "2023-06-21",
    "status": "PRESENT",
    "notes": "On time arrival"
}
```

#### Get Attendance Report
```http
GET /api/attendance/report
```

**Parameters:**
- `project_id`: Project ID (required)
- `start_date`: Start date (required)
- `end_date`: End date (required)
- `entity_type`: EMPLOYEE or DOG (optional)

### Incidents and Suspicions

#### Report Incident
```http
POST /api/incidents
```

**Request Body:**
```json
{
    "project_id": "project-uuid",
    "date": "2023-06-21T14:30:00Z",
    "description": "Suspicious package detected at checkpoint 3",
    "severity": "HIGH",
    "location": "Terminal 1, Gate 15"
}
```

#### Report Suspicion
```http
POST /api/suspicions
```

**Request Body:**
```json
{
    "project_id": "project-uuid",
    "date": "2023-06-21T10:15:00Z",
    "element_type": "EXPLOSIVE",
    "description": "Dog alerted to potential explosive device",
    "location": "Baggage screening area"
}
```

### Performance Evaluations

#### Create Performance Evaluation
```http
POST /api/evaluations
```

**Request Body:**
```json
{
    "project_id": "project-uuid",
    "dog_id": "dog-uuid",
    "evaluation_date": "2023-06-21",
    "performance_rating": "EXCELLENT",
    "detection_accuracy": 95.5,
    "response_time": 8.2,
    "notes": "Outstanding performance in explosive detection",
    "evaluator_id": "evaluator-uuid"
}
```

### Breeding Management

#### Record Mating
```http
POST /api/breeding/mating
```

**Request Body:**
```json
{
    "male_dog_id": "male-uuid",
    "female_dog_id": "female-uuid",
    "mating_date": "2023-06-01",
    "cycle_type": "NATURAL",
    "result": "SUCCESSFUL"
}
```

#### Record Pregnancy
```http
POST /api/breeding/pregnancy
```

#### Record Delivery
```http
POST /api/breeding/delivery
```

## Error Codes

| Code | Description |
|------|-------------|
| `validation_error` | Request data validation failed |
| `permission_denied` | User lacks required permission |
| `not_found` | Requested resource not found |
| `duplicate_entry` | Unique constraint violation |
| `database_error` | Database operation failed |
| `unauthorized` | Authentication required |
| `forbidden` | Access denied |
| `rate_limited` | Too many requests |
| `server_error` | Internal server error |

## Rate Limiting

API endpoints are rate limited to prevent abuse:

- **General API**: 60 requests per minute per IP
- **Authentication**: 5 requests per minute per IP
- **File Upload**: 10 requests per minute per user

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1623456789
```

## Pagination

List endpoints support pagination using limit and offset parameters:

```http
GET /api/dogs?limit=20&offset=40
```

Response includes pagination metadata:
```json
{
    "data": [...],
    "pagination": {
        "total": 150,
        "limit": 20,
        "offset": 40,
        "has_next": true,
        "has_prev": true
    }
}
```

## Filtering and Search

Many endpoints support filtering and search:

```http
GET /api/dogs?status=ACTIVE&breed=German%20Shepherd&search=rex
GET /api/employees?role=HANDLER&active=true
GET /api/projects?status=ACTIVE&manager_id=uuid
```

## File Upload

File uploads use multipart/form-data:

```javascript
const formData = new FormData();
formData.append('photo', fileInput.files[0]);
formData.append('dog_id', 'dog-uuid');

fetch('/api/dogs/photo', {
    method: 'POST',
    headers: {
        'X-CSRFToken': getCSRFToken()
    },
    credentials: 'include',
    body: formData
});
```

## WebSocket Events (Future)

Real-time updates for critical events:

```javascript
const ws = new WebSocket('wss://yourdomain.com/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'incident_reported') {
        // Handle new incident
    }
};
```

## SDK Examples

### JavaScript SDK

```javascript
class K9API {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }
    
    async request(endpoint, options = {}) {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
                ...options.headers
            },
            ...options
        });
        
        return response.json();
    }
    
    // Dogs API
    async getDogs(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/dogs?${params}`);
    }
    
    async createDog(dogData) {
        return this.request('/dogs', {
            method: 'POST',
            body: JSON.stringify(dogData)
        });
    }
    
    // Training API
    async recordTraining(sessionData) {
        return this.request('/training', {
            method: 'POST',
            body: JSON.stringify(sessionData)
        });
    }
}

// Usage
const api = new K9API('/api');
const dogs = await api.getDogs({ status: 'ACTIVE' });
```

### Python SDK

```python
import requests
from typing import Optional, Dict, Any

class K9API:
    def __init__(self, base_url: str, session_cookie: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.cookies.set('session', session_cookie)
    
    def request(self, endpoint: str, method: str = 'GET', 
                data: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, json=data)
        response.raise_for_status()
        return response.json()
    
    def get_dogs(self, **filters) -> Dict[str, Any]:
        params = '&'.join(f"{k}={v}" for k, v in filters.items())
        return self.request(f"/dogs?{params}")
    
    def create_dog(self, dog_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.request("/dogs", method='POST', data=dog_data)

# Usage
api = K9API('/api', session_cookie)
dogs = api.get_dogs(status='ACTIVE')
```

## Testing

Test your API integration:

```bash
# Test authentication
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -c cookies.txt

# Test API endpoint
curl -X GET http://localhost:5000/api/dogs \
  -H "X-CSRFToken: your-csrf-token" \
  -b cookies.txt
```

## Support

For API support:
- Check the [Developer Guide](DEVELOPER_GUIDE.md) for detailed implementation examples
- Review the [Database ERD](DATABASE_ERD.md) for data relationships
- Contact the development team for additional assistance

---

**Last Updated:** September 2025  
**API Version:** 1.0  
**Documentation Version:** 1.0