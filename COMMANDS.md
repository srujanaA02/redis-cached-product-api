# Quick Start Commands

## Starting the Application

```bash
# Start all services
docker-compose up --build

# Start in detached mode
docker-compose up --build -d

# View logs
docker-compose logs -f

# View API logs only
docker-compose logs -f api-service

# Check service status
docker-compose ps
```

## Testing the API

```bash
# Health check
curl http://localhost:8080/health

# Create a product
curl -X POST http://localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Product",
    "description": "A test product",
    "price": 29.99,
    "stock_quantity": 100
  }'

# Get a product (replace {id} with actual product ID)
curl http://localhost:8080/products/{id}

# Update a product
curl -X PUT http://localhost:8080/products/{id} \
  -H "Content-Type: application/json" \
  -d '{
    "price": 24.99,
    "stock_quantity": 150
  }'

# Delete a product
curl -X DELETE http://localhost:8080/products/{id}
```

## Running Tests

```bash
# Run integration tests
python test_api.py

# Run automated test suite (requires rebuild with tests included)
docker-compose exec api-service python -m pytest tests/ -v
```

## Monitoring Cache Behavior

```bash
# Watch Redis commands in real-time
docker-compose exec redis redis-cli monitor

# View cache-related logs
docker-compose logs api-service | grep -i cache

# Check Redis keys
docker-compose exec redis redis-cli keys "product:*"

# View a cached product
docker-compose exec redis redis-cli get "product:{id}"
```

## Stopping the Application

```bash
# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Development Commands

```bash
# Rebuild after code changes
docker-compose up --build

# View API documentation
# Open browser to: http://localhost:8080/docs

# Access container shell
docker-compose exec api-service sh

# Check Redis connection
docker-compose exec redis redis-cli ping
```

## Useful Redis Commands (inside container)

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Inside redis-cli:
PING                          # Test connection
KEYS product:*                # List all product cache keys
GET product:{id}              # Get cached product data
TTL product:{id}              # Check time-to-live
DEL product:{id}              # Manually delete cache entry
FLUSHDB                       # Clear all cache (use with caution!)
INFO stats                    # View Redis statistics
```

## Troubleshooting

```bash
# Check all container logs
docker-compose logs

# Check specific service
docker-compose logs redis
docker-compose logs api-service

# Restart services
docker-compose restart

# Rebuild from scratch
docker-compose down -v
docker-compose up --build

# Check network connectivity
docker-compose exec api-service ping redis

# View environment variables
docker-compose exec api-service env | grep -E 'REDIS|API|DATABASE'
```
