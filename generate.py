import os
import csv
from PIL import Image
from shutil import rmtree, copyfile
import xml.etree.ElementTree as ET
from ifstools import IFS
import cloud_tools


def parse_appeal_file(appeal_file: str) -> list:
    cards = []
    
    with open(appeal_file, "r") as f:
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
    """
    Create merged appeal xml
    :param last_card_id: id of the last card to add to
    :param new_cards: list of new cards to add
    :param mod_path: path of the mod
    :return:
    """
    # Read card data from eac appeal csv
    card_data = {}
    with open("appeal.csv", "r") as f:
        for x in csv.reader(f, delimiter=","):
            for card in new_cards:
                if card.rpartition(".")[0] in x:
                    card_data[x[0]] = x[1:]

    # Create xml and create data for new cards to merge with
    root = ET.Element("appeal_card_data")
    for card in new_cards:
        last_card_id += 1
        
        card_e = ET.SubElement(root, "card")
        card_e.set("id", str(last_card_id))

        info = ET.SubElement(card_e, "info")

        def create_element(name: str, value: str, attrib={}):
            i = ET.SubElement(info, name, attrib)
            i.text = value

        # Game uses [br:0] instead of \n.
        # Not sure if eac has illustrator data so left it as sdvx designers.
        # eac dist date megu weird not sure what the first character is, changed it to a full year (2020).
        # Set to default in case server does not have it on unlock.
        # Not sure what genres there are.
        # Dunno what rarity means, game version or rarity of the card
        # Sort no, also dunno, assume its the order which its sorted by
        # Generator number is prob then num when printed
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

    # Create others dir if not exists
    if not os.path.exists(os.path.join(mod_path, "others")):
        os.mkdir(os.path.join(mod_path, "others"))

    # Save merged xml to file
    tree = ET.ElementTree(root)
    appeal_file_new = os.path.join(mod_path, "others", "appeal_card.merged.xml")
    with open(appeal_file_new, "wb") as f:
        tree.write(f, encoding="shift-jis")


def generate_appeal_cards(cloud_directory: str, game_directory: str):
    """
    Generates mod files
    :param cloud_directory:
    :param game_directory:
    :return:
    """
    mod_path = os.path.join(game_directory, "data_mods", "eac_appeal")
    cloud_appeal_ifs = cloud_tools.find_appeal_ifs(cloud_directory)
    game_appeal_cards = find_game_appeal_cards(game_directory)

    # Recreate mod folder
    if os.path.exists(mod_path):
        rmtree(mod_path)
    os.makedirs(mod_path)

    # Find the last ifs number in game folder to append to
    last_ifs_n = 0
    for x in os.listdir(os.path.join(game_directory, "data", "graphics")):
        if x.startswith("s_psd_card_"):
            ifs_n = int(x.rpartition("_")[2].rpartition(".")[0])
            if ifs_n > last_ifs_n:
                last_ifs_n = ifs_n

    # Put all game appeal card names into a list
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

        # Check the eac folder for new cards
        for card_name in os.listdir(folder_name):
            if card_name.rpartition(".")[0] not in game_names:
                print("Found new file {}".format(card_name))
                new_cards.append(card_name)

                # Create ifs folder
                ifs_folder = os.path.join(mod_path, "graphics", "s_psd_card_{:02d}_ifs".format(last_ifs_n))
                if not os.path.exists(ifs_folder):
                    os.makedirs(ifs_folder)

                # Create ap_card folder
                apc_folder = os.path.join(mod_path, "graphics", "ap_card")
                if not os.path.exists(apc_folder):
                    os.makedirs(apc_folder)

                # Copy to ifs folder
                copyfile(os.path.join(folder_name, card_name), os.path.join(ifs_folder, card_name))

                # Resize in game appeal card to fit correctly otherwise the image is white, 150x192 32bit
                img = Image.open(os.path.join(folder_name, card_name))
                img = img.resize((150, 192), Image.ANTIALIAS)
                img.save(os.path.join(apc_folder, card_name))
                img.close()

        # Delete temp extracted folder
        rmtree(folder_name)

    # Decrypt appeal file to current dir
    with open("appeal.csv", "wb") as f:
        f.write(cloud_tools.decrypt_file(cloud_directory, "data/others/appealmessage.csv"))

    # Create xml at the mod dir
    print("Creating merged xml")
    create_appeal_xml(
        game_appeal_cards[-1][0], 
        new_cards, 
        mod_path
    )

    # Remove temp decrypted appeal file
    os.remove("appeal.csv")

    # Delete mod cache if exists
    cache_folder = os.path.join(game_directory, "data_mods", "_cache")
    if os.path.exists(cache_folder):
        print("Deleting cache")
        rmtree(cache_folder)


if __name__ == "__main__":
    # Change these to ur paths
    GAME_PATH = "E:/KFC/contents"
    CLOUD_PATH = "X:/Games/eac"

    if not os.path.exists(GAME_PATH):
        raise FileExistsError("Game path does not exist, please change in file")
    if not os.path.exists(CLOUD_PATH):
        raise FileExistsError("Cloud path does not exist, please change in file")

    # Generate mod files
    generate_appeal_cards(CLOUD_PATH, GAME_PATH)
