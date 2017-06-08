
#===============================================================================
# Abstraction
#===============================================================================
from core import Generator, Actor, Terminator, Interface, Filter, Flow

#===============================================================================
# Programming Interface
#===============================================================================
from core import register

#===============================================================================
# APIs
#===============================================================================
import pygics

# Flow #########################################################################
from core import _prometheus_flow_by_uuid
@pygics.api('GET', '/flow')
def get_flow(req, fid=None):
    if fid != None:
        flow = _prometheus_flow_by_uuid[fid]
        return {'name' : flow._prometheus_name,
                'uuid' : flow._prometheus_uuid,
                'active' : flow.isRun()}
    result = []
    for flow in _prometheus_flow_by_uuid.values():
        result.append({'name' : flow._prometheus_name,
                       'uuid' : flow._prometheus_uuid,
                       'active' : flow.isRun()})
    return result

@pygics.api('POST', '/flow')
def create_flow(req, name='Non-Named Flow'):
    flow = Flow(name)
    return {'name' : flow._prometheus_name,
            'uuid' : flow._prometheus_uuid,
            'active' : flow.isRun()}

@pygics.api('GET', '/startflow')
def start_flow(req, fid):
    flow = _prometheus_flow_by_uuid[fid]
    flow.start()
    return flow.isRun()

@pygics.api('GET', '/stopflow')
def stop_flow(req, fid):
    flow = _prometheus_flow_by_uuid[fid]
    flow.stop()
    return not flow.isRun()

@pygics.api('DELETE', '/flow')
def delete_flow(req, fid):
    flow = _prometheus_flow_by_uuid[fid]
    flow.delete()
    del flow
    return True

# Generator ####################################################################
from core import _prometheus_generators, _prometheus_generator_by_uuid
@pygics.api('GET', '/generator')
def get_generator(req, gid=None):
    if gid != None:
        cls = _prometheus_generator_by_uuid[gid]
        return _prometheus_generators[cls.VENDOR][cls.TITLE]
    return _prometheus_generators

@pygics.api('POST', '/generator')
def create_generator(req, fid, gid, name='Non-Named Generator'):
    _flow = _prometheus_flow_by_uuid[fid]
    _gen = _prometheus_generator_by_uuid[gid]()
    _gen.create(**req.data)
    return _flow.setGenerator(_gen)

@pygics.api('DELETE', '/generator')
def delete_generator(req, fid):
    _flow = _prometheus_flow_by_uuid[fid]
    return _flow.delGenerator()

# Actor ########################################################################
from core import _prometheus_actors, _prometheus_actor_by_uuid
@pygics.api('GET', '/actor')
def get_actor(req, aid=None):
    if aid != None:
        cls = _prometheus_actor_by_uuid[aid]
        return _prometheus_actors[cls.VENDOR][cls.TITLE]
    return _prometheus_actors

@pygics.api('POST', '/actor')
def create_actor(req, fid, aid, name='Non-Named Actor'):
    _flow = _prometheus_flow_by_uuid[fid]
    _act = _prometheus_actor_by_uuid[aid]()
    _act.create(**req.data)
    return _flow.addProcessor(_act)

@pygics.api('DELETE', '/actor')
def delete_actor(req, fid, aid):
    _flow = _prometheus_flow_by_uuid[fid]
    return _flow.delProcessor(aid)

#===============================================================================
# Web
#===============================================================================
from page import *
prometheus_page = PAGE()

@PAGE.MAIN(prometheus_page, 'Prometheus')
def prometheus_page_main(req):
    return DIV().html(
        HEAD(1).html("Prometheus Main"),
        PARA().html('This is Prometheus Page')
    )


