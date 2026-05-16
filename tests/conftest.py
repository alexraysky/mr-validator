import sys
import os

# Add both the project root and the source directory to sys.path so that tests can import
# modules as 'from source.xxx' (root) and internal modules can import each other as 'import xxx' (source).
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, 'source'))

