import os
import csv
from shutil import rmtree, move
import xml.etree.ElementTree as ET
from ifstools import IFS
import cloud_tools


def find_cloud_appeal_ifs(cloud_directory: str) -> list:
    found = []
    i = 0
    while True:
        i += 1
        directory = "data/graphics/psd_card_{:02d}.ifs".format(i)
        ob_path = cloud_tools.obfuscate(directory)
        if not os.path.isfile(os.path.join(cloud_directory, ob_path)):
            break
        found.append(directory)
    return found


def parse_appeal_file(appeal_file: str) -> list:
    cards = []
    
    with open(appeal_file   , "r") as f:
        data = ET.fromstring(f.read())

    for child in data:
        cards.append([
            int(child.attrib["id"]),
            child[0].find("texture").text
        ])
    
    return cards


def find_game_appeal_cards(game_directory: str) -> list:
    """Finds all current appeal cards in the game directory"""
    appeal_file = os.path.join(game_directory, "data", "others", "appeal_card.xml")
   
    if not os.path.isfile(appeal_file):
        raise FileNotFoundError("Appeal card file not found for game")

    return parse_appeal_file(appeal_file)


def create_appeal_xml(last_card_id: int, new_cards: list, mod_path: str):
    card_data = {}

    with open("appeal.csv", "r") as f:
        for x in csv.reader(f, delimiter=","):
            for card in new_cards:
                if card.rpartition(".")[0] in x:
                    card_data[x[0]] = x[1:]

    root = ET.Element("appeal_card_data")

    for card in new_cards:
        last_card_id += 1
        
        card_e = ET.SubElement(root, "card")
        card_e.set("id", str(last_card_id))

        info = ET.SubElement(card_e, "info")

        def create_element(name: str, value: str, attrib={}):
            i = ET.SubElement(info, name, attrib)
            i.text = value

        data = card_data[card.rpartition(".")[0]]
        create_element("texture", card.rpartition(".")[0])
        create_element("title", data[1])
        create_element("message_a", data[2].replace("\n", "[br:0]"))
        create_element("message_b", data[3].replace("\n", "[br:0]"))
        create_element("message_c", data[4].replace("\n", "[br:0]"))
        create_element("message_d", data[5].replace("\n", "[br:0]"))
        create_element("message_e", data[6].replace("\n", "[br:0]"))
        create_element("message_f", data[7].replace("\n", "[br:0]"))
        create_element("message_g", data[8].replace("\n", "[br:0]"))
        create_element("message_h", data[9].replace("\n", "[br:0]"))
        create_element("illustrator", "SOUND VOLTEX Designers")
        create_element("distribution_date", "2" + data[10][1:], {"__type": "u32"})
        create_element("rarity", data[11], {"__type": "u8"})
        create_element("generator_no", data[12], {"__type": "u8"})
        create_element("is_default", "1", {"__type": "u8"})
        create_element("sort_no", data[15], {"__type": "u16"})
        create_element("genre", "0", {"__type": "u8"})

    if not os.path.exists(os.path.join(mod_path, "others")):
        os.mkdir(os.path.join(mod_path, "others"))

    tree = ET.ElementTree(root)
    appeal_file_new = os.path.join(mod_path, "others", "appeal_card.merged.xml")
    with open(appeal_file_new, "wb") as f:
        tree.write(f, encoding="shift-jis")


def generate_appeal_cards(cloud_directory: str, game_directory: str):
    """Checks what exists and generate them"""
    cloud_appeal_ifs = find_cloud_appeal_ifs(cloud_directory)
    game_appeal_cards = find_game_appeal_cards(game_directory)
    mod_path = os.path.join(game_directory, "data_mods", "eac_appeal")

    # Recreate mod folder
    if os.path.exists(mod_path):
        rmtree(mod_path)
    os.mkdir(mod_path)

    # Get the last ifs in game
    last_ifs_n = 0
    for x in os.listdir(os.path.join(game_directory, "data", "graphics")):
        if x.startswith("s_psd_card_"):
            ifs_n = int(x.rpartition("_")[2].rpartition(".")[0])
            if ifs_n > last_ifs_n:
                last_ifs_n = ifs_n

    game_names = [x[1] for x in game_appeal_cards]
    new_cards = []

    # Extract cloud appeal cards and add if needed
    for appeal_ifs in cloud_appeal_ifs:
        print("Checking cloud {}".format(appeal_ifs))

        # Decrypt and extract cloud folder
        file_name = "cloud_" + appeal_ifs.rpartition("/")[2]
        with open(file_name, "wb") as f:
            f.write(cloud_tools.decrypt_file(cloud_directory, appeal_ifs))
        
        # Extract IFS
        ifs = IFS(file_name)
        ifs.extract(progress=False, recurse=False, tex_only=True)
        ifs.close()

        # Delete ifs file
        os.remove(file_name)

        folder_name = file_name.rpartition(".")[0] + "_ifs"

        for card_name in os.listdir(folder_name):
            if card_name.rpartition(".")[0] not in game_names:
                print("Found new file {}".format(card_name))
                new_cards.append(card_name)

                # Move image file
                ifs_folder = os.path.join(mod_path, "graphics", "s_psd_card_{:02d}_ifs".format(last_ifs_n))
                if not os.path.exists(ifs_folder):
                    os.makedirs(ifs_folder)

                move(os.path.join(folder_name, card_name), os.path.join(ifs_folder, card_name))

    # Write appeal to file, decrypted
    with open("appeal.csv", "wb") as f:
        f.write(cloud_tools.decrypt_file(cloud_directory, "data/others/appealmessage.csv"))

    # Create xml
    print("Creating merged xml")
    create_appeal_xml(
        game_appeal_cards[-1][0], 
        new_cards, 
        mod_path
    )

    os.remove("appeal.csv")

    # Delete cache
    cache_folder = os.path.join(game_directory, "data_mods", "_cache")
    if os.path.exists(cache_folder):
        print("Deleting cache")
        rmtree(cache_folder)

    # Cleanup
    for file in cloud_appeal_ifs:
        rmtree("cloud_" + file.rpartition("/")[2].rpartition(".")[0] + "_ifs")


if __name__ == "__main__":
    GAME_PATH = "E:/KFC/contents"
    CLOUD_PATH = "X:/Games/eac"

    if not os.path.exists(GAME_PATH):
        raise FileExistsError("Game path does not exist")
    if not os.path.exists(CLOUD_PATH):
        raise FileExistsError("Cloud path does not exist")

    generate_appeal_cards(CLOUD_PATH, GAME_PATH)
