#!/bin/bash
# Comprehensive test runner for SpendSense

echo "=========================================="
echo "SpendSense Test Suite"
echo "=========================================="
echo ""

echo "Phase 1: Data Foundation"
echo "----------------------------------------"
python3 -c "from spendsense.storage.sqlite_manager import SQLiteManager; db = SQLiteManager(); db.connect(); db.create_schema(); print('✅ Database schema OK')"
echo ""

echo "Phase 2: Feature Engineering"
echo "----------------------------------------"
python3 test_phase2.py 2>&1 | tail -5
echo ""

echo "Phase 3: Persona System"
echo "----------------------------------------"
python3 test_phase3.py 2>&1 | tail -5
echo ""

echo "Phase 4: Recommendation Engine"
echo "----------------------------------------"
python3 test_phase4.py 2>&1 | tail -5
echo ""

echo "Phase 5: Guardrails & User UX"
echo "----------------------------------------"
python3 test_phase5.py 2>&1 | tail -5
echo ""

echo "Phase 6: Operator Dashboard"
echo "----------------------------------------"
python3 test_phase6.py 2>&1 | tail -5
echo ""

echo "End-to-End Test"
echo "----------------------------------------"
python3 test_end_to_end.py 2>&1 | tail -10
echo ""

echo "=========================================="
echo "All Tests Complete!"
echo "=========================================="

