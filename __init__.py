
#===============================================================================
# Abstraction
#===============================================================================
from core import Generator, Actor, Terminator, Interface, Filter, Flow, register

#===============================================================================
# APIs
#===============================================================================
import pygics
import core

@pygics.api('GET', '/generator')
def get_generators(req, uuid=None):
    if uuid != None:
        cls = core._prometheus_generator_by_uuid[uuid]
        return core._prometheus_generators[cls.VENDOR][cls.TITLE]
    return core._prometheus_generators
 
@pygics.api('GET', '/actor')
def get_actors(req, uuid=None):
    if uuid != None:
        cls = core._prometheus_actor_by_uuid[uuid]
        return core._prometheus_actors[cls.VENDOR][cls.TITLE]
    return core._prometheus_actors



