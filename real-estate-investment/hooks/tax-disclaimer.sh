#!/bin/bash
# Read tool input from stdin
INPUT=$(cat)

# Check if content relates to tax/legal topics
if echo "$INPUT" | grep -qi -e "tax" -e "depreciation" -e "1031" -e "cost segregation" -e "exchange" -e "opportunity zone" -e "entity structure"; then
  echo "Reminder: Tax analysis is for educational purposes only. Recommend consulting a CPA or tax attorney." >&2
fi

exit 0
