import os
import cloud_tools


def find_cloud_appeal_ifs(cloud_directory: str) -> list:
    found = []
    i = 0
    while True:
        i += 1
        directory = os.path.join(cloud_directory, "data", "graphics", "psd_card_{:02d}.ifs".format(i))
        if not os.path.exists(cloud_tools.obfuscate(directory)):
            break
        found.append(directory)
    return found


def generate_appeal_cards(cloud_directory: str, game_directory: str):
    """Checks what exists and generate them"""
    cloud_appeal_ifs = find_cloud_appeal_ifs(cloud_directory)
    print(cloud_appeal_ifs)


if __name__ == "__main__":
    GAME_PATH = "E:/KFC/contents"
    CLOUD_PATH = "X:/Games/eac"

    if not os.path.exists(GAME_PATH):
        raise FileExistsError("Game path does not exist")
    if not os.path.exists(CLOUD_PATH):
        raise FileExistsError("Cloud path does not exist")

    generate_appeal_cards(CLOUD_PATH, GAME_PATH)
