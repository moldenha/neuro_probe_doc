import os
script_path = os.path.abspath(__file__)
script_directory = os.path.dirname(script_path)
parent_directory = os.path.dirname(script_directory)
resource_directory = os.path.join(parent_directory, "resources")

config = {
        "ResourceDirectory"  : resource_directory,
        "SavePointsFile"     : os.path.join(resource_directory, "data_points.json"),
        "ImageListsFile"     : os.path.join(resource_directory, "images.json"),
        "ImagesDirectory"    : os.path.join(resource_directory, "images"),
        "ZoomOutImg"         : os.path.join(resource_directory, "zoom_out.png"),
        "ZoomInImg"          : os.path.join(resource_directory, "zoom_in.png"),
        "SettingsFile"       : os.path.join(resource_directory, "settings.json")
}

if __name__ == '__main__':
    print(script_path)
    print(script_directory)
    print(parent_directory)
    print(resource_directory)
    print(config)
