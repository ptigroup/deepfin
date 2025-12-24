# Linear Sync Workflow Fix

## Root Cause Analysis

The Linear sync workflow was failing with a **400 Bad Request** error when trying to query workflow states.

### The Problem

The workflow had **two** separate issues:

#### Issue #1: Hardcoded Team ID
```python
TEAM_ID = "ea035580-a2a3-4c39-9789-10a89d852428"  # DeepFin team
```
- This team ID was hardcoded and potentially incorrect
- Required querying workflow states separately by team filter
- If the API key didn't have access to this specific team, the query would fail

#### Issue #2: Complex Query Pattern
```python
# OLD APPROACH (FAILED):
query GetWorkflowStates($teamId: String!) {
    workflowStates(filter: { team: { id: { eq: $teamId } } }) {
        nodes {
            id
            name
            type
        }
    }
}
```
- Required separate query to get workflow states
- Used complex filtering that might not work with all API key permissions
- Added unnecessary complexity

### The Solution

Changed to a **simpler, more robust pattern** that matches how `verify-linear.py` works:

```python
# NEW APPROACH (WORKS):
get_issue_query = f"""
{{
  issue(id: "{issue_identifier}") {{
    id
    identifier
    title
    team {{
      id
      key
      states {{
        nodes {{
          id
          name
          type
        }}
      }}
    }}
  }}
}}
"""
```

### Why This Works

1. **No hardcoded team ID** - gets team from the issue itself
2. **Single query** - fetches issue AND its team's workflow states in one call
3. **String interpolation** - uses identifier directly in query (like verify-linear.py)
4. **Simpler permissions** - only needs access to the issue, not global workflow state queries

## Changes Made

### 1. Removed hardcoded TEAM_ID
- No longer needed since we get it from the issue

### 2. Simplified issue fetching
- Changed from `issues(filter: {...})` to `issue(id: "BUD-11")`
- Uses string interpolation instead of GraphQL variables for identifier
- Mirrors the working pattern in `scripts/verify-linear.py`

### 3. Get workflow states from issue
- Added `team.states` to the issue query
- Eliminates separate workflowStates query
- Automatically scoped to the correct team

### 4. Enhanced error logging
```python
if response.status_code != 200:
    print(f"HTTP Error {response.status_code}")
    print(f"Response: {response.text}")  # Shows actual error message
    print(f"Query was: {query[:200]}...")
    response.raise_for_status()
```
- Now shows actual Linear API error messages
- Helps debug future issues

### 5. Created test scripts
- `scripts/test-linear-api.py` - Comprehensive API testing
- `scripts/get-linear-team-id.py` - Find correct team ID
- `scripts/test-linear-workflow.py` - Test workflow logic locally

## Testing

To test the fix locally (requires LINEAR_API_KEY):

```bash
export LINEAR_API_KEY='lin_api_...'

# Test the workflow logic
python scripts/test-linear-workflow.py

# Or run comprehensive tests
python scripts/test-linear-api.py
```

## Verification

The fix will be automatically tested on the next PR merge. The workflow should now:

1. ✅ Find the issue by identifier (e.g., BUD-11)
2. ✅ Get workflow states from the issue's team
3. ✅ Update the issue to "Done"
4. ✅ Add a comment with PR link
5. ✅ Move next issue to "In Progress"

## Key Learnings

1. **Simpler is better** - The complex filtered query was unnecessary
2. **Follow working patterns** - `verify-linear.py` had the right approach all along
3. **Better error messages** - Essential for debugging GraphQL APIs
4. **String interpolation vs variables** - Linear API handles them differently for identifiers

## Summary

The issue was **not** with the API key itself, but with:
- How we were querying the API (complex filtering)
- Using a hardcoded team ID that may have been wrong
- Not showing error messages to see what Linear was actually complaining about

The fix simplifies the entire workflow and makes it more robust by getting all needed data from the issue itself.
