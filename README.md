# literal-tools

A tool for interacting with the Literal GraphQL API.

## Installation

1. Install uv:
```bash
pip install uv
```

2. Create and activate a virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

3. Install dependencies and the package in development mode:
```bash
uv pip install -r requirements.txt
uv pip install -e .
```

## Usage

The tool supports two main modes of operation:

### View Currently Reading Books
By default, running the script without arguments will show your currently reading books:
```bash
python main.py
```

### Create a New Book
To create a new book with a cover image, use the `create-book` command:
```bash
python main.py create-book
```

The first time you run it, you'll be prompted for your Literal.club credentials. The token will be saved in `~/.literal_token` for future use.

## Debug Mode
You can enable debug output by adding the `--debug` flag to any command:
```bash
python main.py --debug
# or
python main.py create-book --debug
```
