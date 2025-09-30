# InfinityAI.Pro Broker Connection System

This document describes the new broker connection management system integrated into InfinityAI.Pro.

## Overview

The broker connection system provides:
- **Secure token storage** with Fernet encryption
- **JWT-based authentication** for user management  
- **Background validation** via Celery tasks
- **Automatic expiry checking** and notifications
- **Multi-broker support** (Dhan, Zerodha, Upstox, etc.)
- **Real-time status updates**

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   PostgreSQL    │
│   (React/Next)  │◄──►│   Backend       │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Celery        │◄──►│   Redis         │
                       │   Worker        │    │   (Message      │
                       └─────────────────┘    │   Broker)       │
                                              └─────────────────┘
```

## Getting Started

### 1. Local Development Setup

#### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+

#### Start the Development Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd InfinityAI.Pro

# Copy environment variables
cp .env.development .env

# Generate a new Fernet key (optional, for production)
python -c "from cryptography.fernet import Fernet; print(f'FERNET_KEY={Fernet.generate_key().decode()}')"

# Start all services
docker-compose up --build

# Wait for all services to start, then access:
# - Backend API: http://localhost:8000
# - Frontend: http://localhost:3000  
# - API Docs: http://localhost:8000/docs
# - Celery Flower: http://localhost:5555
# - pgAdmin: http://localhost:5050
```

#### Services Started:
- **PostgreSQL** (port 5432): User authentication and broker data
- **Redis** (port 6379): Celery message broker and caching
- **FastAPI Backend** (port 8000): Main API server
- **Celery Worker**: Background task processing
- **Celery Beat**: Periodic task scheduler
- **Celery Flower** (port 5555): Task monitoring UI
- **Frontend** (port 3000): React/Next.js UI
- **pgAdmin** (port 5050): Database management

### 2. Database Setup

The system automatically creates the necessary tables on startup:

```sql
-- Users table for authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    -- ... other fields
);

-- Broker connections with encrypted tokens  
CREATE TABLE broker_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    broker_name TEXT NOT NULL,
    encrypted_token BYTEA NOT NULL,
    status TEXT DEFAULT 'pending',
    expiry_timestamp TIMESTAMP WITH TIME ZONE,
    -- ... other fields
);
```

## API Usage

### Authentication Endpoints

#### Register New User
```http
POST /auth/signup
Content-Type: application/json

{
    "username": "john_doe",
    "email": "john@example.com", 
    "password": "SecurePass123",
    "first_name": "John",
    "last_name": "Doe"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
    "username": "john_doe",
    "password": "SecurePass123"
}

Response:
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "john_doe"
}
```

#### Get User Profile
```http
GET /auth/me
Authorization: Bearer <access_token>

Response:
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": true,
    "created_at": "2025-09-30T01:00:00Z"
}
```

### Broker Management Endpoints

#### Add Broker Connection
```http
POST /brokers
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "broker_name": "dhan",
    "token": "your_broker_api_token_here",
    "expiry_timestamp": "2025-12-31T23:59:59Z",
    "metadata": {
        "account_type": "equity",
        "notes": "Primary trading account"
    }
}

Response:
{
    "id": "456e7890-e89b-12d3-a456-426614174001", 
    "broker_name": "dhan",
    "status": "pending",
    "created_at": "2025-09-30T01:30:00Z",
    "validation_attempts": 0
}
```

#### List Broker Connections
```http
GET /brokers
Authorization: Bearer <access_token>

Response:
[
    {
        "id": "456e7890-e89b-12d3-a456-426614174001",
        "broker_name": "dhan", 
        "status": "connected",
        "expiry_timestamp": "2025-12-31T23:59:59Z",
        "last_validated_at": "2025-09-30T01:31:00Z",
        "validation_attempts": 1,
        "metadata": {
            "account_info": {
                "account_id": "D12345",
                "client_name": "John Doe",
                "balance": 50000.0
            }
        }
    }
]
```

#### Update Broker Connection
```http
PUT /brokers/{broker_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "token": "new_broker_token_here",
    "expiry_timestamp": "2026-01-31T23:59:59Z"
}
```

#### Delete Broker Connection
```http
DELETE /brokers/{broker_id}
Authorization: Bearer <access_token>
```

#### Manual Validation
```http
POST /brokers/{broker_id}/validate
Authorization: Bearer <access_token>

Response:
{
    "broker_id": "456e7890-e89b-12d3-a456-426614174001",
    "status": "pending", 
    "message": "Validation scheduled",
    "validated_at": "2025-09-30T01:45:00Z"
}
```

## Broker Status Lifecycle

