#!/bin/bash
# JavaScript validation runner for CI/CD pipelines
# This script validates JavaScript code quality and defensive programming patterns

echo "🚀 Running JavaScript validation checks..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Run the validation script
python3 validate_js.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ All JavaScript validation checks passed!"
    echo "📝 Summary:"
    echo "   - No undefined function references"
    echo "   - All DOM access is safely protected with null checks"
    echo "   - Event handlers use defensive programming patterns"
    echo "   - API calls have proper error handling"
    echo "   - No problematic references to non-existent functionality"
else
    echo "❌ JavaScript validation failed!"
    echo "📝 Please fix the issues above before continuing."
fi

exit $exit_code