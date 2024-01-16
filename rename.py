import os
global c
c = 1

def rename_files(directory):
    global c
    # Change directory to the specified path
    os.chdir(directory)

    # Iterate over files in the directory
    for filename in os.listdir(directory):
            # Construct the new filename
            new_prefix = f"' ({c}).mp4"

            # Rename the file
            os.rename(filename, new_prefix)
            print(f'Renamed: {filename} -> {new_prefix}')
            c = c+1

# Example usage
directory_path = r"C:\Users\iamum\Downloads\Zips\MassDownloader_editbyaxcp_user_saved_1_8_2024\New folder (2)"
rename_files(directory_path)
