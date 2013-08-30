#coding:utf-8
import cPickle
from schematics.models import Model
from schematics.types import StringType, FloatType, BooleanType
from schematics.types.compound import ModelType, ListType
from watchdog.events import EVENT_TYPE_MOVED, EVENT_TYPE_DELETED, EVENT_TYPE_CREATED, EVENT_TYPE_MODIFIED


class BaseModel(Model):
    def dict(self):
        self.validate()
        return self.serialize()

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
    domains = ListType(StringType(), default=[])
    activeDomain = StringType()
    compileLess = BooleanType(default=False)
    compileCoffee = BooleanType(default=False)
    delay = FloatType(default=0.0)


class Config(BaseModel):
    projects = ListType(ModelType(Project), default=[])

    @classmethod
    def load(cls, path):
        config_data = cPickle.load(open(path))
        config = Config(config_data)
        return config

    def save(self, path):
        cPickle.dump(self.dict(), open(path, 'w+'))
        return True


if __name__ == '__main__':
    modal = BaseModel()
    pass
