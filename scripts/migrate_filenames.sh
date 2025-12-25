#!/bin/bash

# Directory containing the images
TARGET_DIR="../output/geronimo"

# Check if directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Directory $TARGET_DIR does not exist."
    exit 1
fi

cd "$TARGET_DIR" || exit

echo "Renaming files in $TARGET_DIR..."

for file in *.png; do
    # Skip if file not found (e.g. empty dir)
    [ -e "$file" ] || continue

    # Check if file already starts with a timestamp (HH:MM_)
    if [[ "$file" =~ ^[0-9]{2}:[0-9]{2}_ ]]; then
        echo "Skipping $file (already has timestamp)"
        continue
    fi

    # Get file modification time in HH:MM format
    # %R is equivalent to %H:%M
    timestamp=$(date -r "$file" "+%H:%M")

    # New filename
    new_name="${timestamp}_${file}"

    echo "Renaming '$file' -> '$new_name'"
    mv "$file" "$new_name"
done

echo "Done."
