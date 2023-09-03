from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import func


Base = declarative_base()


class Activity(Base):
    __tablename__ = 'activity'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)  # Assuming there's a 'user' table add (, ForeignKey('user.id'))
    activity = Column(String(256))  # TODO replace this with activity_id, use ForeignKey
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime)
    duration = Column(Integer)  # Duration in seconds

    def __repr__(self):
        return (f"<Activity(id={self.id!r}, user_id={self.user_id!r}, "
                f"activity={self.activity!r}, start_time={self.start_time!r}, "
                f"end_time={self.end_time!r}, duration={self.duration!r})>")
