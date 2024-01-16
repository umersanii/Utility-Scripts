import os
global c
c = 1

def rename_files(directory):
    global c
    os.chdir(directory)

    for filename in os.listdir(directory):
            new_prefix = f"' ({c}).mp4"

            os.rename(filename, new_prefix)
            print(f'Renamed: {filename} -> {new_prefix}')
            c = c+1

directory_path = r"path_to_folder_here"
rename_files(directory_path)
