#!/usr/bin/env python3
"""Test the Linear workflow logic locally before running in GitHub Actions."""
import os
import sys
import requests


def test_workflow_logic():
    """Test the updated workflow logic."""
    LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
    if not LINEAR_API_KEY:
        print("Error: LINEAR_API_KEY environment variable not set")
        print("\nTo test:")
        print("  export LINEAR_API_KEY='lin_api_...'")
        print("  python scripts/test-linear-workflow.py")
        return False

    LINEAR_API_URL = "https://api.linear.app/graphql"
    headers = {
        "Authorization": LINEAR_API_KEY,
        "Content-Type": "application/json",
    }

    def execute_query(query, variables=None):
        """Execute GraphQL query against Linear API."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        print(f"DEBUG: Sending query with variables: {variables}")
        response = requests.post(LINEAR_API_URL, json=payload, headers=headers)

        # Check response first before raising
        if response.status_code != 200:
            print(f"HTTP Error {response.status_code}")
            print(f"Response: {response.text}")
            print(f"Query was: {query[:200]}...")
            print(f"Variables: {variables}")
            response.raise_for_status()

        data = response.json()
        if "errors" in data:
            print(f"GraphQL errors: {data['errors']}")
            raise Exception(f"GraphQL errors: {data['errors']}")
        return data.get("data", {})

    # Test with Session 7 (which just completed)
    SESSION_NUMBER = 7
    issue_number = SESSION_NUMBER + 4
    issue_identifier = f"BUD-{issue_number}"

    print(f"Testing workflow logic for {issue_identifier}...")
    print("=" * 60)

    # Step 1: Get issue by identifier (NEW APPROACH)
    print("\n[Step 1] Getting issue with team states...")
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

    try:
        issue_result = execute_query(get_issue_query, None)
    except Exception as e:
        print(f"❌ Failed to get issue: {e}")
        return False

    if not issue_result.get("issue"):
        print(f"❌ Issue {issue_identifier} not found")
        return False

    issue_id = issue_result["issue"]["id"]
    print(f"✅ Found issue: {issue_result['issue']['title']}")
    print(f"   ID: {issue_id}")
    print(f"   Team: {issue_result['issue']['team']['key']}")

    # Get workflow states from the issue's team
    team_states = issue_result["issue"]["team"]["states"]["nodes"]
    print(f"\n[Step 2] Found {len(team_states)} workflow states:")
    for state in team_states:
        print(f"   - {state['name']} ({state['type']})")

    done_state = next((s for s in team_states if s["type"] == "completed"), None)
    in_progress_state = next((s for s in team_states if s["type"] == "started"), None)

    if not done_state or not in_progress_state:
        print(f"\n❌ Could not find required workflow states")
        print(f"   Available states: {[s['name'] + ':' + s['type'] for s in team_states]}")
        return False

    print(f"\n✅ Found required states:")
    print(f"   Done: {done_state['name']} ({done_state['id']})")
    print(f"   In Progress: {in_progress_state['name']} ({in_progress_state['id']})")

    print("\n" + "=" * 60)
    print("✅ Workflow logic test PASSED!")
    print("=" * 60)
    print("\nThe Linear sync workflow should work now.")
    print("It will be tested on the next PR merge.")
    return True


if __name__ == "__main__":
    if not test_workflow_logic():
        sys.exit(1)
