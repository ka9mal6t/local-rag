import os
import re


def get_static_files_paths(path, file_extension, *paths):
    file_paths = []
    pattern = re.compile(f".*{file_extension}$", re.IGNORECASE)

    for root, dirs, files in os.walk(os.path.join(path, "static", *paths)):
        for file in files:
            if pattern.match(file):
                file_paths.append(os.path.join(root, file))

    return file_paths