import requests
import os
import json
from pathlib import Path
import getpass

url = "https://literal.club/graphql/"
TOKEN_FILE = Path.home() / ".literal_token"

def get_token():
    # Try to load existing token
    if TOKEN_FILE.exists():
        print("Token file exists")
        try:
            with open(TOKEN_FILE) as f:
                token_data = json.load(f)
                token = token_data.get("token")

                print("Beginning token verification")
                if token:
                    # Verify token is still valid with a simple query
                    headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }
                    test_query = {
                        "query": """
                        {
                          me {
                            email
                          }
                        }
                        """
                    }
                    response = requests.post(url, json=test_query, headers=headers)
                    if response.status_code == 200:
                        print("Token is valid")
                        return token
                    else:
                        print("Token is invalid")
                        print("Response:", response.text)
                        exit(1)
                else:
                    print("No token found")
        except Exception as e:
            print(f"Error reading token file: {e}")

    # If we get here, we need to login
    print("Please login to Literal.club")
    email = input("Email: ")
    password = getpass.getpass("Password: ")

    login_query = {
        "query": """
        mutation login($email: String!, $password: String!) {
          login(email: $email, password: $password) {
            token
            email
            languages
            profile {
              id
              handle
              name
              bio
              image
            }
          }
        }
        """,
        "variables": {
            "email": email,
            "password": password
        }
    }

    login_response = requests.post(url, json=login_query)
    if login_response.status_code != 200:
        print(f"Login failed with status code {login_response.status_code}")
        print("Response:", login_response.text)
        exit(1)

    login_data = login_response.json()
    if "errors" in login_data:
        print("Login failed:", login_data["errors"])
        exit(1)

    token = login_data["data"]["login"]["token"]
    
    # Save token
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump({"token": token}, f)
        os.chmod(TOKEN_FILE, 0o600)  # Make file readable only by owner
    except Exception as e:
        print(f"Warning: Could not save token: {e}")

    return token

# Get token (either from file or by logging in)
token = get_token()

# Now make the introspection query with the token
introspection_query = {
    "query": """
    {
      __schema {
        mutationType {
          fields {
            name
          }
        }
      }
    }
    """
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.post(url, json=introspection_query, headers=headers)

if response.status_code == 200:
    data = response.json()
    mutations = data["data"]["__schema"]["mutationType"]["fields"]
    print("Available mutations:")
    for mutation in mutations:
        print(f"- {mutation['name']}")
else:
    print(f"Request failed with status code {response.status_code}")
    print("Response:", response.text)

