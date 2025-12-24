#!/usr/bin/env python3
"""Test Linear API queries to debug the workflow issue."""
import os
import sys
import json
import requests


def test_linear_api():
    """Test various Linear API queries."""
    LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
    if not LINEAR_API_KEY:
        print("Error: LINEAR_API_KEY environment variable not set")
        print("Set it with: export LINEAR_API_KEY='your_key_here'")
        return False

    headers = {"Authorization": LINEAR_API_KEY, "Content-Type": "application/json"}
    api_url = "https://api.linear.app/graphql"

    print("=" * 60)
    print("Linear API Testing")
    print("=" * 60)

    # Test 1: Viewer query (basic auth test)
    print("\n[Test 1] Testing API key validity...")
    query = """
    {
      viewer {
        id
        name
        email
      }
    }
    """
    response = requests.post(api_url, json={"query": query}, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"ERROR: {response.text}")
        return False

    data = response.json()
    if "errors" in data:
        print(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
        return False

    viewer = data["data"]["viewer"]
    print(f"✅ Authenticated as: {viewer['name']} ({viewer['email']})")

    # Test 2: Get teams
    print("\n[Test 2] Fetching teams...")
    query = """
    {
      teams {
        nodes {
          id
          name
          key
        }
      }
    }
    """
    response = requests.post(api_url, json={"query": query}, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"ERROR: {response.text}")
        return False

    data = response.json()
    if "errors" in data:
        print(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
        return False

    teams = data["data"]["teams"]["nodes"]
    print(f"✅ Found {len(teams)} team(s):")
    for team in teams:
        print(f"   - {team['name']} (key: {team['key']}, id: {team['id']})")

    if not teams:
        print("ERROR: No teams found!")
        return False

    # Use the first team for subsequent tests
    TEAM_ID = teams[0]["id"]
    TEAM_NAME = teams[0]["name"]
    print(f"\n→ Using team: {TEAM_NAME} ({TEAM_ID})")

    # Test 3: Get workflow states (THIS IS THE QUERY THAT FAILS IN WORKFLOW)
    print("\n[Test 3] Testing workflowStates query (with variables)...")
    query = """
    query GetWorkflowStates($teamId: String!) {
        workflowStates(filter: { team: { id: { eq: $teamId } } }) {
            nodes {
                id
                name
                type
            }
        }
    }
    """
    variables = {"teamId": TEAM_ID}
    print(f"Variables: {variables}")

    response = requests.post(api_url, json={"query": query, "variables": variables}, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ HTTP ERROR: {response.text}")
        print("\nThis is likely the problem in the workflow!")
    else:
        data = response.json()
        if "errors" in data:
            print(f"❌ GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
            print("\nThis is likely the problem in the workflow!")
        else:
            states = data["data"]["workflowStates"]["nodes"]
            print(f"✅ Found {len(states)} workflow state(s):")
            for state in states:
                print(f"   - {state['name']} ({state['type']}): {state['id']}")

    # Test 4: Get workflow states (without filter - simpler query)
    print("\n[Test 4] Testing workflowStates query (without filter)...")
    query = """
    {
      workflowStates {
        nodes {
          id
          name
          type
          team {
            id
            name
          }
        }
      }
    }
    """

    response = requests.post(api_url, json={"query": query}, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"ERROR: {response.text}")
    else:
        data = response.json()
        if "errors" in data:
            print(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
        else:
            states = data["data"]["workflowStates"]["nodes"]
            print(f"✅ Found {len(states)} workflow state(s) (all teams):")
            for state in states[:5]:  # Show first 5
                print(f"   - {state['name']} ({state['type']}) - Team: {state['team']['name']}")

    # Test 5: Get issue by identifier (like verify-linear.py does)
    print("\n[Test 5] Testing issue query with identifier string...")
    issue_id = "BUD-11"  # Session 7
    query = f"""
    {{
      issue(id: "{issue_id}") {{
        id
        identifier
        title
        state {{
          name
          type
        }}
      }}
    }}
    """

    response = requests.post(api_url, json={"query": query}, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"ERROR: {response.text}")
    else:
        data = response.json()
        if "errors" in data:
            print(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
        else:
            issue = data["data"]["issue"]
            if issue:
                print(f"✅ Found issue: {issue['identifier']} - {issue['title']}")
                print(f"   State: {issue['state']['name']} ({issue['state']['type']})")
            else:
                print(f"❌ Issue {issue_id} not found")

    # Test 6: Get issue with variables (like workflow does)
    print("\n[Test 6] Testing issue query with identifier via filter...")
    query = """
    query GetIssue($identifier: String!, $teamId: String!) {
        issues(filter: { identifier: { eq: $identifier }, team: { id: { eq: $teamId } } }) {
            nodes {
                id
                identifier
                title
            }
        }
    }
    """
    variables = {"identifier": issue_id, "teamId": TEAM_ID}
    print(f"Variables: {variables}")

    response = requests.post(api_url, json={"query": query, "variables": variables}, headers=headers)
    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"ERROR: {response.text}")
    else:
        data = response.json()
        if "errors" in data:
            print(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
        else:
            issues = data["data"]["issues"]["nodes"]
            if issues:
                print(f"✅ Found {len(issues)} issue(s):")
                for issue in issues:
                    print(f"   - {issue['identifier']}: {issue['title']}")
            else:
                print(f"❌ No issues found for {issue_id}")

    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    if not test_linear_api():
        sys.exit(1)
