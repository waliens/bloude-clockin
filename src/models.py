from sqlalchemy import Column, JSON, Boolean, Integer, Date, DateTime, String, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class Character(Base):
  __tablename__ = "character"
  id = Column(Integer, primary_key=True)
  id_guild = Column(String(22), primary_key=True)
  id_user = Column(String(22))
  name = Column(String(255))
  is_main = Column(Boolean)
  created_at = Column(DateTime)

  __table_args__ = (
    UniqueConstraint('id_user', 'name', name='id_user_name_unique_constraint'),
  )


class Raid(Base):
  __tablename__ = "raid"
  id = Column(Integer, primary_key=True)
  name_en = Column(String(255), unique=True)
  name_fr = Column(String(255), unique=True)
  reset_period = Column(Integer)  # in days
  reset_start = Column(DateTime)  # date of the first reset (of the expansion)


class Attendance(Base):
  __tablename__ = "attendance"
  id_guild = Column(String(22), primary_key=True)
  id_character = Column(Integer, ForeignKey('character.id', ondelete="CASCADE"), primary_key=True)
  id_raid = Column(Integer, ForeignKey('raid.id', ondelete="CASCADE"), primary_key=True)
  created_at = Column(DateTime)
  raid_date = Column(Date)
  cancelled = Column(Boolean)  # if user cancelled his attendance post-registration (on a raid helper for instance)
  
  character = relationship("Character", lazy="joined")
  raid = relationship("Raid", lazy="joined")


class Item(Base):
  __tablename__ = "item"
  id = Column(Integer, primary_key=True)
  name_en = Column(String(255), unique=True)
  name_fr = Column(String(255), unique=True)
  metadata_ = Column("metadata", JSON)


class Loot(Base):
  __tablename__ = "loot"
  id_guild = Column(String(22), primary_key=True)
  id_character = Column(Integer, ForeignKey("character.id", ondelete="CASCADE"), primary_key=True)
  id_item = Column(Integer, ForeignKey("item.id", ondelete="CASCADE"), primary_key=True)
  created_at = Column(DateTime)

  character = relationship("Character", lazy="joined")
  item = relationship("Item", lazy="joined")