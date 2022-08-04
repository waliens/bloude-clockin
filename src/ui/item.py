import logging
from discord import Embed, Interaction, InvalidArgument
from discord.ui import View, Button

from db_util.item import register_loot

class ItemListEmbed(Embed):
  def __init__(self, items, *args, max_items=-1, **kwargs):
    if max_items > 0:
      self._items = items[:max_items]
    else: 
      self._items = items
    description = "\n".join([f"`{i+1}` {item.name}" for i, item in enumerate(self._items)])
    if max_items > 0 and len(items) > max_items:
      description = f"Too many items, only displaying {max_items}.\n\n" + description
    super().__init__(
      *args,
      description=description,
      **kwargs)


class LootSelectionButton(Button):
  def __init__(self, bot, item_nb, item_id, character_id, *args, **kwargs):
    super().__init__(*args, label=f"{item_nb}", **kwargs)
    self._bot = bot
    self._item_id = item_id
    self._character_id = character_id

  async def callback(self, interaction: Interaction):
    try:
      self.view.disable_all_items()
      async with self._bot.db_session() as sess:
        async with sess.begin():
          await register_loot(sess, self._item_id, self._character_id)
      self.view.stop()
      self.view.clear_items()
      await interaction.response.send_message(f"Loot registered.", ephemeral=True, view=self.view)
    except InvalidArgument as e:
      self.view.enable_all_items()
      return await interaction.response.send_message(f"Cannot register the loot: {str(e)}.", ephemeral=True)


class LootListSelectorView(View):
  def __init__(self, bot, items, character_id, *args, max_items=-1, **kwargs):
    super().__init__(*args, **kwargs)
    self._bot = bot
    self._character_id = character_id
    if max_items > 0:
      self._items = items[:max_items]
    else: 
      self._items = items

    self._buttons = [
      LootSelectionButton(self._bot, i+1, item.id, self._character_id) 
      for i, item in enumerate(self._items)
    ]

    for button in self._buttons:
      self.add_item(button)


    