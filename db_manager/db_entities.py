from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class ActivityCatalog(Base):
    __tablename__ = 'activity_catalog'
    __table_args__ = {
        'mysql_charset': 'utf8mb4'
    }
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256))
    description = Column(String(512))
    type = Column(String(50))
    status = Column(String(50))
    emoji = Column(String(10))
    last_chosen = Column(DateTime, default=None)

    def __repr__(self):
        return (f"<ActivityCatalog(id={self.id!r}, name={self.name!r}, description={self.description!r}, "
                f"type={self.type!r}, status={self.status!r}, emoji={self.emoji!r})>")


class Activity(Base):
    __tablename__ = 'activity'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)  # Assuming there's a 'user' table add (, ForeignKey('user.id'))
    activity_id = Column(Integer, ForeignKey('activity_catalog.id'))  # referencing the ActivityCatalog table
    start_time = Column(DateTime, default=datetime.now())
    end_time = Column(DateTime)
    duration = Column(Integer)  # Duration in seconds

    def __repr__(self):
        return (f"<Activity(id={self.id!r}, user_id={self.user_id!r}, "
                f"activity_id={self.activity_id!r}, start_time={self.start_time!r}, "
                f"end_time={self.end_time!r}, duration={self.duration!r})>")


class ActiveSession(Base):
    __tablename__ = 'active_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    activity_id = Column(Integer, ForeignKey('activity_catalog.id'), nullable=False)
    start_time = Column(DateTime, default=datetime.now())
