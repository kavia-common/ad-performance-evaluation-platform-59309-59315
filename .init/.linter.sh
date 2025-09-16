#!/bin/bash
cd /home/kavia/workspace/code-generation/ad-performance-evaluation-platform-59309-59315/creative_scoring_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

