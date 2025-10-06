#!/bin/bash
#
# Example curl commands for testing Solido RAG endpoint
#

BASE_URL="${FAKEAI_URL:-http://localhost:8000}"
API_KEY="${FAKEAI_API_KEY:-test-key}"

echo "========================================================================"
echo "Solido RAG API Examples"
echo "========================================================================"
echo ""

# Example 1: Basic PVTMC query
echo "Example 1: PVTMC Query"
echo "------------------------"
curl -X POST "${BASE_URL}/rag/api/prompt" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "query": "What is PVTMC?",
    "filters": {"family": "Solido", "tool": "SDE"},
    "inference_model": "meta-llama/Llama-3.1-70B-Instruct",
    "top_k": 3
  }' | jq '.'
echo ""
echo ""

# Example 2: Sweep configuration query
echo "Example 2: Sweep Configuration"
echo "-------------------------------"
curl -X POST "${BASE_URL}/rag/api/prompt" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "query": "How to configure variable sweeps?",
    "filters": {"family": "Solido", "tool": "SDE"},
    "inference_model": "meta-llama/Llama-3.1-70B-Instruct",
    "top_k": 5
  }' | jq '.content, .retrieved_docs | length'
echo ""
echo ""

# Example 3: Multiple queries (array format)
echo "Example 3: Multiple Queries (Array)"
echo "------------------------------------"
curl -X POST "${BASE_URL}/rag/api/prompt" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "query": [
      "What is simulation setup?",
      "How to configure tests?",
      "What are corner groups?"
    ],
    "filters": {"family": "Solido", "tool": "SDE"},
    "inference_model": "meta-llama/Llama-3.1-70B-Instruct",
    "top_k": 4
  }' | jq '.usage'
echo ""
echo ""

# Example 4: Generic query without Solido filters
echo "Example 4: Generic RAG Query"
echo "-----------------------------"
curl -X POST "${BASE_URL}/rag/api/prompt" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{
    "query": "IC design best practices",
    "filters": {"category": "design"},
    "inference_model": "meta-llama/Llama-3.1-70B-Instruct",
    "top_k": 3
  }' | jq '.retrieved_docs[0] | {source, score}'
echo ""

echo ""
echo "========================================================================"
echo "All examples completed!"
echo "========================================================================"
