#!/bin/bash

echo "=========================================="
echo "Backend Test Script"
echo "=========================================="
echo ""

echo "1. Testing Python syntax..."
echo "-------------------------------------------"
cd backend
python3 -m py_compile main.py
if [[ $? -eq 0 ]]; then
    echo "✅ Python syntax OK"
else
    echo "❌ Python syntax error"
    exit 1
fi
echo ""

echo "2. Checking imports..."
echo "-------------------------------------------"
python3 -c "
try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import asyncpg
    import pydantic
    print('✅ All imports available')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"
echo ""

echo "3. Checking Dockerfile..."
echo "-------------------------------------------"
if grep -q "uvicorn.*main:app" Dockerfile; then
    echo "✅ Dockerfile uses correct uvicorn command"
else
    echo "❌ Dockerfile command incorrect"
fi
echo ""

echo "4. Checking requirements.txt..."
echo "-------------------------------------------"
if grep -q "asyncpg" requirements.txt; then
    echo "✅ asyncpg present (PostgreSQL driver)"
else
    echo "❌ asyncpg missing"
fi

if grep -q "fastapi" requirements.txt; then
    echo "✅ fastapi present"
else
    echo "❌ fastapi missing"
fi
echo ""

echo "=========================================="
echo "Backend verification complete"
echo "=========================================="
