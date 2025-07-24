# db.py
import os
import hashlib
from peewee import (
    Model, SqliteDatabase, CharField, TextField,
    DateTimeField, FloatField, ForeignKeyField, IntegerField
)
from datetime import datetime

db_path = os.path.join(os.path.dirname(__file__), "trends.sqlite")
db = SqliteDatabase(db_path)


class BaseModel(Model):
    class Meta:
        database = db


class Trend(BaseModel):
    keyword = CharField(index=True)
    count = IntegerField()
    avg_sentiment = FloatField()
    score = FloatField()
    timestamp = DateTimeField(default=datetime.utcnow)

    @staticmethod
    def get_or_create_latest(keyword: str, **fields):
        trend, created = Trend.get_or_create(
            keyword=keyword,
            defaults={**fields}
        )
        if not created:
            # Update with new values if score is newer
            trend.count = fields["count"]
            trend.avg_sentiment = fields["avg_sentiment"]
            trend.score = fields["score"]
            trend.timestamp = datetime.utcnow()
            trend.save()
        return trend


class Post(BaseModel):
    trend = ForeignKeyField(Trend, backref='posts')
    source = CharField()
    user_id = CharField()
    date = CharField()
    content = TextField()
    content_hash = CharField(index=True)

    @staticmethod
    def hash_content(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def exists(cls, content: str):
        return cls.select().where(cls.content_hash == cls.hash_content(content)).exists()


class MarketData(BaseModel):
    trend = ForeignKeyField(Trend, backref='market_data')
    symbol = CharField()
    price = FloatField(null=True)
    change = FloatField(null=True)
    percent_change = FloatField(null=True)
    source = CharField()
    timestamp = DateTimeField(default=datetime.utcnow)


def init_db():
    db.connect()
    db.create_tables([Trend, Post, MarketData])
