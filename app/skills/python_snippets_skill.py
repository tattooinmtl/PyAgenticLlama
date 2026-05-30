"""
Python Snippets Skill for llama.cpp
───────────────────────────────────
Production-ready Python code patterns for data processing, utilities,
algorithms, file I/O, and common development tasks.

Usage:
  execute(category="data_processing", type="json_parsing")
  execute(search="file")
  execute(list=True)
"""

SNIPPETS_DB = {
    # ──────────────────────────────────────────────────────────────────
    # DATA PROCESSING
    # ──────────────────────────────────────────────────────────────────
    "data_processing": {
        "json_parsing": {
            "description": "Parse, validate, and manipulate JSON data",
            "code": """
import json
from pathlib import Path
from typing import Any, Dict, List

# Parse JSON from string
data = json.loads('{"name": "John", "age": 30}')

# Parse JSON from file
with open('data.json', 'r') as f:
    data = json.load(f)

# Write JSON to file with pretty printing
with open('output.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# Safe JSON parsing with error handling
def safe_json_load(json_str: str) -> Dict[str, Any] | None:
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return None

# Parse and filter large JSON
def filter_json_objects(json_array: List[Dict], key: str, value: Any) -> List[Dict]:
    return [obj for obj in json_array if obj.get(key) == value]

# Deep merge dictionaries
def deep_merge(base: Dict, updates: Dict) -> Dict:
    result = base.copy()
    for key, val in updates.items():
        if isinstance(val, dict) and key in result and isinstance(result[key], dict):
            result[key] = deep_merge(result[key], val)
        else:
            result[key] = val
    return result

# Example usage
users = [
    {"id": 1, "name": "Alice", "active": True},
    {"id": 2, "name": "Bob", "active": False}
]
active_users = filter_json_objects(users, "active", True)
print(active_users)  # [{'id': 1, 'name': 'Alice', 'active': True}]
"""
        },
        "csv_data": {
            "description": "Read, process, and write CSV files",
            "code": """
import csv
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

# Read CSV into list of dicts
def read_csv(filepath: str) -> List[Dict]:
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

# Write list of dicts to CSV
def write_csv(filepath: str, data: List[Dict], fieldnames: List[str]):
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

# Filter CSV by condition
def filter_csv(filepath: str, key: str, value: str) -> List[Dict]:
    data = read_csv(filepath)
    return [row for row in data if row.get(key) == value]

# Group CSV data by column
def group_by_column(data: List[Dict], column: str) -> Dict[str, List[Dict]]:
    groups = defaultdict(list)
    for row in data:
        groups[row.get(column)].append(row)
    return dict(groups)

# Calculate aggregates
def calculate_aggregate(data: List[Dict], numeric_column: str) -> Dict[str, float]:
    values = [float(row[numeric_column]) for row in data if numeric_column in row]
    if not values:
        return {}
    return {
        'sum': sum(values),
        'mean': sum(values) / len(values),
        'min': min(values),
        'max': max(values),
        'count': len(values)
    }

# Example: Read, filter, aggregate
users = read_csv('users.csv')
active_users = filter_csv('users.csv', 'status', 'active')
by_department = group_by_column(users, 'dept')
salary_stats = calculate_aggregate(users, 'salary')
print(salary_stats)  # {'sum': 450000, 'mean': 150000, ...}
"""
        },
        "list_dict_operations": {
            "description": "Common operations on lists and dictionaries",
            "code": """
from typing import List, Dict, Any
from collections import Counter, defaultdict
from itertools import groupby

# Flatten nested list
def flatten(nested_list: List) -> List:
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result

# Count occurrences
items = ['a', 'b', 'a', 'c', 'a']
counts = Counter(items)
print(counts)  # Counter({'a': 3, 'b': 1, 'c': 1})

# Group consecutive items
data = [1, 1, 2, 2, 2, 3, 1]
grouped = [(k, list(g)) for k, g in groupby(data)]
print(grouped)  # [(1, [1, 1]), (2, [2, 2, 2]), (3, [3]), (1, [1])]

# Sort dict by value
scores = {'alice': 95, 'bob': 87, 'charlie': 92}
sorted_scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))
print(sorted_scores)  # {'alice': 95, 'charlie': 92, 'bob': 87}

# Merge multiple dicts
dict1 = {'a': 1, 'b': 2}
dict2 = {'c': 3, 'd': 4}
merged = {**dict1, **dict2}
print(merged)  # {'a': 1, 'b': 2, 'c': 3, 'd': 4}

# Create dict from pairs
pairs = [('name', 'John'), ('age', 30), ('city', 'NYC')]
person = dict(pairs)
print(person)  # {'name': 'John', 'age': 30, 'city': 'NYC'}

# Remove duplicates while preserving order
def remove_duplicates(items: List[Any]) -> List[Any]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

# Filter dict
def filter_dict(d: Dict, keys: List[str]) -> Dict:
    return {k: v for k, v in d.items() if k in keys}

user = {'id': 1, 'name': 'Alice', 'email': 'alice@ex.com', 'password': 'xxx'}
safe_user = filter_dict(user, ['id', 'name', 'email'])
print(safe_user)  # {'name': 'Alice', 'email': 'alice@ex.com'}
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # FILE I/O
    # ──────────────────────────────────────────────────────────────────
    "file_io": {
        "file_operations": {
            "description": "Read, write, and manipulate files safely",
            "code": """
from pathlib import Path
import tempfile
import shutil
from typing import List

# Read file with error handling
def read_file(filepath: str, encoding: str = 'utf-8') -> str | None:
    try:
        return Path(filepath).read_text(encoding=encoding)
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

# Write file safely (with backup)
def write_file_safe(filepath: str, content: str, create_backup: bool = True):
    path = Path(filepath)
    
    # Create backup if file exists
    if path.exists() and create_backup:
        backup = Path(f"{filepath}.bak")
        shutil.copy(filepath, backup)
    
    # Write with temp file first (atomic)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    # Replace original
    Path(tmp_path).replace(filepath)

# Read file line by line (memory efficient)
def read_lines(filepath: str) -> List[str]:
    try:
        with open(filepath, 'r') as f:
            return [line.rstrip('\\n') for line in f]
    except Exception as e:
        print(f"Error: {e}")
        return []

# Append to file
def append_file(filepath: str, content: str):
    Path(filepath).write_text(
        Path(filepath).read_text() + "\\n" + content
    )

# List files by pattern
def find_files(directory: str, pattern: str) -> List[str]:
    return [str(p) for p in Path(directory).glob(pattern)]

# Get file info
def file_info(filepath: str) -> Dict:
    path = Path(filepath)
    return {
        'exists': path.exists(),
        'size_bytes': path.stat().st_size if path.exists() else None,
        'is_file': path.is_file(),
        'is_dir': path.is_dir(),
        'absolute': str(path.absolute())
    }

# Create directory with parents
def ensure_dir(dirpath: str):
    Path(dirpath).mkdir(parents=True, exist_ok=True)

# Example usage
content = "Hello, World!"
write_file_safe('output.txt', content)
lines = read_lines('output.txt')
info = file_info('output.txt')
print(info)
"""
        },
        "path_handling": {
            "description": "Cross-platform path manipulation with pathlib",
            "code": """
from pathlib import Path
import os

# Current working directory
cwd = Path.cwd()
print(cwd)  # /home/user/project

# Construct paths safely (cross-platform)
config_file = Path.home() / '.config' / 'myapp' / 'config.json'
print(config_file)  # /home/user/.config/myapp/config.json

# Get file parts
path = Path('/home/user/documents/report.pdf')
print(path.name)        # report.pdf
print(path.stem)        # report
print(path.suffix)      # .pdf
print(path.parent)      # /home/user/documents
print(path.parts)       # ('/', 'home', 'user', 'documents', 'report.pdf')

# Join paths
base = Path('/data')
file = base / 'input' / 'file.txt'
print(file)  # /data/input/file.txt

# Check path properties
path = Path('myfile.txt')
print(path.exists())    # True/False
print(path.is_file())   # True/False
print(path.is_dir())    # True/False
print(path.is_absolute())  # True/False

# Get relative path
base = Path('/home/user/projects')
full = Path('/home/user/projects/app/src/main.py')
relative = full.relative_to(base)
print(relative)  # app/src/main.py

# Resolve to absolute path
symlink = Path('~/projects/myapp')
absolute = symlink.expanduser().resolve()

# Glob patterns
py_files = list(Path('.').glob('**/*.py'))  # All .py files recursively
print(len(py_files))
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # STRING & TEXT
    # ──────────────────────────────────────────────────────────────────
    "string_text": {
        "string_manipulation": {
            "description": "Common string operations and text processing",
            "code": """
import re
from typing import List

# Case transformations
text = "Hello World"
print(text.lower())        # hello world
print(text.upper())        # HELLO WORLD
print(text.title())        # Hello World
print(text.swapcase())     # hELLO wORLD

# String formatting
name = "Alice"
age = 30
print(f"{name} is {age} years old")  # f-string (preferred)
print("{} is {} years old".format(name, age))  # format()

# String methods
text = "  hello world  "
print(text.strip())       # hello world
print(text.replace('world', 'python'))  # hello python
print(text.split())       # ['hello', 'world']

# Regex matching
pattern = r'^[a-z]+@[a-z]+\\.[a-z]+$'
email = "user@example.com"
if re.match(pattern, email):
    print("Valid email")

# Find and replace with regex
text = "Order: 001, Order: 002, Order: 003"
numbers = re.findall(r'\\d+', text)
print(numbers)  # ['001', '002', '003']

# Split with regex
text = "apple, banana; orange | grape"
items = re.split(r'[,;|]', text)
print(items)  # ['apple', ' banana', ' orange ', ' grape']

# String validation
def is_valid_username(username: str) -> bool:
    # 3-20 chars, alphanumeric + underscore
    return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))

# Truncate string
def truncate(text: str, max_len: int = 50) -> str:
    return text[:max_len] + "..." if len(text) > max_len else text

# Join strings with separator
words = ['apple', 'banana', 'cherry']
result = ', '.join(words)
print(result)  # apple, banana, cherry

# Remove special characters
text = "Hello@123! How #are% you?"
clean = re.sub(r'[^a-zA-Z0-9\\s]', '', text)
print(clean)  # Hello123 How are you

# Convert string to title case (excluding small words)
def title_case(text: str) -> str:
    small_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at'}
    words = text.split()
    return ' '.join(
        word if word.lower() in small_words else word.capitalize()
        for word in words
    )
"""
        },
        "regex_patterns": {
            "description": "Common regex patterns for validation and parsing",
            "code": """
import re
from typing import Optional

# Email validation
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
def is_valid_email(email: str) -> bool:
    return bool(re.match(EMAIL_PATTERN, email))

# Phone number (US format)
PHONE_PATTERN = r'^\\(?\\d{3}\\)?[-.]?\\d{3}[-.]?\\d{4}$'
def is_valid_phone(phone: str) -> bool:
    return bool(re.match(PHONE_PATTERN, phone))

# URL validation
URL_PATTERN = r'^https?://[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}(:[0-9]+)?(/[^\\s]*)?$'
def is_valid_url(url: str) -> bool:
    return bool(re.match(URL_PATTERN, url))

# IP address (IPv4)
IP_PATTERN = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
def is_valid_ipv4(ip: str) -> bool:
    return bool(re.match(IP_PATTERN, ip))

# Hex color code
COLOR_PATTERN = r'^#?([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$'
def is_valid_hex_color(color: str) -> bool:
    return bool(re.match(COLOR_PATTERN, color))

# Extract all numbers from text
def extract_numbers(text: str):
    return re.findall(r'-?\\d+\\.?\\d*', text)

# Extract all words from text
def extract_words(text: str):
    return re.findall(r'\\b\\w+\\b', text)

# Extract URLs from text
def extract_urls(text: str):
    return re.findall(r'https?://[^\\s]+', text)

# Split camelCase into words
def split_camel_case(text: str) -> str:
    return re.sub(r'([a-z])([A-Z])', r'\\1 \\2', text).lower()

# Example usage
print(is_valid_email("user@example.com"))      # True
print(extract_numbers("Price: $19.99, Qty: 5")) # ['19.99', '5']
print(split_camel_case("myVariableName"))       # my variable name
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # UTILITIES & HELPERS
    # ──────────────────────────────────────────────────────────────────
    "utilities": {
        "logging_debug": {
            "description": "Logging configuration and debugging utilities",
            "code": """
import logging
import sys
import traceback
from datetime import datetime

# Setup basic logging
def setup_logging(name: str, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# File logging
def add_file_handler(logger, filepath: str):
    handler = logging.FileHandler(filepath)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Quick debug printer
def debug_print(label: str, value, pretty: bool = True):
    if pretty:
        import pprint
        print(f"\\n[DEBUG] {label}:")
        pprint.pprint(value)
    else:
        print(f"[DEBUG] {label}: {value}")

# Print full stack trace
def print_traceback():
    traceback.print_exc()

# Timer for profiling
class Timer:
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start = None
    
    def __enter__(self):
        self.start = datetime.now()
        return self
    
    def __exit__(self, *args):
        elapsed = (datetime.now() - self.start).total_seconds()
        print(f"{self.name} took {elapsed:.3f}s")

# Example usage
logger = setup_logging(__name__, logging.DEBUG)
logger.info("Application started")
logger.debug("Debug message")
logger.error("Error occurred")

with Timer("Database Query"):
    # Slow operation
    import time
    time.sleep(0.5)
"""
        },
        "decorators": {
            "description": "Useful decorator patterns for functions",
            "code": """
import functools
import time
from typing import Any, Callable

# Retry decorator
def retry(max_attempts: int = 3, delay: float = 1):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    print(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator

# Cache decorator (simple)
def cache(func: Callable):
    cached = {}
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = (args, tuple(kwargs.items()))
        if key not in cached:
            cached[key] = func(*args, **kwargs)
        return cached[key]
    return wrapper

# Timing decorator
def time_it(func: Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

# Type checking decorator
def validate_types(**type_checks):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for key, expected_type in type_checks.items():
                if key in kwargs and not isinstance(kwargs[key], expected_type):
                    raise TypeError(f"{key} must be {expected_type}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Example usage
@retry(max_attempts=3, delay=0.5)
def unstable_function():
    import random
    if random.random() < 0.7:
        raise Exception("Random failure")
    return "Success"

@time_it
def slow_function():
    time.sleep(0.1)
    return "Done"

@cache
def expensive_computation(n: int):
    return sum(range(n))

@validate_types(name=str, age=int)
def create_user(name: str, age: int):
    return {'name': name, 'age': age}
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # ALGORITHMS
    # ──────────────────────────────────────────────────────────────────
    "algorithms": {
        "sorting_searching": {
            "description": "Common sorting and searching algorithms",
            "code": """
from typing import List, Any

# Binary search
def binary_search(arr: List[int], target: int) -> int:
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1  # Not found

# Linear search
def linear_search(arr: List[Any], target: Any) -> int:
    for i, item in enumerate(arr):
        if item == target:
            return i
    return -1

# Bubble sort
def bubble_sort(arr: List[int]) -> List[int]:
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

# Quick sort
def quick_sort(arr: List[int]) -> List[int]:
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)

# Merge sort
def merge_sort(arr: List[int]) -> List[int]:
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left: List[int], right: List[int]) -> List[int]:
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

# Example usage
data = [64, 34, 25, 12, 22, 11, 90]
print(bubble_sort(data.copy()))      # [11, 12, 22, 25, 34, 64, 90]
print(binary_search([1, 3, 5, 7, 9], 5))  # 2
"""
        }
    }
}


def execute(**kwargs):
    """
    Execute the Python snippets skill.
    
    Parameters:
      category    - Category: data_processing, file_io, string_text, utilities, algorithms
      type        - Snippet type (e.g., "json_parsing", "file_operations")
      search      - Free-text search across snippets
      format      - Return format: "code" (default), "full"
      list        - If True, list all available snippets
    """
    
    category = str(kwargs.get("category", "")).strip().lower()
    snippet_type = str(kwargs.get("type", "")).strip().lower()
    search_term = str(kwargs.get("search", "")).strip().lower()
    output_format = str(kwargs.get("format", "code")).lower()
    list_only = bool(kwargs.get("list", False))

    # ──────────────────────────────────────────────────────────────────
    # LIST MODE
    # ──────────────────────────────────────────────────────────────────
    if list_only:
        lines = ["Available Python Snippets:\\n"]
        for cat in SNIPPETS_DB:
            lines.append(f"\\n📂 {cat.upper()}")
            for snippet_name in SNIPPETS_DB[cat]:
                desc = SNIPPETS_DB[cat][snippet_name].get("description", "")
                lines.append(f"  • {snippet_name}: {desc}")
        return "\\n".join(lines)

    # ──────────────────────────────────────────────────────────────────
    # SEARCH MODE
    # ──────────────────────────────────────────────────────────────────
    if search_term:
        lines = [f"Search results for: '{search_term}'\\n"]
        found = False
        
        for cat in SNIPPETS_DB:
            for snippet_name in SNIPPETS_DB[cat]:
                snippet = SNIPPETS_DB[cat][snippet_name]
                desc = snippet.get("description", "").lower()
                
                if search_term in desc or search_term in snippet_name.lower():
                    found = True
                    lines.append(f"\\n[{cat}] {snippet_name}")
                    lines.append(f"  {snippet.get('description', '')}")
        
        if not found:
            return f"No snippets found matching '{search_term}'"
        
        return "\\n".join(lines)

    # ──────────────────────────────────────────────────────────────────
    # RETRIEVE SPECIFIC SNIPPET
    # ──────────────────────────────────────────────────────────────────
    if not category or not snippet_type:
        return "Error: Both 'category' and 'type' required. Use list=True to see options."

    if category not in SNIPPETS_DB:
        return f"Error: Category '{category}' not found."

    if snippet_type not in SNIPPETS_DB[category]:
        return f"Error: Type '{snippet_type}' not found in '{category}'."

    snippet = SNIPPETS_DB[category][snippet_type]

    # ──────────────────────────────────────────────────────────────────
    # FORMAT OUTPUT
    # ──────────────────────────────────────────────────────────────────
    output = []
    output.append(f"📍 [{category}] {snippet_type}")
    output.append(f"   {snippet.get('description', '')}\\n")
    output.append("──── PYTHON CODE ────\\n")
    output.append(snippet.get("code", ""))

    return "\\n".join(output)
