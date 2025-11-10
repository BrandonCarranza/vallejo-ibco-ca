#!/bin/bash
set -e

echo "Running smoke tests..."

# Test health endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$response" != "200" ]; then
    echo "❌ Health check failed (HTTP $response)"
    exit 1
fi
echo "✅ Health check passed"

# Test API endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/cities)
if [ "$response" != "200" ]; then
    echo "❌ API test failed (HTTP $response)"
    exit 1
fi
echo "✅ API test passed"

# Test database connection
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/detailed)
if [ "$response" != "200" ]; then
    echo "❌ Database health check failed (HTTP $response)"
    exit 1
fi
echo "✅ Database connection OK"

# Test root endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ "$response" != "200" ]; then
    echo "❌ Root endpoint test failed (HTTP $response)"
    exit 1
fi
echo "✅ Root endpoint OK"

# Test OpenAPI docs
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$response" != "200" ]; then
    echo "❌ Docs endpoint test failed (HTTP $response)"
    exit 1
fi
echo "✅ API documentation OK"

echo ""
echo "✅ All smoke tests passed!"
