import os
import json

def is_text_file(filepath):
    """
    Check if a file is a text file by trying to read the first few bytes.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read(1024)
            return True
    except (UnicodeDecodeError, IOError):
        return False

def create_notebook(root_dir, output_file):
    notebook = {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.8.5"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    # Add introduction and setup cell
    intro_cell = {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Project Codebase\n",
            "\n",
            "Run the cells below to recreate the project structure and files in this environment (e.g., Google Colab).\n",
            "\n",
            "## Setup\n",
            "1. Run all cells to create files.\n",
            "2. Install dependencies: `!pip install -r requirements.txt` (or backend/requirements.txt)\n",
            "3. a terminal or other cells to run the project.\n"
        ]
    }
    notebook["cells"].append(intro_cell)

    # Directories and files to exclude
    EXCLUDE_DIRS = {
        '.git', '.venv', 'venv', '__pycache__', 'node_modules', 
        'sample_audios', 'output_sample', 'site-packages', 'dist', 'build'
    }
    EXCLUDE_EXTENSIONS = {
        '.db', '.pyc', '.wav', '.mp3', '.png', '.jpg', '.jpeg', '.gif', 
        '.ico', '.pdf', '.exe', '.dll', '.so', '.dylib', '.bin', '.pkl'
    }
    EXCLUDE_FILES = {
        'package-lock.json', 'yarn.lock', 'meetings.db', 'test_meetings.db', 
        output_file, os.path.basename(__file__)
    }

    print(f"Scanning directory: {root_dir}")
    
    file_count = 0
    dirs_to_create = set()

    # First pass: Collect all necessary directories
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file in EXCLUDE_FILES: continue
            _, ext = os.path.splitext(file)
            if ext.lower() in EXCLUDE_EXTENSIONS: continue
            
            # Use relative path for Colab structure
            rel_dir = os.path.relpath(root, root_dir)
            if rel_dir != ".":
                dirs_to_create.add(rel_dir.replace(os.path.sep, '/'))

    # Add cell to create directories
    if dirs_to_create:
        sorted_dirs = sorted(list(dirs_to_create))
        mkdir_script = "import os\n\ndirs = [\n" + ",\n".join([f"    '{d}'" for d in sorted_dirs]) + "\n]\n\nfor d in dirs:\n    os.makedirs(d, exist_ok=True)\n    print(f'Created {d}')"
        
        mkdir_cell = {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + '\n' for line in mkdir_script.splitlines()]
        }
        notebook["cells"].append(mkdir_cell)


    for root, dirs, files in os.walk(root_dir):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file in EXCLUDE_FILES:
                continue
                
            _, ext = os.path.splitext(file)
            if ext.lower() in EXCLUDE_EXTENSIONS:
                continue
                
            filepath = os.path.join(root, file)
            # relative path for display and writefile
            rel_path = os.path.relpath(filepath, root_dir).replace(os.path.sep, '/')
            
            if not is_text_file(filepath):
                print(f"Skipping binary file: {rel_path}")
                continue

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Create Markdown cell for filename
                markdown_cell = {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [f"### `{rel_path}`"]
                }
                notebook["cells"].append(markdown_cell)
                
                # Create Code cell with content and %%writefile magic
                source_lines = [f"%%writefile {rel_path}\n"] + [line + '\n' for line in content.splitlines()]
                
                code_cell = {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": source_lines
                }
                notebook["cells"].append(code_cell)
                
                print(f"Added: {rel_path}")
                file_count += 1
                
            except Exception as e:
                print(f"Error reading {rel_path}: {e}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=2)
        
    print(f"\nSuccessfully created {output_file} with {file_count} files.")

if __name__ == "__main__":
    current_dir = os.getcwd()
    create_notebook(current_dir, "codebase_dump.ipynb")
