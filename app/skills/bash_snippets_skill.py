"""
Bash/Shell Snippets Skill for llama.cpp
───────────────────────────────────────
System administration, automation, file operations, text processing,
and Linux/Unix scripting patterns.

Usage:
  execute(category="system", type="disk_usage")
  execute(search="backup")
  execute(list=True)
"""

SNIPPETS_DB = {
    # ──────────────────────────────────────────────────────────────────
    # SYSTEM & MONITORING
    # ──────────────────────────────────────────────────────────────────
    "system": {
        "disk_usage": {
            "description": "Check disk space and find large files",
            "code": """
#!/bin/bash

# Disk space overview
df -h

# Disk space for specific mount
df -h /

# Usage by directory (top-level)
du -sh /*

# Top 10 largest directories
du -sh */ | sort -rh | head -10

# Find files larger than 100MB
find . -type f -size +100M

# Find top 10 largest files
find . -type f -exec du -h {} + | sort -rh | head -10

# Disk I/O stats (Linux)
iostat -x 1 5

# Monitor disk usage in real-time
watch -n 1 'df -h'
"""
        },
        "process_management": {
            "description": "Monitor, manage, and troubleshoot processes",
            "code": """
#!/bin/bash

# List all processes
ps aux

# List processes for user
ps aux | grep username

# Find process by name
pgrep -f "process_name"

# Get PID of process
pgrep -f "nginx"  # Returns PID

# Kill process by name
pkill -f "slow_process"

# Kill process by PID
kill -9 12345

# Monitor process in real-time
top -p PID

# Memory usage by process
ps aux --sort=-%mem | head -20

# CPU usage by process
ps aux --sort=-%cpu | head -20

# List open files by process
lsof -p PID

# Monitor system resources (top alternative)
htop

# Watch for long-running processes
watch -n 5 'ps aux | grep "[p]ython"'
"""
        },
        "system_info": {
            "description": "Get system information and diagnostics",
            "code": """
#!/bin/bash

# OS and kernel info
uname -a
cat /etc/os-release
lsb_release -a

# CPU information
nproc                    # Number of cores
lscpu                    # Detailed CPU info
cat /proc/cpuinfo

# Memory usage
free -h                  # Human-readable
free -b                  # In bytes
cat /proc/meminfo

# Uptime
uptime

# Load average
cat /proc/loadavg

# Network interfaces
ip addr show
ifconfig

# Network stats
netstat -tuln           # Listening ports
ss -tuln                # Modern alternative
netstat -s              # Network statistics

# System temperature
sensors
watch -n 1 sensors

# Hardware info
lsblk                   # Block devices
lsusb                   # USB devices
dmidecode               # Hardware details
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # FILE OPERATIONS
    # ──────────────────────────────────────────────────────────────────
    "file_ops": {
        "find_search": {
            "description": "Find files using various criteria",
            "code": """
#!/bin/bash

# Find files by name
find . -name "*.log"

# Find files modified in last 24 hours
find . -type f -mtime 0

# Find files larger than 1GB
find . -type f -size +1G

# Find empty files
find . -type f -empty

# Find files with specific permissions
find . -type f -perm 644

# Find files owned by user
find . -type f -user username

# Find and delete (be careful!)
find . -name "*.tmp" -delete

# Find and execute command
find . -name "*.bak" -exec rm {} \\;

# Find with case-insensitive search
find . -iname "*photo*"

# Find directories only
find . -type d -name "cache"

# Find with multiple criteria
find . -type f -name "*.log" -mtime +7

# Search in specific depth
find . -maxdepth 2 -name "*.py"

# Combine with other commands
find . -name "*.txt" -exec wc -l {} \\; | awk '{sum += $1} END {print sum}'
"""
        },
        "batch_rename": {
            "description": "Rename multiple files",
            "code": """
#!/bin/bash

# Rename with rename command
rename 's/old/new/' *.txt

# Rename pattern matching
rename 's/\\.jpg/.jpeg/' *.jpg

# Batch rename with loop
for file in *.txt; do
  mv "$file" "${file%.txt}.log"
done

# Rename with date
for file in *.jpg; do
  mv "$file" "photo_$(date +%s).jpg"
done

# Rename lowercase to uppercase
for file in *; do
  mv "$file" "$(echo $file | tr 'a-z' 'A-Z')"
done

# Add prefix to files
for file in *.txt; do
  mv "$file" "prefix_$file"
done

# Add suffix before extension
for file in *.pdf; do
  mv "$file" "${file%.pdf}_final.pdf"
done

# Using sed for pattern replacement
for file in file_[0-9]*.txt; do
  newname=$(echo "$file" | sed 's/file_/document_/')
  mv "$file" "$newname"
done
"""
        },
        "copy_archive": {
            "description": "Copy, backup, and archive files",
            "code": """
#!/bin/bash

# Copy with progress
cp -v file1 file2

# Copy directory recursively
cp -r /source /destination

# Copy preserving attributes
cp -p original copy

# Recursive copy with all attributes
cp -a /source /destination

# Copy to remote server
scp file.txt user@host:/path/to/dest

# Tar archive
tar -cvf archive.tar file1 file2 dir1

# Tar + gzip
tar -czvf archive.tar.gz directory/

# Tar specific files
tar -czf backup.tar.gz --include="*.py" --exclude="__pycache__" .

# Extract tar
tar -xvf archive.tar
tar -xzvf archive.tar.gz

# List tar contents
tar -tzf archive.tar.gz | head -20

# Zip archive
zip -r archive.zip directory/

# Unzip
unzip archive.zip -d /destination

# Backup with timestamp
backup_dir="/backups/backup_$(date +%Y%m%d_%H%M%S)"
cp -r /important/data "$backup_dir"

# Incremental backup with tar
tar -czf backup_$(date +%Y%m%d).tar.gz --newer-mtime-than backup_last.tar.gz /data
touch backup_last.tar.gz
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # TEXT PROCESSING
    # ──────────────────────────────────────────────────────────────────
    "text": {
        "grep_patterns": {
            "description": "Search text with grep and regex",
            "code": """
#!/bin/bash

# Basic grep
grep "pattern" file.txt

# Case-insensitive
grep -i "pattern" file.txt

# Invert match (exclude pattern)
grep -v "pattern" file.txt

# Show line numbers
grep -n "pattern" file.txt

# Count matches
grep -c "pattern" file.txt

# Show context (lines before/after)
grep -B 2 -A 2 "pattern" file.txt

# Search recursively in directory
grep -r "pattern" /path/to/dir

# Search only in specific files
grep "pattern" *.py

# Use regex
grep -E "^[0-9]{3}-[0-9]{4}$" file.txt

# Extended regex (simplify)
grep -E "email|contact" file.txt

# Word boundary (whole words only)
grep -w "word" file.txt

# Multiple patterns (OR)
grep -E "pattern1|pattern2" file.txt

# Exclude pattern
grep -v "exclude_this" file.txt

# Search for empty lines
grep "^$" file.txt

# Search for lines with at least N characters
grep "^.\\{100,\\}" file.txt

# Complex pattern: IP addresses
grep -E "^[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}$" file.txt
"""
        },
        "sed_awk": {
            "description": "Text transformation with sed and awk",
            "code": """
#!/bin/bash

# Replace text in file (sed)
sed 's/old/new/' file.txt                    # First occurrence per line
sed 's/old/new/g' file.txt                   # All occurrences
sed 's/old/new/2' file.txt                   # Second occurrence
sed -i 's/old/new/g' file.txt                # In-place edit

# Case-insensitive replace
sed 's/old/new/gi' file.txt

# Delete lines matching pattern
sed '/pattern/d' file.txt

# Delete specific line numbers
sed '5d' file.txt                            # Delete line 5
sed '5,10d' file.txt                         # Delete lines 5-10

# Print specific lines
sed -n '5,10p' file.txt

# Extract columns (awk)
awk '{print $1}' file.txt                    # First column
awk '{print $1, $3}' file.txt                # First and third

# Print with custom delimiter
awk -F: '{print $1}' /etc/passwd             # Using : as delimiter

# Sum column
awk '{sum += $2} END {print sum}' numbers.txt

# Filter rows
awk '$2 > 50 {print $1, $2}' data.txt        # Print rows where column 2 > 50

# Count lines/words/characters
wc -l file.txt                               # Lines
wc -w file.txt                               # Words
wc -c file.txt                               # Characters

# Print lines matching pattern
awk '/pattern/ {print}' file.txt

# Replace with regex group reference
sed 's/\\([0-9]\\+\\)/[\\1]/g' file.txt     # Wrap numbers in brackets

# Insert line before match
sed '/pattern/i\\New line' file.txt

# Append line after match
sed '/pattern/a\\New line' file.txt
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # SCRIPTING & AUTOMATION
    # ──────────────────────────────────────────────────────────────────
    "scripting": {
        "script_template": {
            "description": "Basic bash script template with best practices",
            "code": """
#!/bin/bash

# Script header
# Description: What this script does
# Usage: ./script.sh [options]
# Author: Your Name
# Date: 2024

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m'  # No Color

# Functions
log_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check prerequisites
check_requirements() {
  local required=("curl" "jq" "python3")
  for cmd in "${required[@]}"; do
    if ! command -v "$cmd" &> /dev/null; then
      log_error "$cmd is required but not installed"
      exit 1
    fi
  done
}

# Main script logic
main() {
  log_info "Starting script..."
  
  # Your code here
  local result=$(some_function)
  log_info "Result: $result"
  
  log_info "Script completed successfully"
}

# Parse arguments
if [[ $# -eq 0 ]]; then
  log_error "No arguments provided"
  echo "Usage: $0 <argument>"
  exit 1
fi

check_requirements
main "$@"
"""
        },
        "cron_scheduler": {
            "description": "Cron job examples and management",
            "code": """
#!/bin/bash

# View current cron jobs
crontab -l

# Edit cron jobs
crontab -e

# Delete all cron jobs
crontab -r

# Cron syntax: MIN HOUR DAY MONTH WEEKDAY COMMAND
# Example entries:

# Run every day at 2:30 AM
30 2 * * * /path/to/script.sh

# Run every 30 minutes
*/30 * * * * /path/to/script.sh

# Run every Monday at 9 AM
0 9 * * 1 /path/to/backup.sh

# Run on 1st of month at midnight
0 0 1 * * /path/to/monthly_task.sh

# Run every 6 hours
0 */6 * * * /path/to/script.sh

# Run multiple times per day
0 9,12,18 * * * /path/to/script.sh

# Run every weekday (Mon-Fri)
0 8 * * 1-5 /path/to/work_script.sh

# Logging cron output
0 2 * * * /path/to/script.sh >> /var/log/script.log 2>&1

# Send email on completion
0 2 * * * /path/to/script.sh | mail -s "Daily Report" admin@example.com

# Run as specific user
0 2 * * * /usr/sbin/cron-runner -u username /path/to/script.sh

# List system-wide cron jobs
ls -la /etc/cron.d/
cat /etc/crontab
"""
        },
        "error_handling": {
            "description": "Error handling and defensive programming in bash",
            "code": """
#!/bin/bash

# Exit on error
set -e                  # Exit on any error
set -u                  # Exit on undefined variable
set -o pipefail         # Exit if any command in pipe fails
set -E                  # Inherit ERR trap

# Trap errors
trap 'handle_error $? $LINENO' ERR

handle_error() {
  local exit_code=$1
  local line_number=$2
  echo "Error on line $line_number (exit code: $exit_code)" >&2
  exit "$exit_code"
}

# Cleanup on exit
trap 'cleanup' EXIT

cleanup() {
  # Remove temp files
  rm -rf "$TEMP_DIR"
  echo "Cleanup completed"
}

# Check if variable is set
if [[ -z "${VARIABLE:-}" ]]; then
  echo "VARIABLE is not set" >&2
  exit 1
fi

# Check if command exists
if ! command -v docker &> /dev/null; then
  echo "docker is required but not installed" >&2
  exit 1
fi

# Check if file exists
if [[ ! -f "$config_file" ]]; then
  echo "Config file not found: $config_file" >&2
  exit 1
fi

# Check if directory exists
if [[ ! -d "$directory" ]]; then
  mkdir -p "$directory" || {
    echo "Failed to create directory" >&2
    exit 1
  }
fi

# Try-catch pattern
if command -v sudo &> /dev/null; then
  sudo systemctl restart nginx
else
  systemctl restart nginx
fi || {
  echo "Failed to restart nginx" >&2
  exit 1
}
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # NETWORKING
    # ──────────────────────────────────────────────────────────────────
    "networking": {
        "network_diagnostics": {
            "description": "Network troubleshooting and diagnostics",
            "code": """
#!/bin/bash

# Test connectivity
ping -c 4 8.8.8.8

# DNS resolution
nslookup example.com
dig example.com

# Trace route
traceroute example.com

# Check open ports
netstat -tuln
ss -tuln                         # Modern alternative

# Check specific port
lsof -i :8080                   # Port 8080
netstat -tuln | grep :8080

# Network interface info
ip addr show
ip route show

# Check if port is listening
nc -zv hostname 22              # Port 22

# Download speed test
curl -O https://speedtest.example.com/file.bin
du -h file.bin

# Test TCP connection
timeout 3 bash -c 'echo "" | nc hostname 3306' && echo "Connected" || echo "Failed"

# Check DNS servers
cat /etc/resolv.conf

# Network statistics
ss -s
netstat -s

# Monitor network traffic
ifstat 1                        # Updates every 1 second
iftop                           # Top for network
nethogs                         # Network usage by process
"""
        },
        "ssh_scp": {
            "description": "SSH and SCP operations",
            "code": """
#!/bin/bash

# Basic SSH connection
ssh user@hostname

# SSH with port
ssh -p 2222 user@hostname

# Execute remote command
ssh user@hostname "ls -la /home"

# SSH with key file
ssh -i /path/to/key.pem user@hostname

# Copy file to remote
scp file.txt user@hostname:/path/to/dest

# Copy file from remote
scp user@hostname:/path/to/file.txt ./

# Copy directory
scp -r user@hostname:/path/to/dir ./

# SSH tunnel (local port forwarding)
ssh -L 8080:localhost:8080 user@hostname

# Reverse tunnel (remote port forwarding)
ssh -R 8080:localhost:8080 user@hostname

# SFTP transfer
sftp user@hostname
> get remote_file.txt
> put local_file.txt
> exit

# SCP with options
scp -P 2222 -r -v user@hostname:/src ./dest

# Add public key to remote
cat ~/.ssh/id_rsa.pub | ssh user@hostname "cat >> ~/.ssh/authorized_keys"

# SSH agent
eval $(ssh-agent)
ssh-add ~/.ssh/id_rsa
"""
        }
    }
}


def execute(**kwargs):
    """
    Execute the Bash/Shell snippets skill.
    
    Parameters:
      category  - Category: system, file_ops, text, scripting, networking
      type      - Snippet type (e.g., "disk_usage", "grep_patterns")
      search    - Free-text search across snippets
      list      - If True, list all available snippets
    """
    
    category = str(kwargs.get("category", "")).strip().lower()
    snippet_type = str(kwargs.get("type", "")).strip().lower()
    search_term = str(kwargs.get("search", "")).strip().lower()
    list_only = bool(kwargs.get("list", False))

    # ──────────────────────────────────────────────────────────────────
    # LIST MODE
    # ──────────────────────────────────────────────────────────────────
    if list_only:
        lines = ["Available Bash/Shell Snippets:\\n"]
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
    output.append("──── BASH SCRIPT ────\\n")
    output.append(snippet.get("code", ""))

    return "\\n".join(output)
