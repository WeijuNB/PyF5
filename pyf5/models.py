#coding:utf-8
import cPickle
from schematics.models import Model
from schematics.serialize import to_python
from schematics.types import DateTimeType, StringType, FloatType, BooleanType

from collections import namedtuple

# Change = namedtuple('Change', 'time, path, type')
from schematics.types.compound import ModelType, ListType
from watchdog.events import EVENT_TYPE_MOVED, EVENT_TYPE_DELETED, EVENT_TYPE_CREATED, EVENT_TYPE_MODIFIED, os
from utils import config_path


class BaseModel(Model):
    def dict(self):
        self.validate()
        return to_python(self)

    def __repr__(self):
        s = '<' + self.__class__.__name__
        for key in self._data:
            s += ' %s=%s' % (key, self._data[key])
        s += '>'
        return s

    def __str__(self):
        return self.__repr__()


class Change(BaseModel):
    timestamp = FloatType(required=True)
    path = StringType(required=True)
    type = StringType(required=True, choices=[
        EVENT_TYPE_MOVED,
        EVENT_TYPE_DELETED,
        EVENT_TYPE_CREATED,
        EVENT_TYPE_MODIFIED
    ])


class Project(BaseModel):
    path = StringType(required=True)
    active = BooleanType(default=False)
    muteList = ListType(StringType(), default=[])
    targetHost = StringType()


class Config(BaseModel):
    projects = ListType(ModelType(Project), default=[])

    @classmethod
    def load(cls, path):
        config_data = cPickle.load(open(config_path()))
        config = Config(**config_data)
        return config

    def save(self, path):
        cPickle.dump(self.dict(), open(path, 'w+'))
        return True


if __name__ == '__main__':
    config = Config()
    pass
