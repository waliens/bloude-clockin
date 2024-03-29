
from discord import ApplicationContext, Bot, Embed,Interaction, InvalidArgument, Member, Option, Role, SlashCommandGroup, guild_only
from discord.ext import commands
from sqlalchemy import update
from db_util.charter import get_guild_charter
from models import GuildCharter, GuildCharterField

from ui.guild_info import GuildCharterEmbed
from ui.util import EmbedFieldEditorModal

from pycord18n.extension import _ as _t


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
        raise InvalidArgument(_t("general.invalid.adminrequired"))

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          charter = await get_guild_charter(sess, guild_id)
          embed = GuildCharterEmbed(charter, section=section)
          await ctx.respond(embed=embed, ephemeral=not public)
    except InvalidArgument as e:
      await ctx.respond(_t("charter.show.error", error=str(e)), ephemeral=True)

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
        interaction = await ctx.respond(embed=embed, ephemeral=False)
        response = await interaction.original_response()
        charter.id_sign_message = str(response.id)
        sess.add(charter)
        await sess.commit()
        
  @charter_group.command(description="Edit charter title. Creates the charter if it does not exist.")
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def edit(self, ctx: ApplicationContext,
    title: Option(str, description="The charter title")
  ):
    try:
      if len(title) == 0:
        raise InvalidArgument(_t("charter.invalid.titleempty"))

      guild_id = str(ctx.guild.id)
      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          charter = await sess.get(GuildCharter, guild_id)
          if charter is None:
            charter = GuildCharter(
              id_guild=guild_id, 
              title=None, 
              id_sign_message=None, 
              id_sign_channel=None, 
              sign_emoji=None, 
              id_sign_role=None
            )
            sess.add(charter)
          charter.title = title
          await sess.commit()
          await ctx.respond(_t("charter.edit.success"), ephemeral=True)
          await self._update_published_charter(sess, guild_id, charter=charter)
    except InvalidArgument as e:
      await ctx.respond(_t("charter.edit.error", error=str(e)), ephemeral=True)

  @charter_section_group.command(description="Edit a section of the charter")
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def update(self, ctx,
    section: Option(int, description="The number of the section to update")
  ):
    try:
      guild_id = str(ctx.guild.id)

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          charter = await get_guild_charter(sess, guild_id)

          if not charter.has_section(section):
            raise InvalidArgument(_t("charter.section.invalid.unknown"))
          section = charter.get_section(section)

          async def submit_callback(interaction: Interaction, title: str, content: str):
            if len(content) > GuildCharterField.CONTENT_MAX_SIZE:
              raise InvalidArgument(_t("charter.section.invalid.contenttoolong", count=GuildCharterField.CONTENT_MAX_SIZE))
            if len(title) > GuildCharterField.TITLE_MAX_SIZE:
              raise InvalidArgument(_t("charter.section.invalid.titletoolong", count=GuildCharterField.TITLE_MAX_SIZE))
            
            async with self.bot.db_session_class() as clbk_sess:
              async with clbk_sess.begin():
                query = update(GuildCharterField).where(
                  GuildCharterField.id_guild == guild_id, 
                  GuildCharterField.number == section.number
                ).values(title=title, content=content)
                await clbk_sess.execute(query)
                await interaction.response.send_message(content=_t("charter.section.update.success"), ephemeral=True)
                await self._update_published_charter(clbk_sess, guild_id)


          modal = EmbedFieldEditorModal(
            submit_callback,
            title=_t("charter.section.modal.title", number=section.number), 
            title_field_value=section.title, 
            max_title_size=GuildCharterField.TITLE_MAX_SIZE - 4,  # for section number
            content_field_value=section.content,
            max_content_size=GuildCharterField.CONTENT_MAX_SIZE
          )

          await ctx.send_modal(modal)
    except InvalidArgument as e:
      await ctx.respond(_t("charter.section.update.error", error=str(e)), ephemeral=True)
    
  @charter_section_group.command(description="Create a charter section. Create charter if it does not exist.")
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def create(self, ctx,
    number: Option(int, description="Section number. All existing sections with number higher or equal are moved one number up.") = None
  ):
    try:
      guild_id = str(ctx.guild.id)

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          # create charter if necessary
          charter = await sess.get(GuildCharter, guild_id)
          if charter is None:
            charter = GuildCharter(title=_t("charter.default.title"), id_guild=guild_id)
            sess.add(charter)
            await sess.commit()

          if number is not None and not 1 <= number <= len(charter.fields) + 1:
            raise InvalidArgument(_t("charter.section.invalid.number"))
          
          if number is None:
            number = len(charter.fields) + 1

          # post edit modal for user
          async def submit_callback(interaction: Interaction, title: str, content: str):
            if len(content) > GuildCharterField.CONTENT_MAX_SIZE:
              raise InvalidArgument(_t("charter.section.invalid.contenttoolong", count=GuildCharterField.CONTENT_MAX_SIZE))
            if len(title) > GuildCharterField.TITLE_MAX_SIZE:
              raise InvalidArgument(_t("charter.section.invalid.titletoolong", count=GuildCharterField.TITLE_MAX_SIZE))

            async with self.bot.db_session_class() as clbk_sess:
              async with clbk_sess.begin():
                updated_charter = await get_guild_charter(clbk_sess, guild_id)
          
                for field in updated_charter.fields:
                  if field.number >= number:
                    field.number += 1  
                          
                updated_charter.fields.append(GuildCharterField(number=number, title=title, content=content))

                await clbk_sess.commit()
                await interaction.response.send_message(content=_t("charter.section.create.success"), ephemeral=True)
                await self._update_published_charter(clbk_sess, guild_id, charter=updated_charter)


          modal = EmbedFieldEditorModal(
            submit_callback,
            title=_t("charter.section.modal.title", number=number), 
            title_field_value="", 
            max_title_size=GuildCharterField.TITLE_MAX_SIZE - 4, # for section number
            content_field_value=""
          )

          await ctx.send_modal(modal)
    except InvalidArgument as e:
      await ctx.respond(_t("charter.section.create.error", error=str(e)), ephemeral=True)

  @charter_section_group.command(description="Deletes a section of the charter")
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def delete(self, ctx, 
    number: Option(int, description="Section number")
  ):
    try:
      guild_id = str(ctx.guild.id)
      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          charter = await get_guild_charter(sess, guild_id)

          if not 1 <= number <= len(charter.fields):
            raise InvalidArgument(_t("charter.section.invalid.number"))

          charter.fields = sorted(charter.fields, key=lambda f: f.number)
          del charter.fields[number - 1]
          await sess.flush()
          
          for field in charter.fields:
            if field.number > number:
              field.number -= 1

          await sess.commit()
          await ctx.respond(_t("charter.section.delete.success"), ephemeral=True)
          await self._update_published_charter(sess, guild_id, charter=charter)  
    except InvalidArgument as e:
      await ctx.respond(_t("charter.section.delete.error", error=str(e)), ephemeral=True)

  async def _update_published_charter(self, session, guild_id, charter=None):
    # edit any existing published charter
    if charter is None:
      charter = await get_guild_charter(session, guild_id)
    if charter.id_sign_message is None:
      return
    channel = await self.bot.fetch_channel(charter.id_sign_channel)
    sign_message = await channel.fetch_message(charter.id_sign_message)
    await sign_message.edit(embed=GuildCharterEmbed(charter, sign_info=True))
  
  @charter_group.command()
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def unsigned(self, ctx: ApplicationContext,
    with_role: Option(Role, description="Only list unsigned people also attributed with this role.") = None,
    public: Option(bool, description="To display the list of unsigned people publicly.") = False
  ):
    try:
      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          charter = await get_guild_charter(sess, str(ctx.guild.id))

          if charter.id_sign_message is None:
            raise InvalidArgument(_t("charter.invalid.none"))
          
          sign_role = ctx.guild.get_role(int(charter.id_sign_role))
          
          signed_members = {m.id for m in sign_role.members}
          unsigned_members = list()
          for member in (ctx.guild.members if with_role is None else with_role.members):
            if member.id not in signed_members and not member.bot:
              unsigned_members.append(member)
          
          description = "\n".join([f"- <@{m.id}>" for m in unsigned_members])
          if with_role is not None:
            description = _t("charter.unsigned.withrole", role_id=with_role.id) + "\n" + description
          
          embed = Embed(
            title=_t("charter.unsigned.title"), 
            description=description
          )
          await ctx.respond(embed=embed, ephemeral=not public)

    except InvalidArgument as e:
      await ctx.respond(_t("charter.unsigned.error", error=str(e)), ephemeral=True)



def setup(bot: Bot):
  bot.add_cog(GuildInfoCog(bot))