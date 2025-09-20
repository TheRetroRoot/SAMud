#!/usr/bin/env python3
"""NPC configuration validator script."""

import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List


def validate_npc_config(file_path: Path) -> tuple[bool, List[str]]:
    """Validate an NPC configuration file.

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, [f"YAML parse error: {e}"]
    except Exception as e:
        return False, [f"File read error: {e}"]

    if not data or 'npc' not in data:
        errors.append("Missing 'npc' root key")
        return False, errors

    npc = data['npc']

    # Required fields
    required = ['id', 'name', 'description']
    for field in required:
        if field not in npc:
            errors.append(f"Missing required field: {field}")

    # Validate ID format (snake_case)
    if 'id' in npc:
        npc_id = npc['id']
        if not isinstance(npc_id, str) or not npc_id.replace('_', '').isalnum():
            errors.append(f"Invalid ID format: {npc_id} (use snake_case)")

    # Validate dialogue structure
    if 'dialogue' in npc:
        dialogue = npc['dialogue']
        if not isinstance(dialogue, dict):
            errors.append("'dialogue' must be a dictionary")
        else:
            # Check for recommended dialogue fields
            recommended_dialogue = ['greeting_new', 'greeting_return']
            for field in recommended_dialogue:
                if field not in dialogue:
                    errors.append(f"Warning: Missing recommended dialogue field: {field}")

    # Validate keywords
    if 'keywords' in npc:
        keywords = npc['keywords']
        if not isinstance(keywords, dict):
            errors.append("'keywords' must be a dictionary")
        else:
            for pattern, response in keywords.items():
                if not isinstance(pattern, str) or not isinstance(response, str):
                    errors.append(f"Invalid keyword entry: {pattern}")

    # Validate movement configuration
    if 'movement' in npc:
        movement = npc['movement']
        if not isinstance(movement, dict):
            errors.append("'movement' must be a dictionary")
        else:
            if 'allowed_rooms' in movement:
                if not isinstance(movement['allowed_rooms'], list):
                    errors.append("'allowed_rooms' must be a list")

            if 'tick_interval' in movement:
                interval = movement['tick_interval']
                if not isinstance(interval, (int, float)) or interval <= 0:
                    errors.append(f"Invalid tick_interval: {interval} (must be positive number)")

            if 'movement_probability' in movement:
                prob = movement['movement_probability']
                if not isinstance(prob, (int, float)) or not (0 <= prob <= 1):
                    errors.append(f"Invalid movement_probability: {prob} (must be 0.0-1.0)")

            if 'schedule' in movement:
                schedule = movement['schedule']
                if not isinstance(schedule, dict):
                    errors.append("'schedule' must be a dictionary")
                else:
                    valid_times = ['morning', 'afternoon', 'evening', 'night']
                    for time in schedule:
                        if time not in valid_times:
                            errors.append(f"Invalid schedule time: {time}")

    # Validate ambient actions
    if 'ambient_actions' in npc:
        actions = npc['ambient_actions']
        if not isinstance(actions, list):
            errors.append("'ambient_actions' must be a list")
        else:
            for action in actions:
                if not isinstance(action, str):
                    errors.append(f"Invalid ambient action: {action} (must be string)")

    return len(errors) == 0, errors


def main():
    """Validate all NPC configuration files."""
    if len(sys.argv) > 1:
        # Validate specific file
        file_path = Path(sys.argv[1])
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

        is_valid, errors = validate_npc_config(file_path)
        if is_valid:
            print(f"✓ {file_path} is valid")
        else:
            print(f"✗ {file_path} has errors:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
    else:
        # Validate all NPC files
        npc_dir = Path(__file__).parent
        npc_files = list(npc_dir.glob("*.yml"))

        # Skip the template file
        npc_files = [f for f in npc_files if f.name != "npc_schema_template.yml"]

        if not npc_files:
            print("No NPC configuration files found")
            sys.exit(0)

        all_valid = True
        for file_path in npc_files:
            is_valid, errors = validate_npc_config(file_path)
            if is_valid:
                print(f"✓ {file_path.name}")
            else:
                all_valid = False
                print(f"✗ {file_path.name}:")
                for error in errors:
                    print(f"  - {error}")

        if not all_valid:
            sys.exit(1)


if __name__ == "__main__":
    main()