# -*- coding: utf-8 -*-
import os
import sys
import logging.handlers
import six
from six.moves.configparser import RawConfigParser

class LiteralExpr:
    def __init__(self, expr):
        self.expr = expr
    def __repr__(self):
        return self.expr

def dump_config(f=None):
    fclose = lambda:None
    if isinstance(f, six.string_types):
        f = open(f, 'w')
        fclose = f.close
    if f is None:
        f = sys.stdout
    try:
        handlers = {}
        formatters = {}
        loggers = {}
        def process_formatter(formatter):
            if formatter is None:
                return dict(sectname=None)
            if id(formatter) in formatters:
                return formatters[id(formatter)]
            klass = formatter.__class__
            fmtinfo = {'format':formatter._fmt, 'datefmt':formatter.datefmt or ''}
            if klass is not logging.Formatter:
                fmtinfo['class'] = klass.__module__+'.'+klass.__name__
            style = getattr(formatter, '_style', None)
            if style:
                for k,(tp,df) in getattr(logging, '_STYLES', {}).items():
                    if isinstance(style, tp):
                        if k != '%':
                            fmtinfo['style'] = k
                        break
            formatters[id(formatter)] = fmtinfo
            fmtinfo['sectname'] = 'form%d'%(len(formatters),)
            return fmtinfo
        def process_stream(stream):
            if stream is None:
                return None
            if stream is sys.stdout:
                return LiteralExpr('sys.stdout')
            if stream is sys.stderr:
                return LiteralExpr('sys.stderr')
            return stream.name
        def process_handler(handler):
            if handler is None:
                return dict(sectname=None)
            if id(handler) in handlers:
                return handlers[id(handler)]
            klass = handler.__class__
            try:
                reduced_obj = handler.__reduce_ex__(2)
                assert reduced_obj[0] is copy_reg.__newobj__
                assert isinstance(reduced_obj[1], tuple)
                assert len(reduced_obj[1]) == 1
                assert reduced_obj[1][0] is klass
            except Exception:
                reduced_obj = None
            if reduced_obj is None:
                hdlrdict = handler.__dict__.copy()
            else:
                hndldict = reduced_obj[2].copy()
            if klass is getattr(logging, '_StderrHandler', None):
                hndlinfo = {'class':'_StderrHandler', 'args':'()'}
            elif klass is logging.FileHandler:
                if handler.delay is not False:
                    args = os.path.relpath(handler.baseFilename),handler.mode,handler.encoding,handler.delay
                elif handler.encoding is not None:
                    args = os.path.relpath(handler.baseFilename),handler.mode,handler.encoding
                else:
                    args = os.path.relpath(handler.baseFilename),handler.mode
                hndlinfo = {'class':'FileHandler', 'args':repr(args), 'filename':args[0], 'mode':args[1]}
            elif klass is logging.StreamHandler:
                args = process_stream(handler.stream),
                hndlinfo = {'class':'StreamHandler', 'args':repr(args)}
            elif isinstance(klass, logging.FileHandler):
                args = os.path.relpath(handler.baseFilename),handler.mode
                hndlinfo = {'args':repr(args), 'filename':args[0], 'mode':args[1]}
            else:
                assert klass.__module__=='logging', "Unknown class of handler "+repr(handler)
            if 'class' not in hndlinfo:
                hndlinfo['class'] = klass.__module__+'.'+klass.__name__
            if getattr(handler, 'formatter', None):
                hndlinfo['formatter'] = process_formatter(handler.formatter)['sectname']
            hndlinfo['level'] = logging.getLevelName(handler.level)
            if issubclass(klass, logging.handlers.MemoryHandler) and handler.target:
                hndlinfo['target'] = process_handler(handler.target)
            handlers[id(handler)] = hndlinfo
            hndlinfo['sectname'] = handler._name or 'hand%d'%(len(handlers),)
            return hndlinfo
        def process_logger(logger):
            if isinstance(logger, logging.PlaceHolder):
                return
            if logger is None:
                # used as "parent" of root logger
                return dict(name='', qualname='')
            if id(logger) in loggers:
                return loggers[id(logger)]
            channel = name = logger.name
            if logger is logger.root:
                channel = name = ''
            parent = process_logger(logger.parent)
            pnamel = len(parent['name'])
            if pnamel and name[:pnamel+1] == parent['name']+'.':
                channel = name[pnamel+1:]
            loginfo = dict(
                    name=name, channel=channel,
                    qualname=name or '(root)',
                    sectname=(name or 'root').replace('.', '_'),
                    level=logging.getLevelName(logger.level),
                    parent=parent['qualname'],
                )
            if not logger.propagate:
                loginfo['propagate'] = '0'
            loginfo['handlers'] = ','.join(hndlinfo['sectname'] for hndlinfo in (process_handler(handler) for handler in logger.handlers) if hndlinfo)
            loggers[id(logger)] = loginfo
            #loginfo['sectname'] = name and 'log%d'%(len(loggers),) or 'root'
            return loginfo
        process_logger(logging.root)
        for logname in sorted(list(logging.root.manager.loggerDict.keys())):
            logger = logging.root.manager.loggerDict[logname]
            process_logger(logger)
        assert id(logging.root) in loggers
        assert all('sectname' in loginfo for loginfo in loggers.values())
        assert loggers[id(logging.root)]['sectname'] == 'root'
        assert all('sectname' in loginfo for loginfo in loggers.values())
        conf = RawConfigParser()
        conf.add_section('loggers')
        conf.set('loggers', 'keys', ','.join(loginfo['sectname'] for loginfo in loggers.values()))
        if handlers:
            conf.add_section('handlers')
            conf.set('handlers', 'keys', ','.join(hndlinfo['sectname'] for hndlinfo in handlers.values()))
        if formatters:
            conf.add_section('formatters')
            conf.set('formatters', 'keys', ','.join(fmtinfo['sectname'] for fmtinfo in formatters.values()))
        for loginfo in loggers.values():
            sectname = 'logger_'+loginfo.pop('sectname')
            loginfo.pop('name')
            conf.add_section(sectname)
            for k,v in loginfo.items():
                conf.set(sectname, k, v)
        for hdlrinfo in handlers.values():
            sectname = 'handler_'+hdlrinfo.pop('sectname')
            conf.add_section(sectname)
            for k,v in hdlrinfo.items():
                conf.set(sectname, k, v)
        for fmtinfo in formatters.values():
            sectname = 'formatter_'+fmtinfo.pop('sectname')
            conf.add_section(sectname)
            for k,v in fmtinfo.items():
                conf.set(sectname, k, v)
        if sys.version_info[0:2] >= (3, 4):
            conf.write(f, False)
        else:
            conf.write(f)
    finally:
        fclose()

if __name__ == '__main__':
    if len(sys.argv)>1:
        import logging.config
        logging.config.fileConfig(sys.argv[1])
    else:
        logging.basicConfig()
    dump_config(sys.stdout)
