from taskiq import TaskiqScheduler

from src.scheduling.broker import broker
from src.scheduling.source import redis_source

scheduler = TaskiqScheduler(broker, sources=[redis_source])
