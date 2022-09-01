from unicodedata import name
import pytz
import datetime
from sqlalchemy import Column, JSON, Boolean, Enum, Integer, DateTime, String, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql


from db_util.wow_data import ProfessionEnum, RaidSizeEnum, RoleEnum, ClassEnum, SpecEnum

Base = declarative_base()


def utcnow():
  return datetime.datetime.now(tz=pytz.UTC).replace(tzinfo=None)


class GuildSettings(Base):
  __tablename__ = "guild_settings"
  DEFAULT_TZ = "utc"
  DEFAULT_LOCALE = "en"
  id_guild = Column(String(22), primary_key="True")
  locale = Column(String(32), default=DEFAULT_TZ)  # locale string
  timezone = Column(String(256), default=DEFAULT_LOCALE)  # timezone identifier
  cheer_message = Column(String(256), nullable=True, default=None)



class Character(Base):
  __tablename__ = "character"
  id = Column(Integer, primary_key=True)
  id_guild = Column(String(22))
  id_user = Column(String(22))
  name = Column(String(255))
  is_main = Column(Boolean)
  role = Column(Enum(RoleEnum))
  spec = Column(Enum(SpecEnum), nullable=True)
  character_class = Column(Enum(ClassEnum))
  created_at = Column(DateTime, default=utcnow)
  updated_at = Column(DateTime, onupdate=utcnow)

  __table_args__ = (
    UniqueConstraint('id_user', 'name', 'id_guild', name='id_guild_user_name_unique_constraint'),
  )


class Raid(Base):
  __tablename__ = "raid"
  id = Column(Integer, primary_key=True)
  name_en = Column(String(255), unique=True)
  name_fr = Column(String(255), unique=True)
  short_name = Column(String(255), unique=True)
  reset_period = Column(Integer)  # in days
  reset_start = Column(DateTime)  # date of the first reset (of the expansion)

  @property
  def name(self):
    return self.name_en

  @property
  def first_reset_end(self):
    return self.reset_start + datetime.timedelta(days=self.reset_period)


class Attendance(Base):
  __tablename__ = "attendance"
  id = Column(Integer, primary_key=True)
  id_character = Column(Integer, ForeignKey('character.id', ondelete="CASCADE"))
  id_raid = Column(Integer, ForeignKey('raid.id', ondelete="CASCADE"))
  created_at = Column(DateTime, default=utcnow)
  updated_at = Column(DateTime, onupdate=utcnow)
  raid_datetime = Column(DateTime)
  raid_size = Column(Enum(RaidSizeEnum))
  cancelled = Column(Boolean)  # if user cancelled his attendance post-registration (on a raid helper for instance)
  
  character = relationship("Character", lazy="joined")
  raid = relationship("Raid", lazy="joined")


class Item(Base):
  __tablename__ = "item"
  id = Column(Integer, primary_key=True)
  name_en = Column(String(255))
  name_fr = Column(String(255))
  metadata_ = Column("metadata", postgresql.JSON)

  @property
  def name(self):
    return self.name_en


class Recipe(Base):
  __tablename__ = "recipe"
  id = Column(Integer, primary_key=True)
  name_en = Column(String(255))
  name_fr = Column(String(255))
  metadata_ = Column("metadata", postgresql.JSON)
  profession = Column(Enum(ProfessionEnum))


class UserRecipe(Base):
  __tablename__ = "user_recipe"
  id_recipe = Column(Integer, ForeignKey('recipe.id', ondelete="CASCADE"), primary_key=True)
  id_character = Column(Integer, ForeignKey('character.id', ondelete="CASCADE"), primary_key=True)
  created_at = Column(DateTime, default=utcnow)

  character = relationship("Character", lazy="joined")
  recipe = relationship("Recipe", lazy="joined")


class Loot(Base):
  __tablename__ = "loot"
  id_character = Column(Integer, ForeignKey("character.id", ondelete="CASCADE"), primary_key=True)
  id_item = Column(Integer, ForeignKey("item.id", ondelete="CASCADE"), primary_key=True)
  count = Column(Integer, default=1)
  created_at = Column(DateTime, default=utcnow)
  updated_at = Column(DateTime, onupdate=utcnow)

  character = relationship("Character", lazy="joined")
  item = relationship("Item", lazy="joined") 


class GuildCharter(Base):
  __tablename__ = "guild_charter"

  TITLE_MAX_SIZE = 256 

  id_guild = Column(String(22), primary_key=True)
  title = Column(String(256), nullable=False)
  id_sign_channel = Column(String(22), nullable=True)
  id_sign_message = Column(String(22), nullable=True)
  id_sign_role = Column(String(22), nullable=True)
  sign_emoji = Column(String(128), nullable=True)

  fields = relationship("GuildCharterField", lazy="joined", back_populates="charter", cascade="all, delete-orphan")

  def get_section(self, number):
    filtered = [f for f in self.fields if f.number == number]
    return filtered[0]

  def has_section(self, number):
    return len([f for f in self.fields if f.number == number]) != 0


class GuildCharterField(Base):
  __tablename__ = "guild_charter_field"
  
  TITLE_MAX_SIZE = 256 
  CONTENT_MAX_SIZE = 1000  

  id_guild = Column(String(22), ForeignKey('guild_charter.id_guild', ondelete="CASCADE"), primary_key=True, )
  number = Column(Integer, primary_key=True)
  title = Column(String(256))
  content = Column(String(1000))
  
  charter = relationship("GuildCharter", back_populates="fields")
