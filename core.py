# -*- coding: utf-8 -*-
'''
Created on 2017. 5. 18.
@author: HyechurnJang
'''

import uuid
import inspect
from pygics import Task, Queue

_prometheus_generators = {}
_prometheus_generator_by_uuid = {}
_prometheus_actors = {}
_prometheus_actor_by_uuid = {}

class Element:
    
    VENDOR = 'Unknown'
    TITLE = 'Unknown'
    VERSION = ''
    INFO = ''
    DESC = ''
    
    def __init__(self):
        self._prometheus_uuid = str(uuid.uuid4()).replace('-', '')
        self._prometheus_flow = None
        self._prometheus_prev = None
        self._prometheus_next = None
    
    def getUUID(self): return self._prometheus_uuid
    def getName(self): return self._prometheus_name
    
class Processor(Element):
    
    class InputParamNotMatched(Exception):
        def __init__(self): Exception.__init__(self, 'input parameter not matched')
    
    class OutputParamNotMatched(Exception):
        def __init__(self): Exception.__init__(self, 'output parameter not matched')
        
    class ExceptProcessing(Exception):
        def __init__(self, e): Exception.__init__(self, str(e))
    
    def __init__(self):
        Element.__init__(self)
        self._prometheus_create_scheme = {}
        self._prometheus_input_scheme = {}
        self._prometheus_output_scheme = {}
        self._prometheus_create_option = {}
        self._prometheus_input_option = {}
        self._prometheus_output_option = {}
        
        spec = inspect.getargspec(self.create)
        
        self._prometheus_create_args = spec.args
        self._prometheus_create_defs = spec.defaults if spec.defaults != None else []
        
        alen = len(self._prometheus_create_args)
        dlen = len(self._prometheus_create_defs)
        rlen = alen - dlen
        
        for i in range(0, alen):
            if i < rlen: self._prometheus_create_scheme[self._prometheus_create_args[i]] = 'required'
            else:
                self._prometheus_create_scheme[self._prometheus_create_args[i]] = 'optional'
                self._prometheus_create_option[self._prometheus_create_args[i]] = self._prometheus_create_defs[i - rlen]
    
    def __set_input_scheme__(self):
        spec = inspect.getargspec(self.InputScheme)
        
        self._prometheus_input_args = spec.args[1:]
        self._prometheus_input_defs = spec.defaults if spec.defaults != None else []
        
        alen = len(self._prometheus_input_args)
        dlen = len(self._prometheus_input_defs)
        rlen = alen - dlen
        
        for i in range(0, alen):
            if i < rlen: self._prometheus_input_scheme[self._prometheus_input_args[i]] = 'required'
            else:
                self._prometheus_input_scheme[self._prometheus_input_args[i]] = 'optional'
                self._prometheus_input_option[self._prometheus_input_args[i]] = self._prometheus_input_defs[i - rlen]
    
    def __inspect_input_format__(self, input_data):
        try: self.InputScheme(**input_data)
        except TypeError: raise Processor.InputParamNotMatched()
        for k, v in self._prometheus_input_option.items():
            if k not in input_data: input_data[k] = v
    
    def __set_output_scheme__(self):
        spec = inspect.getargspec(self.OutputScheme)
        
        self._prometheus_output_args = spec.args[1:]
        self._prometheus_output_defs = spec.defaults if spec.defaults != None else []
        
        alen = len(self._prometheus_output_args)
        dlen = len(self._prometheus_output_defs)
        rlen = alen - dlen
        
        for i in range(0, alen):
            if i < rlen: self._prometheus_output_scheme[self._prometheus_output_args[i]] = 'required'
            else:
                self._prometheus_output_scheme[self._prometheus_output_args[i]] = 'optional'
                self._prometheus_output_option[self._prometheus_output_args[i]] = self._prometheus_output_defs[i - rlen]
    
    def __inspect_output_format__(self, data):
        if not isinstance(data, tuple): data = [data]
        output_data = {}
        for i in range(0, len(data)): output_data[self._prometheus_output_args[i]] = data[i]
        try: self.OutputScheme(**output_data)
        except TypeError: raise Processor.OutputParamNotMatched()
        for k, v in self._prometheus_output_option.items():
            if k not in output_data: output_data[k] = v
        return output_data
    
