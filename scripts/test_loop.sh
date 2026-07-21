#!/usr/bin/env bash
#
# test_loop.sh — Run cleanup→deploy cycles for both projects until 3 consecutive
# successful executions for each, fixing issues along the way.
#
set -uo pipefail

export PATH="$HOME/.local/bin:$PATH"
cd /usr/local/google/home/ppardyak/Dogfood/sudoku

PROJECTS=("ppardyak-cad" "ppardyak-new-project")
MAX_GLOBAL_RETRIES=10
SUCCESS_NEEDED=3

declare -A SUCCESS_COUNT
for p in "${PROJECTS[@]}"; do
  SUCCESS_COUNT[$p]=0
done

run_cycle() {
  local project=$1
  echo
  echo "================================================================"
  echo "  CYCLE for ${project} (successes so far: ${SUCCESS_COUNT[$project]}/${SUCCESS_NEEDED})"
  echo "================================================================"

  # Cleanup
  echo "--- CLEANUP ---"
  echo "y" | PROJECT_ID=${project} ./scripts/cleanup.sh 2>&1
  local cleanup_exit=$?
  if [ $cleanup_exit -ne 0 ]; then
    echo "❌ CLEANUP FAILED (exit $cleanup_exit) for ${project}"
    return 1
  fi

  # Wait for API deactivation to settle before re-enabling.
  echo "  Waiting 30s for API state to settle..."
  sleep 30

  # Verify cleanup via last audit file
  local last_audit=$(ls -t audits/audit_${project}_cleanup-post_*.md 2>/dev/null | head -1)
  if [ -n "$last_audit" ]; then
    if grep -q "Cloud Run services | 0" "$last_audit" 2>/dev/null && \
       grep -q "Artifact Registry repos | 0" "$last_audit" 2>/dev/null; then
      echo "✅ Post-cleanup audit: clean state confirmed"
    else
      echo "⚠️  Post-cleanup audit: state not clean"
    fi
  fi

  # Deploy
  echo "--- DEPLOY ---"
  rm -rf terraform/.terraform
  rm -f terraform/terraform.tfstate.${project} terraform/terraform.tfstate.${project}.backup
  PROJECT_ID=${project} TF_ARGS="-auto-approve" ./scripts/deploy.sh 2>&1
  local deploy_exit=$?
  if [ $deploy_exit -ne 0 ]; then
    echo "❌ DEPLOY FAILED (exit $deploy_exit) for ${project}"
    return 1
  fi

  # Verify deploy via last audit file
  local deploy_audit=$(ls -t audits/audit_${project}_setup-post_*.md 2>/dev/null | head -1)
  if [ -n "$deploy_audit" ]; then
    if grep -q "Cloud Run services | 1" "$deploy_audit" 2>/dev/null; then
      echo "✅ Post-deploy audit: deployed state confirmed"
    else
      echo "⚠️  Post-deploy audit: state not as expected"
    fi
  fi

  echo "✅ CYCLE PASSED for ${project}"
  return 0
}

for attempt in $(seq 1 $MAX_GLOBAL_RETRIES); do
  echo
  echo "############################################################"
  echo "  GLOBAL ATTEMPT ${attempt}/${MAX_GLOBAL_RETRIES}"
  echo "  Successes: cad=${SUCCESS_COUNT[ppardyak-cad]}/${SUCCESS_NEEDED}, new=${SUCCESS_COUNT[ppardyak-new-project]}/${SUCCESS_NEEDED}"
  echo "############################################################"

  all_passed=true

  for project in "${PROJECTS[@]}"; do
    # Skip if already has enough successes
    if [ ${SUCCESS_COUNT[$project]} -ge $SUCCESS_NEEDED ]; then
      echo "✅ ${project} already has ${SUCCESS_NEEDED} successes, skipping"
      continue
    fi

    if run_cycle "$project"; then
      SUCCESS_COUNT[$project]=$(( ${SUCCESS_COUNT[$project]} + 1 ))
      echo "📊 ${project} success count: ${SUCCESS_COUNT[$project]}/${SUCCESS_NEEDED}"
    else
      SUCCESS_COUNT[$project]=0
      all_passed=false
      echo "📊 ${project} success count reset to 0/${SUCCESS_NEEDED}"
    fi
  done

  # Clean up both at the end of each attempt
  for project in "${PROJECTS[@]}"; do
    echo "--- FINAL CLEANUP of ${project} ---"
    echo "y" | PROJECT_ID=${project} ./scripts/cleanup.sh 2>&1
  done

  # Check if all have enough successes
  all_done=true
  for project in "${PROJECTS[@]}"; do
    if [ ${SUCCESS_COUNT[$project]} -lt $SUCCESS_NEEDED ]; then
      all_done=false
    fi
  done

  if $all_done; then
    echo
    echo "============================================"
    echo "  🎉 ALL TESTS PASSED!"
    echo "  3 consecutive successful cleanup→deploy cycles for both projects."
    echo "============================================"
    exit 0
  fi

  echo
  echo "Current scores: cad=${SUCCESS_COUNT[ppardyak-cad]}/${SUCCESS_NEEDED}, new=${SUCCESS_COUNT[ppardyak-new-project]}/${SUCCESS_NEEDED}"
done

echo
echo "❌ Exceeded max retries ($MAX_GLOBAL_RETRIES) without 3 consecutive successes."
echo "Final scores: cad=${SUCCESS_COUNT[ppardyak-cad]}/${SUCCESS_NEEDED}, new=${SUCCESS_COUNT[ppardyak-new-project]}/${SUCCESS_NEEDED}"
exit 1
