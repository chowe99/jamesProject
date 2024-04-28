import os
import sys
import fnmatch

def cat_files(directory, ignore_patterns):
    for root, dirs, files in os.walk(directory, topdown=True):
        # Filter directories according to ignore patterns
        dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, pattern) for pattern in ignore_patterns)]
        
        # Process each file in the current directory
        for filename in files:
            filepath = os.path.join(root, filename)
            if not any(fnmatch.fnmatch(filepath, pattern) for pattern in ignore_patterns):
                try:
                    print(f"Contents of {filepath}:")
                    with open(filepath, 'r') as file:
                        print(file.read())
                        print("-" * 40)  # Print a separator after the contents of each file
                except Exception as e:
                    print(f"Could not read file {filepath}. Error: {e}")

def main():
    if len(sys.argv) < 3 or not sys.argv[1] == "-I":
        print("Usage: python cat_files.py -I \"venv|*.cfg|*.pyc|__pycache__\" <directory>")
        return

    ignore_patterns = sys.argv[2].split('|')
    directory = sys.argv[3]

    cat_files(directory, ignore_patterns)

if __name__ == "__main__":
    main()

