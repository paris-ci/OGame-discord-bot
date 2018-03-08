from discord.ext import commands


def is_ready():
    async def predicate(ctx):
        await ctx.bot.wait_until_ready()
        return True

    return commands.check(predicate)


class NotSuperAdmin(commands.CheckFailure):
    pass


def is_super_admin():
    async def predicate(ctx):
        #await ctx.bot.wait_until_ready()
        cond = ctx.message.author.id in ctx.bot.admins
        ctx.logger.debug(f"Check for super-admin returned {cond}")
        if cond:
            return True
        else:
            raise NotSuperAdmin

    return commands.check(predicate)


class NotServerAdmin(commands.CheckFailure):
    pass


def is_server_admin():
    async def predicate(ctx):
        #await ctx.bot.wait_until_ready()
        cond = ctx.message.author.id in ctx.bot.admins  # User is super admin
        cond = cond or ctx.message.channel.permissions_for(ctx.message.author).administrator  # User have server administrator permission
        ctx.logger.debug(f"Check for admin returned {cond}")

        if cond:
            return True
        else:
            raise NotServerAdmin

    return commands.check(predicate)