```
┌─────────────┐    Validation    ┌─────────────┐
│   pending   │──────────────────►│  connected  │
└─────────────┘                  └─────────────┘
       │                                │
       │ Validation Failed              │ Token Expired
       ▼                                ▼
┌─────────────┐                  ┌─────────────┐
│   invalid   │                  │   expired   │  
└─────────────┘                  └─────────────┘
       │                                │
       │ Update Token                   │ Update Token
       └────────────────┬───────────────┘
                        ▼
                 ┌─────────────┐
                 │   pending   │ (Re-validation)
                 └─────────────┘
```

## Background Tasks

The system runs several Celery background tasks:

### Broker Validation Task
- **Trigger**: When broker connection is added/updated
- **Purpose**: Validates token with broker API
- **Retry**: 3 attempts with exponential backoff
- **Queue**: `broker_validation`

### Expired Token Check
- **Schedule**: Every 5 minutes
- **Purpose**: Mark expired tokens and notify users
- **Queue**: `maintenance`

### Session Cleanup
- **Schedule**: Daily at 2 AM UTC
- **Purpose**: Remove old user sessions
- **Queue**: `maintenance`

### Health Check
- **Schedule**: Every 10 minutes  
- **Purpose**: Monitor system health
- **Queue**: `maintenance`

## Monitoring

### Celery Flower Dashboard
Access http://localhost:5555 to monitor:
- Active tasks
- Task history
- Worker status
- Queue statistics
- Task failures and retries

### Health Check Endpoint
```http
GET /health

Response:
{
    "status": "healthy",
    "timestamp": "2025-09-30T01:00:00Z", 
    "version": "2.0.0",
    "services": {
        "postgresql": {"status": "healthy"},
        "cryptography": {"status": "healthy"},
        "redis": {"status": "healthy"},
        "cassandra": {"status": "error"},
        "market_data": {"status": "healthy"}
    }
}
```

## Security Features

### Token Encryption
- All broker tokens encrypted with **Fernet** (AES 128)
- Encryption keys stored securely (Azure Key Vault in production)
- No plaintext tokens stored in database

### JWT Authentication
- Access tokens with configurable expiry (default: 1 hour)
- Refresh tokens for extended sessions (default: 30 days)
- Session tracking with IP and user agent
- Automatic token invalidation on logout

### Password Security
- **bcrypt** hashing with salt
- Strong password requirements
- Account lockout protection

### Database Security
- UUID primary keys (no sequential IDs)
- Proper foreign key constraints
- Audit logging for sensitive operations
- Connection pooling with SSL

## Production Deployment

### Environment Variables
```bash
# Required in production
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379/0
JWT_SECRET=<strong-secret-key>
FERNET_KEY=<generated-fernet-key>

# Optional
AZURE_KEYVAULT_URL=https://vault.vault.azure.net/
AWS_ACCESS_KEY_ID=<access-key>
AWS_SECRET_ACCESS_KEY=<secret-key>
```

### Railway Deployment
The system is configured for Railway deployment with:
- Automatic PostgreSQL addon
- Redis addon  
- Environment variable management
- Health checks
- Horizontal scaling support

### Security Hardening Checklist
- [ ] Use strong JWT secrets (64+ characters)
- [ ] Generate new Fernet keys for each environment  
- [ ] Enable HTTPS/TLS for all connections
- [ ] Use managed database services (not self-hosted)
- [ ] Enable database encryption at rest
- [ ] Configure Redis AUTH and SSL
- [ ] Set up proper CORS policies
- [ ] Enable API rate limiting
- [ ] Use secure session cookies (httpOnly, secure, sameSite)
- [ ] Configure proper firewall rules
- [ ] Enable audit logging
- [ ] Set up monitoring and alerting

## Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check PostgreSQL connection
docker exec -it infinityai_postgres psql -U infinityai -d infinityai -c "SELECT 1;"

# Check application logs
docker logs infinityai_backend
```

#### Celery Tasks Not Running
```bash
# Check Celery worker status
docker logs infinityai_celery_worker

# Check Redis connection
docker exec -it infinityai_redis redis-cli ping
```

#### Broker Validation Failing
```bash
# Check task status in Flower: http://localhost:5555
# Check broker API credentials
# Review validation logs in worker container
```

### Debugging

Enable debug logging:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

Database queries logging:
```python
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## API Reference

Full API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Contributing

1. Follow the existing code structure
2. Add tests for new broker integrations
3. Update this documentation for new features
4. Use type hints and proper error handling
5. Follow security best practices

## Support

For issues related to broker integrations:
1. Check the validation logs in Celery Flower
2. Verify broker API credentials  
3. Test broker APIs manually with tools like Postman
4. Review broker-specific documentation

The system currently supports:
- ✅ **Dhan** - Full integration with dhanhq library
- 🔄 **Zerodha** - Placeholder (implement with kiteconnect library)
- 🔄 **Upstox** - Placeholder (implement with upstox library)  
- ✅ **Mock Broker** - For testing and development