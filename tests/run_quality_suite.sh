#!/bin/bash
# XOCOA V2 Quality Assurance Suite

echo "🧐 [QA] Starting System Validation..."

# 1. Unit & Integration Tests
echo "🧪 [QA] Running Pytest (Integration)..."
# Run pytest inside the container to ensure environment consistency
docker exec xocoa_backend pytest tests/test_v2_infrastructure.py
PYTEST_STATUS=$?

# 2. Performance Benchmarking
if command -v k6 &> /dev/null
then
    echo "🏎️  [QA] Running Load Tests (k6)..."
    k6 run tests/load_test.js
    K6_STATUS=$?
else
    echo "⚠️  [QA] k6 not found, skipping load test."
    K6_STATUS=0
fi

# 3. Security (Container Scan)
if command -v trivy &> /dev/null
then
    echo "🛡️  [QA] Scanning Docker Image..."
    trivy image xocoa-backend:latest
    TRIVY_STATUS=$?
else
    echo "⚠️  [QA] trivy not found, skipping security scan."
    TRIVY_STATUS=0
fi

# Summary
echo "---------------------------------------"
if [ $PYTEST_STATUS -eq 0 ] && [ $K6_STATUS -eq 0 ] && [ $TRIVY_STATUS -eq 0 ]; then
    echo "✅ [RESULT] SYSTEM STABLE. Ready for Production."
    exit 0
else
    echo "❌ [RESULT] VALIDATION FAILED. Check logs before deploying."
    exit 1
fi
