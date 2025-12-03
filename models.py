from sqlalchemy import Column, Integer, String, JSON
from database import Base


class GeoLocation(Base):
    __tablename__ = "geo_location"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ip = Column(String, unique=True, index=True)
    ipstack_response = Column(JSON)
