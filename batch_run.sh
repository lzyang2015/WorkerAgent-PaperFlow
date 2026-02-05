#!/bin/zsh

# Define files
TASKS_FILE="tasks.txt"
RESULTS_FILE="batch_results.txt"
TEMP_TASKS_FILE="${TASKS_FILE}.tmp"

# 1. Environment Initialization
echo "Initializing environment..."
# Check if proxy_on is available (as command, function, or alias)
# We source zshrc just in case
if [[ -f "$HOME/.zshrc" ]]; then
    source "$HOME/.zshrc" >/dev/null 2>&1
fi
setopt aliases

if command -v proxy_on > /dev/null 2>&1 || alias proxy_on > /dev/null 2>&1; then
    echo "Executing proxy_on..."
    proxy_on
else
    echo "Warning: 'proxy_on' command/alias not found. Proceeding without explicit proxy initialization."
    echo "Please ensure your proxy is configured if needed."
fi

# Check if tasks file exists
if [[ ! -f "$TASKS_FILE" ]]; then
    echo "Error: $TASKS_FILE not found!"
    exit 1
fi

echo "Starting batch processing from $TASKS_FILE..."

# Initialize temp file for remaining tasks
: > "$TEMP_TASKS_FILE"

# Use a file descriptor for reading to avoid stdin conflict with subprocesses
# and use 'read' to parse fields directly
while read -r url profile_arg junk <&3; do
    # Skip comments (#) and empty lines
    if [[ -z "$url" || "$url" == "#"* ]]; then
        continue
    fi

    # Set default profile if not provided
    profile="${profile_arg:-default}"

    echo "---------------------------------------------------"
    echo "Processing: URL=$url, Profile=$profile"

    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    # Execute the python command
    # Redirect stdin to /dev/null to prevent Python from stealing input from the loop
    cmd="PYTHONPATH=. python3 src/cli/main.py \"$url\" --profile \"$profile\""
    echo "Executing: $cmd"
    
    # Run in a subshell or block to allow redirection
    PYTHONPATH=. python3 src/cli/main.py "$url" --profile "$profile" < /dev/null
    exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        echo "SUCCESS"
        echo "[$timestamp] SUCCESS: $url (Profile: $profile)" >> "$RESULTS_FILE"
    else
        echo "FAILURE (Exit Code: $exit_code)"
        echo "[$timestamp] FAILURE: $url (Profile: $profile) - Exit Code: $exit_code" >> "$RESULTS_FILE"
        # Keep failed task in the list
        # We reconstruct the line (or just save the url/profile)
        echo "$url $profile" >> "$TEMP_TASKS_FILE"
    fi

done 3< "$TASKS_FILE"

# Update tasks file
# If all successful, TEMP_TASKS_FILE will be empty (or contain only skipped comments)
# If some failed, they are preserved.
mv "$TEMP_TASKS_FILE" "$TASKS_FILE"

echo "---------------------------------------------------"
echo "Batch processing complete. Results saved to $RESULTS_FILE."
echo "Remaining tasks in $TASKS_FILE."