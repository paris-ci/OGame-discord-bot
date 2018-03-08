import urllib.request

import os
import errno

import time
from lxml import etree

HOUR = 3600
DAY = 24 * HOUR
WEEK = 7 * DAY

positions_names = {0: "Total", 1: "Economie", 2: "Recherche", 3: "Militaire", 4: "Militaire (pertes)", 5: "Militaire (construit)", 6: "Militaire (détruit)", 7: "Honneur", }

cache_time = {"players.xml": DAY,
              "universe.xml": WEEK,
              "playerData.xml": WEEK,
              "highscore.xml?category=1&type=0": HOUR,
              "highscore.xml?category=1&type=1": HOUR,
              "highscore.xml?category=1&type=2": HOUR,
              "highscore.xml?category=1&type=3": HOUR,
              "highscore.xml?category=1&type=4": HOUR,
              "highscore.xml?category=1&type=5": HOUR,
              "highscore.xml?category=1&type=6": HOUR,
              "highscore.xml?category=1&type=7": HOUR,
              "alliances.xml": DAY,
              "serverData.xml": DAY,
              "universes.xml": DAY}


class OGame_API():

    def __init__(self, bot):
        self.bot = bot
        self.cache = {}

    async def create_folder(self, folder):

        try:
            os.makedirs(folder)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    async def get_root(self, server_id, file):
        if server_id not in self.cache.keys():
            self.cache[server_id] = {}

        if file in self.cache[server_id].keys():
            self.bot.logger.debug(f"Got {file} for {server_id} from cache")
            if int(self.cache[server_id][file].attrib["timestamp"]) + cache_time.get(file, WEEK) < time.time():
                self.bot.logger.info(f"Le fichier {file} mis en cache à expiré. Re-téléchargement")
                await self.update(server_id, file)
            else:
                self.bot.logger.debug(f"Le fichier {file} est à jour.")

        else:
            self.bot.logger.debug(f"Cache miss for {file} for {server_id}")
            await self.update(server_id, file)

        return self.cache[server_id][file]

    async def update(self, server_id, file):
        """
        https://board.fr.ogame.gameforge.com/index.php/Thread/619580-Ogame-API/

        :param server_id:
        :return:
        """

        base_url = f"https://s{server_id}-fr.ogame.gameforge.com/api/"
        folder = f"cache/{server_id}/"

        await self.create_folder(folder)

        url = base_url + file
        place = folder + file
        self.bot.logger.info(f"Downloading {url} into {place}")
        urllib.request.urlretrieve(url, place)

        tree = etree.parse(place)
        root = tree.getroot()
        self.cache[server_id][file] = root

    async def get_player_dict_from_name(self, server_id, player_name) -> dict:
        root = await self.get_root(server_id=server_id, file="players.xml")
        players = root.xpath(f"//player[@name='{player_name}']")

        try:
            return await self.get_player_dict_from_id(server_id, players[0].attrib["id"])
        except IndexError:
            return None

    async def get_player_dict_from_id(self, server_id, player_id) -> dict:
        root = await self.get_root(server_id=server_id, file=f"playerData.xml?id={player_id}")

        player_parsed = {"positions": [], "planets": [], "alliance": {"name": "Aucune", "tag": "NULL", "id": 000000}}
        player_parsed.update(dict(root.attrib))

        #positions = root.xpath("//positions")

        #for position in positions[0]:
        #    position_parsed = dict(position.attrib)
        #    position_parsed["type"] = int(position_parsed["type"])
        #    position_parsed["position"] = position.text
        #    position_parsed["name"] = positions_names[position_parsed["type"]]
        #    player_parsed["positions"].append(position_parsed)

        player_parsed["positions"] = await self.get_player_positions(server_id, player_id)

        planets = root.xpath("//planets")

        for planet in planets[0]:
            planet_dict = dict(planet.attrib)
            planet_dict["moons"] = []
            for moon in planet:
                planet_dict["moons"].append(dict(moon.attrib))

            player_parsed["planets"].append(planet_dict)

        try:
            alliance = root.xpath("//alliance")[0]
            player_parsed["alliance"]["id"] = int(alliance.attrib['id'])
            player_parsed["alliance"]["name"] = alliance.findtext('name', default='Aucune')
            player_parsed["alliance"]["tag"] = alliance.findtext('tag', default='NULL')
        except IndexError:
            pass

        return player_parsed

    async def get_player_positions(self, server_id, player_id):
        positions = []
        for i in range(8): # 7 positions to get
            root = await self.get_root(server_id, f"highscore.xml?category=1&type={i}")
            player = root.xpath(f"//player[@id={player_id}]")[0]
            position = dict(player.attrib)
            position["name"] = positions_names[i]
            position["type"] = i
            positions.append(position)

        return positions


    async def get_alliance_dict_from_id(self, server_id, alliance_id) -> dict:
        root = await self.get_root(server_id=server_id, file="alliances.xml")
        alliance = root.xpath(f"//alliance[@id='{alliance_id}']")

        alliance_parsed = dict(alliance[0].attrib)

        alliance_parsed["members"] = []

        for player in alliance[0]:
            alliance_parsed["members"].append(player.attrib["id"])

        return alliance_parsed

    async def get_alliance_dict_from_name(self, server_id, alliance_name) -> dict:
        root = await self.get_root(server_id=server_id, file="alliances.xml")
        alliance = root.xpath(f"//alliance[@name='{alliance_name}']")

        return await self.get_alliance_dict_from_id(server_id, alliance[0].attrib["id"])
