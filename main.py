import requests
import os
import json
from pathlib import Path
import getpass
import sys

url = "https://literal.club/graphql/"
TOKEN_FILE = Path.home() / ".literal_token"
DEBUG = "--debug" in sys.argv

# ANSI escape codes
ITALIC = "\033[3m"
RESET = "\033[0m"

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def get_token():
    # Try to load existing token
    if TOKEN_FILE.exists():
        debug_print("Token file exists")
        try:
            with open(TOKEN_FILE) as f:
                token_data = json.load(f)
                token = token_data.get("token")
                profile_id = token_data.get("profile_id")

                debug_print("Beginning token verification")
                if token and profile_id:
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
                        debug_print("Token is valid")
                        return token, profile_id
                    else:
                        debug_print("Token is invalid")
                        debug_print("Response:", response.text)
                        debug_print("Attempting to login")
                else:
                    debug_print("No token or profile_id found")
        except Exception as e:
            debug_print(f"Error reading token file: {e}")

    print("Please login to Literal")
    email = input("Email: ")
    password = getpass.getpass("Password: ")

    login_query = {
        "query": """
        mutation login($email: String!, $password: String!) {
          login(email: $email, password: $password) {
            token
            profile {
              id
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
    profile_id = login_data["data"]["login"]["profile"]["id"]
    
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump({"token": token, "profile_id": profile_id}, f)
        os.chmod(TOKEN_FILE, 0o600)  # Make file readable only by owner
    except Exception as e:
        debug_print(f"Warning: Could not save token: {e}")

    return token, profile_id

token, profile_id = get_token()

# Query for currently reading books
reading_books_query = {
    "query": """
    query booksByReadingStateAndProfile(
      $limit: Int!
      $offset: Int!
      $readingStatus: ReadingStatus!
      $profileId: String!
    ) {
      booksByReadingStateAndProfile(
        limit: $limit
        offset: $offset
        readingStatus: $readingStatus
        profileId: $profileId
      ) {
        title
        subtitle
        authors {
          id
          name
        }
      }
    }
    """,
    "variables": {
        "limit": 10,
        "offset": 0,
        "readingStatus": "IS_READING",
        "profileId": profile_id
    }
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.post(url, json=reading_books_query, headers=headers)

if response.status_code == 200:
    data = response.json()
    if "errors" in data:
        print("Error fetching reading states:", data["errors"])
    else:
        books = data["data"]["booksByReadingStateAndProfile"]
        if books:
            for book in books:
                authors = ", ".join(author['name'] for author in book['authors']) if book['authors'] else "Unknown Author"
                title = book['title']
                subtitle = f": {book['subtitle']}" if book.get('subtitle') else ""
                print(f"{authors} - {ITALIC}{title}{subtitle}{RESET}")
        else:
            print("Not currently reading any books")
else:
    print(f"Request failed with status code {response.status_code}")
    print("Response:", response.text)

