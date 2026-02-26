# The entire point of this is that if there is crashing all data is saved and handled safely
# And there should be an avoidance of all errors

from .config import config
import os
import json
from pathlib import Path
import shutil
from tkinter import messagebox
from tkinter import filedialog
import tkinter as tk

def safe_json_load(filepath : str):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}

def safe_json_store(filepath : str, data : dict):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def set_always_sync_on_startup(new_state_ : tk.BooleanVar):
    new_state = new_state_.get()
    current_state = config.get("StartupBackupSync", False)
    do_sync = config.get("PerformExternalSync", False)
    if not do_sync:
        messagebox.showwarning("Unable to always startup sync", 
                           "External sync not setup for always sync on startup")
        new_state_.set(False)
        return
    settings = safe_json_load(config["SettingsFile"])
    settings["StartupBackupSync"] = new_state
    config["StartupBackupSync"] = new_state 
    safe_json_store(config["SettingsFile"], settings)



def safe_copy_file(source_file : str, destination_file : str):
    try:
        # This will overwrite destination_file if it already exists
        shutil.copy2(source_file, destination_file)
        print(f"Successfully copied and overwrote {destination_file}")
    except shutil.SameFileError:
        print("Source and destination are the same file.")
    except PermissionError:
        print("Permission denied.")
    except FileNotFoundError:
        print("Source file not found or destination directory does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

def safe_copy_dir(source_dir : str, destination_dir : str, relative_ignore = []):
    try_ignore = [path for path in relative_ignore if os.path.exists(os.path.join(source_dir, path))]
    
    try:
        # Copy the entire directory tree
        print(try_ignore)
        shutil.copytree(source_dir, 
                        destination_dir,
                        dirs_exist_ok=True, 
                        ignore=shutil.ignore_patterns(*try_ignore))
        print(f"Directory '{source_dir}' successfully copied to '{destination_dir}'")
    except FileExistsError:
        print(f"Error: Destination directory '{destination_dir}' already exists.")
    except Exception as e:
        print(f"Error: {e}")


def backup_from_sync():
    resource_check(False)
    destination_dir = config.get("ExternalSyncDir", None)
    if not config.get("PerformExternalSync", False) or not destination_dir:
        messagebox.warning("Unable to sync", "Sync directory does not exist, or was not specified, unable to use as backup")
    safe_copy_dir(source_dir = destination_dir, destination_dir = config["ResourceDirectory"], relative_ignore = ["settings.json"])

def set_external_sync():
    directory_path = filedialog.askdirectory()
    if directory_path:
        settings = safe_json_load(config["SettingsFile"])
        settings["ExternalSyncDir"] = directory_path
        config["PerformExternalSync"] = True
        config["ExternalSyncDir"] = directory_path
        safe_json_store(config["SettingsFile"], settings)
        resource_check(False)

def external_sync(force = False):
    if force:
        resource_check(False)
    if not config.get("PerformExternalSync", False):
        return
    destination_dir = config.get("ExternalSyncDir", None)
    if not destination_dir:
        return
    safe_copy_dir(config["ResourceDirectory"], destination_dir, relative_ignore = ["settings.json"]) 

def external_sync_data_points():
    if not config.get("PerformExternalSync", False):
        return
    destination_dir = config.get("ExternalSyncDir", None)
    if not destination_dir:
        return
    destination_file = os.path.join(destination_dir, "data_points.json")
    source_file = config["SavePointsFile"]
    safe_copy_file(source_file, destination_file)

def external_sync_images():
    if not config.get("PerformExternalSync", False):
        return
    destination_dir = config.get("ExternalSyncDir", None)
    if not destination_dir:
        return
    destination_img_dir = os.path.join(destination_dir, "images")
    source_dir = config["ImagesDirectory"]
    safe_copy_dir(source_dir, destination_img_dir)
    safe_copy_file(config["ImageListsFile"], os.path.join(destination_dir, "images.json"))


def get_data_points():
    return safe_json_load(config["SavePointsFile"])

def save_data_points(data):
    safe_json_store(config["SavePointsFile"], data)
    external_sync_data_points()

def load_image_paths():
    imgs = safe_json_load(config["ImageListsFile"])
    if imgs == {}:
        return []
    return imgs

# Copies the image into the 
def add_image(source_image_path : str):
    img_name = Path(source_image_path).name
    dest_image_path = os.path.join(config["ImagesDirectory"], img_name)
    images = load_image_paths()
    if img_name not in images:
        try:
            shutil.copy(source_image_path, dest_image_path)
            images.append(img_name)
            print("appending to image lists file")
            safe_json_store(config["ImageListsFile"], images)
            external_sync_images()
            return dest_image_path
        except FileNotFoundError:
            print(f"Error: Source file '{source_image_path}' not found.")
            return None
        except IsADirectoryError:
            print(f"Error: Destination is a directory, but expected a file path for shutil.copyfile(). Use shutil.copy() instead.")
            return None
        except PermissionError:
            print("Error: Permission denied.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    return None

# This takes a single image name, and return's its path
def get_image_path(img_name : str):
    directory = config["ImagesDirectory"]
    imgs = os.listdir(directory)
    for img in imgs:
        if Path(img).stem == img_name:
            return os.path.join(directory, img)
    return None

# The point of this function is to make sure all the resources and everything is set
# Before accidentally changing any data
def resource_check(do_backup_sync=True):
    for file in load_image_paths():
        im_name = Path(file).stem
        im_path = get_image_path(im_name)
        if im_path is None or not os.path.exists(im_path):
            messagebox.showwarning("Image Not Found", f"The image {file} does not exist! Please put that image into the resources/images directory manually")
        assert im_path and os.path.exists(im_path), f"Error image file path {file} does not exist, exiting before important data over written"
    data_points = get_data_points()
    # keys = list(data_points.keys())
    # for key in keys:
    #     assert key in config["ImagePaths"], f"Error expexted the image {key} to be a current valid image path"
    save = False
    for file in load_image_paths():
        im_name = Path(file).stem
        if im_name not in data_points.keys():
            data_points[file] = {}
            save = True
    if save:
        save_data_points(data_points)

    # Checking for external sync
    settings = safe_json_load(config["SettingsFile"])
    config["StartupBackupSync"] = False
    sync_dir = settings.get("ExternalSyncDir", None)
    sync_from_backup_on_start = settings.get("StartupBackupSync", False)
    if not sync_dir or not os.path.exists(sync_dir):
        messagebox.showwarning("No External Sync Directory", 
                               "While it is not required, it is reccomended to setup an external sync directory")
        config["PerformExternalSync"] = False
        return
    
    config["ExternalSyncDir"] = sync_dir
    config["PerformExternalSync"] = True
    config["StartupBackupSync"] = sync_from_backup_on_start
    if sync_from_backup_on_start and do_backup_sync:
        backup_from_sync()



