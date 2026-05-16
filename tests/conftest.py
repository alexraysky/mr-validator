import sys
import os

# Add the source directory to the path so that tests can import modules
# both as 'from source.xxx' and just 'import xxx' if needed by the source itself.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'source')))
