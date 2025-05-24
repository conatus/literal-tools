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

def get_signed_cover_url(token, file_type="image/jpeg"):
    """Get a signed URL for uploading a book cover.
    
    Args:
        token (str): Authentication token
        file_type (str): MIME type of the image (default: "image/jpeg")
    
    Returns:
        dict: Contains signedUrl, key, and fileName for the upload
    """
    signed_url_query = {
        "query": """
        query signedUrlForCoverUpload($fileType: String!) {
          signedUrlForCoverUpload(fileType: $fileType) {
            signedUrl
            key
            fileName
          }
        }
        """,
        "variables": {
            "fileType": file_type
        }
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=signed_url_query, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print("Error getting signed URL:", data["errors"])
            return None
        return data["data"]["signedUrlForCoverUpload"]
    else:
        print(f"Request failed with status code {response.status_code}")
        print("Response:", response.text)
        return None

def create_book(token, book_data):
    """Create a new book in Literal.
    
    Args:
        token (str): Authentication token
        book_data (dict): Book information with the following fields:
            - title (str): Book title (required)
            - subtitle (str, optional): Book subtitle
            - description (str): Book description
            - authors (str): Author names, comma-separated
            - language (str): Language code (e.g., 'en')
            - isbn10 (str, optional): ISBN-10
            - isbn13 (str, optional): ISBN-13
            - pageCount (str, optional): Number of pages
            - publishedDate (str): Publication date (YYYY-MM-DD)
            - publisher (str): Publisher name
            - mature (bool): Whether the book is mature content
            - cover (str): URL to cover image
            - physicalFormat (str): Format (e.g., 'paperback')
    """
    create_book_query = {
        "query": """
        mutation createBook(
          $title: String!
          $subtitle: String
          $description: String!
          $authors: String!
          $language: String!
          $isbn10: String
          $isbn13: String
          $pageCount: String
          $publishedDate: String
          $publisher: String
          $mature: Boolean
          $cover: String
          $physicalFormat: String
        ) {
          createBook(
            title: $title
            subtitle: $subtitle
            description: $description
            authors: $authors
            language: $language
            isbn10: $isbn10
            isbn13: $isbn13
            pageCount: $pageCount
            publishedDate: $publishedDate
            publisher: $publisher
            mature: $mature
            cover: $cover
            physicalFormat: $physicalFormat
          ) {
            id
            title
            subtitle
            authors {
              name
            }
          }
        }
        """,
        "variables": book_data
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=create_book_query, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print("Error creating book:", data["errors"])
            return None
        return data["data"]["createBook"]
    else:
        print(f"Request failed with status code {response.status_code}")
        print("Response:", response.text)
        return None

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

def upload_cover_image(signed_url, image_path):
    """Upload a cover image to DigitalOcean Spaces using a signed URL.
    
    Args:
        signed_url (str): The signed URL for uploading
        image_path (str): Path to the local image file
    
    Returns:
        bool: True if upload was successful, False otherwise
    """
    try:
        with open(image_path, 'rb') as image_file:
            headers = {
                'Content-Type': 'image/jpeg',
                'x-amz-acl': 'public-read'
            }
            response = requests.put(signed_url, data=image_file, headers=headers)
            
            if response.status_code == 200:
                print("Cover image uploaded successfully")
                return True
            else:
                print(f"Upload failed with status code {response.status_code}")
                print("Response:", response.text)
                return False
    except Exception as e:
        print(f"Error uploading cover image: {e}")
        return False

def create_book_with_cover(token, book_data, cover_image_path):
    """Create a new book with a cover image in Literal.
    
    Args:
        token (str): Authentication token
        book_data (dict): Book information (see create_book function for details)
        cover_image_path (str): Path to the local cover image file
    
    Returns:
        dict: Created book data if successful, None otherwise
    """
    # Step 1: Get signed URL for cover upload
    signed_url_data = get_signed_cover_url(token)
    if not signed_url_data:
        print("Failed to get signed URL for cover upload")
        return None
    
    # Step 2: Upload the cover image
    if not upload_cover_image(signed_url_data["signedUrl"], cover_image_path):
        print("Failed to upload cover image")
        return None
    
    # Step 3: Create the book with the cover URL
    # The cover URL is constructed from the key returned by the signed URL
    book_data["cover"] = f"https://literal.club/covers/{signed_url_data['key']}"
    
    return create_book(token, book_data)

def get_book_data_interactive():
    """Interactively collect book information from the user.
    
    Returns:
        tuple: (book_data dict, cover_image_path str)
    """
    print("\nPlease provide the following information about your book:")
    
    book_data = {}
    
    # Required fields
    book_data["title"] = input("Title: ").strip()
    book_data["description"] = input("Description: ").strip()
    book_data["authors"] = input("Authors (comma-separated): ").strip()
    book_data["language"] = input("Language code (e.g., 'en', press Enter for 'en'): ").strip() or "en"
    book_data["publishedDate"] = input("Publication date (YYYY-MM-DD): ").strip()
    book_data["publisher"] = input("Publisher: ").strip()
    
    # Optional fields
    subtitle = input("Subtitle (optional, press Enter to skip): ").strip()
    if subtitle:
        book_data["subtitle"] = subtitle
        
    isbn10 = input("ISBN-10 (optional, press Enter to skip): ").strip()
    if isbn10:
        book_data["isbn10"] = isbn10
        
    isbn13 = input("ISBN-13 (optional, press Enter to skip): ").strip()
    if isbn13:
        book_data["isbn13"] = isbn13
        
    page_count = input("Number of pages (optional, press Enter to skip): ").strip()
    if page_count:
        book_data["pageCount"] = page_count
    
    mature = input("Is this book mature content? (y/n, default: n): ").strip().lower()
    book_data["mature"] = mature == 'y'
    
    physical_format = input("Physical format (e.g., 'paperback', 'hardcover', press Enter to skip): ").strip()
    if physical_format:
        book_data["physicalFormat"] = physical_format
    
    # Get cover image path
    cover_image_path = input("\nPath to cover image file: ").strip()
    
    return book_data, cover_image_path

if __name__ == "__main__":
    # Get token and profile_id (either from file or by logging in)
    token, profile_id = get_token()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "create-book":
        # Get book data interactively
        book_data, cover_image_path = get_book_data_interactive()
        
        # Create the book with cover
        result = create_book_with_cover(token, book_data, cover_image_path)
        if result:
            print("\nBook created successfully!")
            print(f"Title: {result['title']}")
            if result.get('subtitle'):
                print(f"Subtitle: {result['subtitle']}")
            print("Authors:", ", ".join(author['name'] for author in result['authors']))
        else:
            print("\nFailed to create book")
    else:
        # Default mode: show currently reading books
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

