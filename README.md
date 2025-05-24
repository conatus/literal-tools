# literal-tools

A tool for interacting with the Literal.club GraphQL API.

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

Run the script:
```bash
python main.py
```

The first time you run it, you'll be prompted for your Literal.club credentials. The token will be saved in `~/.literal_token` for future use.
