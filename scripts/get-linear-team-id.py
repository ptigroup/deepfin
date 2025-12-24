#!/usr/bin/env python3
"""Get the correct Linear team ID for the workflow."""
import os
import sys
import requests


def get_team_id():
    """Get Linear team ID."""
    LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
    if not LINEAR_API_KEY:
        print("Error: LINEAR_API_KEY environment variable not set")
        print("\nTo set it:")
        print("  export LINEAR_API_KEY='lin_api_...'")
        print("\nTo get a key:")
        print("  1. Go to https://linear.app/settings/api")
        print("  2. Create a Personal API key with read access")
        return False

    headers = {"Authorization": LINEAR_API_KEY, "Content-Type": "application/json"}

    # Get teams
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

    response = requests.post(
        "https://api.linear.app/graphql",
        json={"query": query},
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Error: HTTP {response.status_code}")
        print(response.text)
        return False

    data = response.json()

    if "errors" in data:
        print(f"❌ GraphQL Error: {data['errors']}")
        return False

    teams = data["data"]["teams"]["nodes"]

    if not teams:
        print("❌ No teams found!")
        print("Make sure your API key has access to the Linear workspace.")
        return False

    print(f"\n✅ Found {len(teams)} team(s):\n")
    for i, team in enumerate(teams, 1):
        print(f"{i}. {team['name']}")
        print(f"   Key: {team['key']}")
        print(f"   ID:  {team['id']}")
        print()

    if len(teams) == 1:
        print(f"→ Use this ID in .github/workflows/linear-sync.yml:")
        print(f"  TEAM_ID = \"{teams[0]['id']}\"")
    else:
        print("→ Choose the correct team and use its ID in .github/workflows/linear-sync.yml")

    return True


if __name__ == "__main__":
    if not get_team_id():
        sys.exit(1)
