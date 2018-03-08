import datetime
import urllib.request

import discord
from discord.ext import commands
import os
import errno


class General():
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def update(self, ctx, server_id: int = 150):
        """
        https://board.fr.ogame.gameforge.com/index.php/Thread/619580-Ogame-API/

        :param server_id:
        :return:
        """

        await self.bot.ogame_API.update(server_id)
        await self.bot.send_message(ctx=ctx, message=":ok_hand:")

    @commands.command()
    async def player_info(self, ctx, player, server_id: int = 150):
        p = await self.bot.ogame_API.get_player_dict_from_name(server_id, player)

        if not p:
            await self.bot.send_message(ctx=ctx, message="Le joueur est introuvable")
            return


        e = discord.Embed()
        e.title = f"Informations sur {player}"
        e.set_footer(text=f"Requested by {ctx.author.name}#{ctx.author.discriminator}")

        e.add_field(name="Alliance", value=f"{p['alliance']['name']} ({p['alliance']['tag']})")
        e.add_field(name="ID", value=p["id"])

        await self.bot.send_message(ctx=ctx, embed=e)


        e = discord.Embed()
        e.title = f"Scores de {player}"
        e.set_footer(text=f"Requested by {ctx.author.name}#{ctx.author.discriminator}")

        # player_parsed = {"positions" : [], "planets": [], "alliance": {"name" : "Aucune", "tag": "NULL", "id": 000000}}

        for position in p["positions"]:
            e.add_field(name=position["name"], value=f"{position['score']} @ {position['position']}")

        await self.bot.send_message(ctx=ctx, mention=False, embed=e)


        e = discord.Embed()
        e.title = f"Planetes de {player}"
        e.set_footer(text=f"Requested by {ctx.author.name}#{ctx.author.discriminator}")


        for planet in p["planets"]:
            pstr = f"[{planet['coords']}]"
            if len(planet["moons"]) >= 1:
                for moon in planet["moons"]:
                    pstr += f"\n🌝: {moon['name']}"
            e.add_field(name=planet["name"], value=pstr)

        await self.bot.send_message(ctx=ctx, mention=False, embed=e)



    @commands.command()
    async def alliance_info(self, ctx, alliance_name, server_id: int = 150):
        a = await self.bot.ogame_API.get_alliance_dict_from_name(server_id, alliance_name)

        e = discord.Embed()  # .from_data({"Title": "Info sur un joueur", "fields" : p})
        e.title = f"Informations sur l'alliance {alliance_name}"
        e.set_footer(text=f"Requested by {ctx.author.name}#{ctx.author.discriminator}")

        for title, content in a.items():
            if title == "members":
                liste_joueurs = []

                for player in content:
                    p = await self.bot.ogame_API.get_player_dict_from_id(server_id, int(player))
                    if p["id"] == a["founder"]:
                        name = f"**{p['name']}**"
                    else:
                        name = p['name']

                    liste_joueurs.append(name)

                content = "\n".join(liste_joueurs)
            elif title == "founder":
                content = (await self.bot.ogame_API.get_player_dict_from_id(server_id, int(content)))["name"]
            elif title == "foundDate":
                content = datetime.datetime.fromtimestamp(
                    int(content)
                ).strftime('%Y-%m-%d %H:%M:%S')
            elif title == "open":
                content = bool(int(content))

            e.add_field(name=title, value=content)

        await self.bot.send_message(ctx=ctx, embed=e)


def setup(bot):
    bot.add_cog(General(bot))