class Interface(Element):
    
    class ExceptNonFilter(Exception):
        def __init__(self): Exception.__init__(self, 'except non filter')
    
    #===========================================================================
    # Inheritance
    #===========================================================================
    def __init__(self):
        Element.__init__(self)
        self._prometheus_flt = None
    
    def setFilter(self, flt):
        self._prometheus_flt = flt
        
    def getScheme(self):
        if self._prometheus_prev == None or self._prometheus_next == None: return None
        ret = {}
        ret['SRC'] = self._prometheus_prev._prometheus_output_scheme
        ret['DST'] = self._prometheus_next._prometheus_input_scheme
        return ret
    
    #===========================================================================
    # Internal Implemented
    #===========================================================================
    def __process__(self, stack, src):
        if self._prometheus_flt != None:
            dst = {}
            env = {'STACK' : stack, 'SRC' : src, 'DST' : dst}
            premap = self._prometheus_flt['premap']
            mapping = self._prometheus_flt['mapping']
            postmap = self._prometheus_flt['postmap']
            if premap != None and premap != '':
                exec(premap, env, env)
            for k, v in mapping.items():
                code = '''DST['%s'] = %s''' % (k, v)
                exec(code, env, env)
            if postmap != None and postmap != '':
                exec(postmap, env, env)
            return dst
        raise Interface.ExceptNonFilter()

class Filter(dict):
    
    def __init__(self, **flt):
        dict.__init__(self)
        self['premap'] = flt['premap'] if 'premap' in flt else None
        self['mapping'] = flt['mapping'] if 'mapping' in flt else {}
        self['postmap'] = flt['postmap'] if 'postmap' in flt else None
    
    def setPreprocess(self, code):
        self['premap'] = code
        return self
    
    def setMapping(self, param, code):
        self['mapping'][param] = code
        return self
    
    def setPostprocess(self, code):
        self['postmap'] = code
        return self

class Generator(Processor):
    
    #===========================================================================
    # Implementation
    #===========================================================================
    def OutputScheme(self): pass
    def create(self): pass
    def delete(self): pass
    
    #===========================================================================
    # Inheritance
    #===========================================================================
    def __init__(self):
        Processor.__init__(self)
        self.__set_output_scheme__()
    
    #===========================================================================
    # Internal Trigger
    #===========================================================================
    def trigger(self, data):
        if self._prometheus_flow != None: self._prometheus_flow._prometheus_flow_trigger.put(data)
    
class Actor(Processor):
    
    #===========================================================================
    # Implementation
    #===========================================================================
    def InputScheme(self): pass
    def OutputScheme(self): pass
    def create(self): pass
    def delete(self): pass
    def process(self): pass
    
    #===========================================================================
    # Inheritance
    #===========================================================================
    def __init__(self):
        Processor.__init__(self)
        self.__set_input_scheme__()
        self.__set_output_scheme__()
    
    #===========================================================================
    # Internal Implemented
    #===========================================================================
    def __process__(self, data):
        self.__inspect_input_format__(data)
        try: data = self.process(**data)
        except Exception as e: raise Processor.ExceptProcessing(e) 
        return self.__inspect_output_format__(data)

class Terminator(Processor):
    
    #===========================================================================
    # Implementation
    #===========================================================================
    def InputScheme(self): pass
    def create(self): pass
    def delete(self): pass
    def process(self): pass
    
    #===========================================================================
    # Inheritance
    #===========================================================================
    def __init__(self):
        Processor.__init__(self)
        self.__set_input_scheme__()
    
    #===========================================================================
    # Processing Method
    #===========================================================================
    def __process__(self, data):
        self.__inspect_input_format__(data)
        try: data = self.process(**data)
        except Exception as e: raise Element.ExceptProcessing(e)

