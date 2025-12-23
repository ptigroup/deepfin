#!/usr/bin/env python3
"""Verify Linear issue status for a given session."""
import os
import sys

import requests


def verify_linear_status(session_num: int) -> bool:
    """Verify that a session's Linear issue is marked as Done.

    Args:
        session_num: The session number (1-18)

    Returns:
        True if issue is marked as completed, False otherwise
    """
    LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
    if not LINEAR_API_KEY:
        print("Error: LINEAR_API_KEY environment variable not set")
        print("Set it with: export LINEAR_API_KEY='your_key_here'")
        return False

    headers = {"Authorization": LINEAR_API_KEY, "Content-Type": "application/json"}

    # Calculate issue ID (Session 1 = BUD-5, Session 2 = BUD-6, etc.)
    issue_id = f"BUD-{session_num + 4}"

    query = f"""
    {{
      issue(id: "{issue_id}") {{
        identifier
        title
        state {{
          name
          type
        }}
      }}
    }}
    """

    response = requests.post(
        "https://api.linear.app/graphql", json={"query": query}, headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Error: HTTP {response.status_code}")
        print(response.text)
        return False

    data = response.json()

    if "errors" in data:
        print(f"❌ GraphQL Error: {data['errors']}")
        return False

    issue = data["data"]["issue"]

    print(f"\nSession {session_num} ({issue['identifier']}):")
    print(f"  Title: {issue['title']}")
    print(f"  State: {issue['state']['name']} ({issue['state']['type']})")

    if issue["state"]["type"] == "completed":
        print("  [DONE] Session marked as Done")
        return True
    else:
        print("  [TODO] Session NOT marked as Done")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/verify-linear.py <session_number>")
        print("Example: python scripts/verify-linear.py 5")
        sys.exit(1)

    try:
        session_num = int(sys.argv[1])
        if session_num < 1 or session_num > 18:
            print("Error: Session number must be between 1 and 18")
            sys.exit(1)

        success = verify_linear_status(session_num)
        sys.exit(0 if success else 1)

    except ValueError:
        print("Error: Session number must be an integer")
        sys.exit(1)
