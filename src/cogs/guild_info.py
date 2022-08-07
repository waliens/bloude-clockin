


import select
from discord import ApplicationContext, Bot, Embed, Emoji, Guild, Interaction, InvalidArgument, Option, Role, SlashCommandGroup, guild_only, slash_command
from discord.ext import commands
from sqlalchemy import update
from db_util.charter import get_guild_charter
from models import GuildCharter, GuildCharterField

from ui.guild_info import GuildCharterEmbed
from ui.util import EmbedFieldEditorModal


class GuildInfoCog(commands.Cog):
  def __init__(self, bot):
      self.bot = bot

  charter_group = SlashCommandGroup("charter", "Display, update and sign tracking of a guild charter.")
  charter_section_group = charter_group.create_subgroup("section", "To handle creation, update and deletion of command groups.")

  @charter_group.command(description="Charte de guilde")
  @guild_only()
  async def show(self, ctx, 
    section: Option(int, description="A section number of the charter") = None, 
    public: Option(bool, description="To show the bot response and the charter publicly") = False
  ):
    try:
      guild_id = str(ctx.guild.id)
      if public and not ctx.author.guild_permissions.administrator:
        raise InvalidArgument("cannot display charter without admin role")

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          charter = await get_guild_charter(sess, guild_id)
          embed = GuildCharterEmbed(charter, section=section)
          await ctx.respond(embed=embed, ephemeral=not public)
    except InvalidArgument as e:
      await ctx.respond(f"Cannot display rules: {str(e)}")

  @charter_group.command(description="Publish the charter and enable sign tracking.")
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def publish(self, ctx: ApplicationContext,
    sign_emoji: Option(str, description="The reaction emoji for signing the charter."),
    sign_role: Option(Role, description="The role assigned to people who sign the charter")
  ):
    guild_id = str(ctx.guild.id)
    async with self.bot.db_session_class() as sess:
      async with sess.begin():
        charter = await get_guild_charter(sess, guild_id)
        charter.sign_emoji = sign_emoji
        charter.id_sign_role = str(sign_role.id)
        charter.id_sign_channel = str(ctx.channel_id)
        embed = GuildCharterEmbed(charter, sign_info=True)
        interaction = await ctx.send(embed=embed)
        charter.id_sign_message = str(interaction.id)
        sess.add(charter)
        await sess.commit()
        

  @charter_section_group.command(description="edit a section of the charter")
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def update(self, ctx,
    section: Option(int, description="The number of the section to update") = None,
    title: Option(str, description="Specify to update the title of the charter") = None
  ):
    try:
      guild_id = str(ctx.guild.id)
      if title is None and section is None:
        raise InvalidArgument("nothing to update, specify either title or section")
      if title is not None and not 0 < len(title) <= 256:
        raise InvalidArgument("title is too short/long")

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          charter = await get_guild_charter(sess, guild_id)
          if title is not None:
            charter.title = title
            await sess.commit()

          if section is None:
            await ctx.respond("Title updated.")
            return 

          if not charter.has_section(section):
            raise InvalidArgument("no such section")
          section = charter.get_section(section)

          async def submit_callback(interaction: Interaction, title: str, content: str):
            if title is None or content is None or not 0 < len(title) <= 256 or not 0 < len(content) <= 1000:
              raise InvalidArgument("invalid title or content")
            async with self.bot.db_session_class() as clbk_sess:
              async with clbk_sess.begin():
                query = update(GuildCharterField).where(
                  GuildCharterField.id_guild == guild_id, 
                  GuildCharterField.number == section.number
                ).values(title=title, content=content)
                await clbk_sess.execute(query)
                await interaction.response.send_message(content="Guild charter section updated.", ephemeral=True)

                # edit any existing published charter
                new_charter = await get_guild_charter(clbk_sess, guild_id)
                if new_charter.id_sign_message is None:
                  return
                channel = await self.bot.fetch_channel(new_charter.id_sign_channel)
                sign_message = await channel.fetch_message(new_charter.id_sign_message)
                await sign_message.edit(embed=GuildCharterEmbed(new_charter, sign_info=True))

          modal = EmbedFieldEditorModal(
            submit_callback,
            title=f"Section {(section.number)}", 
            title_field_value=section.title, 
            content_field_value=section.content
          )

          await ctx.send_modal(modal)
    except InvalidArgument as e:
      await ctx.respond(f"Cannot display rules: {str(e)}")

  @charter_group.command()
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def unsigned(self, ctx: ApplicationContext,
    with_role: Option(Role, description="Only list unsigned people also attributed with this role.") = None
  ):
    try:
      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          charter = await get_guild_charter(sess, str(ctx.guild.id))

          if charter.id_sign_message is None:
            raise InvalidArgument("no charter configured")
          
          sign_role = ctx.guild.get_role(int(charter.id_sign_role))
          
          signed_members = {m.id for m in sign_role.members}
          unsigned_members = list()
          for member in (ctx.guild.members if with_role is None else with_role.members):
            if member.id not in signed_members and not member.bot:
              unsigned_members.append(member)
          
          embed = Embed(title="Unsigned", description="\n".join([f"- <@{m.id}>" for m in unsigned_members]))
          await ctx.respond(embed=embed)

    except InvalidArgument as e:
      await ctx.respond(f"Cannot list unsigned: {str(e)}")




def setup(bot: Bot):
  bot.add_cog(GuildInfoCog(bot))