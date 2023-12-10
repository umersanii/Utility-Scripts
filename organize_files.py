import os
import shutil

def organize_desktop():
    desktop_path = os.path.expanduser("~/Desktop")

    # Create folders if they don't exist
    folders = ["Documents", "Video", "Code", "Audio", "Other Media"]
    for folder in folders:
        folder_path = os.path.join(desktop_path, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    # Get a list of all items on the desktop (files, directories, and shortcuts)
    items = [i for i in os.listdir(desktop_path)]

    def get_new_name(file_path):
        base_name, ext = os.path.splitext(file_path)
        index = 1
        while True:
            new_name = f"{base_name}({index}){ext}"
            if not os.path.exists(new_name):
                return new_name
            index += 1

    for item in items:
        item_path = os.path.join(desktop_path, item)

        if os.path.isfile(item_path):
            if item.endswith(('.lnk', '.url')):
                continue
            if item.endswith(('.txt', '.pdf', '.docx', ".rar")):
                target_folder = os.path.join(desktop_path, 'Documents')
            elif item.endswith(('.mp4', '.avi', '.mkv')):
                target_folder = os.path.join(desktop_path, 'Video')
            elif item.endswith(('.jpeg', '.jpg', '.png', '.gif', '.ico', '.jpeg', '.webp')):
                target_folder = os.path.join(desktop_path, 'Other Media')
            elif item.endswith(('.asm', '.cpp', '.h','.asm')):
                target_folder = os.path.join(desktop_path, 'Code')
            elif item.endswith(('.mp3', 'wav')):
                target_folder = os.path.join(desktop_path, 'Audio')
            else:
                continue

            target_path = os.path.join(target_folder, item)

            # If a file with the same name already exists, rename it
            if os.path.exists(target_path):
                new_name = get_new_name(target_path)
                shutil.move(item_path, new_name)
                try:
                    shutil.move(new_name, target_folder)
                except:
                    pass
            else:
                shutil.move(item_path, target_folder)
        # elif os.path.isdir(item_path):
        #     shutil.move(item_path, os.path.join(desktop_path, 'Folders', item))
        # elif os.path.islink(item_path):
        #     shutil.move(item_path, os.path.join(desktop_path, 'Shortcuts', item))


def organize_downloads():
    desktop_path = os.path.expanduser("~/Downloads")

    # Create folders if they don't exist
    folders = ["Documents", "Video", "Code", "Audio", "Other Media", "Executables", "Zips", "Torrent"]
    for folder in folders:
        folder_path = os.path.join(desktop_path, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    # Get a list of all items on the desktop (files, directories, and shortcuts)
    items = [i for i in os.listdir(desktop_path)]

    def get_new_name(file_path):
        base_name, ext = os.path.splitext(file_path)
        index = 1
        while True:
            new_name = f"{base_name}({index}){ext}"
            if not os.path.exists(new_name):
                return new_name
            index += 1

    for item in items:
        item_path = os.path.join(desktop_path, item)

        if os.path.isfile(item_path):
            if item.endswith(('.lnk', '.url')):
                continue
            if item.endswith(('.txt', '.pdf', '.docx', '.odt')):
                target_folder = os.path.join(desktop_path, 'Documents')
            elif item.endswith(('.mp4', '.avi', '.mkv')):
                target_folder = os.path.join(desktop_path, 'Video')
            elif item.endswith(('.py', '.cpp', '.h','.asm', '.md', '.css')):
                target_folder = os.path.join(desktop_path, 'Code')
            elif item.endswith(('.jpg', '.jpeg', '.png', '.gif', '.ico', '.jpeg')):
                target_folder = os.path.join(desktop_path, 'Other Media')
            elif item.endswith(('.mp3', 'wav')):
                target_folder = os.path.join(desktop_path, 'Audio')
            elif item.endswith(('.exe')):
                target_folder = os.path.join(desktop_path, 'Executables')
            elif item.endswith(( ".rar", ".7z")):
                target_folder = os.path.join(desktop_path, 'Zip')
            elif item.endswith(( ".torrent")):
                target_folder = os.path.join(desktop_path, 'Torrent')
            else:
                continue

            target_path = os.path.join(target_folder, item)

            # If a file with the same name already exists, rename it
            if os.path.exists(target_path):
                new_name = get_new_name(target_path)
                shutil.move(item_path, new_name)
                try:
                    shutil.move(new_name, target_folder)
                except:
                    pass
            else:
                shutil.move(item_path, target_folder)
        # elif os.path.isdir(item_path):
        #     shutil.move(item_path, os.path.join(desktop_path, 'Folders', item))
        # elif os.path.islink(item_path):
        #     shutil.move(item_path, os.path.join(desktop_path, 'Shortcuts', item))

if __name__ == "__main__":
    organize_desktop()
    organize_downloads()