class Flow(Task):
    
    def __init__(self):
        Task.__init__(self)
        self._prometheus_uuid = str(uuid.uuid4()).replace('-', '')
        self._prometheus_flow_trigger = Queue()
        
        self._prometheus_flow_processors = {}
        self._prometheus_flow_interfaces = {}
        self._prometheus_flow_generator = None
        
    def run(self):
        data = self._prometheus_flow_trigger.get()
        stack = {'order' : [], 'data' : []}
        curr_elem = self._prometheus_flow_generator
        stack['order'].append(self._prometheus_flow_generator._prometheus_uuid)
        stack['data'].append(data)
        while curr_elem._prometheus_next != None:
            curr_elem = curr_elem._prometheus_next
            if isinstance(curr_elem, Interface):
                try: data = curr_elem.__process__(stack, data)
                except Exception as e:
                    print('Processor:%s:%s %s' % (curr_elem.getName(), curr_elem.getUUID(), str(e)))
                    break
            elif isinstance(curr_elem, Processor):
                try: data = curr_elem.__process__(data)
                except Exception as e:
                    print('Interface:%s:%s %s' % (curr_elem.getName(), curr_elem.getUUID(), str(e)))
                    break
                stack['order'].append(curr_elem._prometheus_uuid)
                stack['data'].append(data)
            Task.yielding()
        
    def setGenerator(self, generator):
        if not isinstance(generator, Generator): return False
        self.delGenerator()
        generator._prometheus_flow = self
        self._prometheus_flow_processors[generator._prometheus_uuid] = generator
        self._prometheus_flow_generator = generator
        return True
    
    def delGenerator(self):
        if self._prometheus_flow_generator == None: return False
        generator = self._prometheus_flow_processors.pop(self._prometheus_flow_generator._prometheus_uuid)
        self._prometheus_flow_generator = None
        output_interface = generator._prometheus_next
        if output_interface != None:
            output_interface = self._prometheus_flow_interfaces.pop(output_interface._prometheus_uuid)
            output_interface._prometheus_next._prometheus_prev = None
            output_interface.delete()
            del output_interface
        generator.delete()
        del generator
        return True
    
    def addProcessor(self, actor):
        if not isinstance(actor, Actor) and not isinstance(actor, Terminator): return False
        if actor._prometheus_uuid in self._prometheus_flow_processors: return False
        actor._prometheus_flow = self
        self._prometheus_flow_processors[actor._prometheus_uuid] = actor
        return True
    
    def delProcessor(self, uuid):
        if uuid not in self._prometheus_flow_processors: return False
        if uuid == self._prometheus_flow_generator._prometheus_uuid: return False
        processor = self._prometheus_flow_processors.pop(uuid)
        input_interface = processor._prometheus_prev
        output_interface = processor._prometheus_next
        if input_interface != None:
            input_interface = self._prometheus_flow_interfaces.pop(input_interface._prometheus_uuid)
            input_interface._prometheus_prev._prometheus_next = None
            input_interface.delete()
            del input_interface
        if output_interface != None:
            output_interface = self._prometheus_flow_interfaces.pop(output_interface._prometheus_uuid)
            output_interface._prometheus_next._prometheus_prev = None
            output_interface.delete()
            del output_interface
        processor.delete()
        del processor
        return True
    
    def addInterface(self, **intf_desc):
        if 'src' not in intf_desc: return False
        if 'dst' not in intf_desc: return False
        src_uuid = intf_desc['src']
        dst_uuid = intf_desc['dst']
        if src_uuid not in self._prometheus_flow_processors: return False
        if dst_uuid not in self._prometheus_flow_processors: return False
        src_processor = self._prometheus_flow_processors[src_uuid]
        dst_processor = self._prometheus_flow_processors[dst_uuid]
        if src_processor._prometheus_next != None: return False
        if dst_processor._prometheus_prev != None: return False
        if isinstance(src_processor, Terminator): return False
        if isinstance(dst_processor, Generator): return False
        interface = Interface()
        interface.setFilter(Filter(**intf_desc))
        interface._prometheus_flow = self
        interface._prometheus_prev = src_processor
        interface._prometheus_next = dst_processor
        src_processor._prometheus_next = interface
        dst_processor._prometheus_prev = interface
        self._prometheus_flow_interfaces[interface._prometheus_uuid] = interface
        return True
    
    def delInterface(self, uuid):
        if uuid not in self._prometheus_flow_interfaces: return False
        interface = self._prometheus_flow_interfaces.pop(uuid)
        interface._prometheus_prev._prometheus_next = None
        interface._prometheus_next._prometheus_prev = None
        interface.delete()
        del interface
        return True

def register(cls):
    mro = inspect.getmro(cls)
    if Generator in mro:
        vendor = cls.VENDOR
        title = cls.TITLE
        if vendor not in _prometheus_generators:
            _prometheus_generators[vendor] = {}
        cls_uuid = str(uuid.uuid4()).replace('-', '')
        _prometheus_generators[vendor][title] = {'uuid' : cls_uuid,
                                                 'type' : 'generator',
                                                 'vendor' : vendor,
                                                 'title' : title,
                                                 'version' : cls.VERSION,
                                                 'info' : cls.INFO,
                                                 'description' : cls.DESC}
        _prometheus_generator_by_uuid[uuid] = cls
    elif Processor in mro:
        vendor = cls.VENDOR
        title = cls.TITLE
        if vendor not in _prometheus_actors:
            _prometheus_actors[vendor] = {}
        cls_uuid = str(uuid.uuid4()).replace('-', '')
        if Actor in mro: type = 'actor'
        elif Terminator in mro: type = 'terminator'
        else: type = 'raw'
        _prometheus_actors[vendor][title] = {'uuid' : cls_uuid,
                                             'type' : type,
                                             'vendor' : vendor,
                                             'title' : title,
                                             'version' : cls.VERSION,
                                             'info' : cls.INFO,
                                             'description' : cls.DESC}
        _prometheus_actor_by_uuid[uuid] = cls
    return cls