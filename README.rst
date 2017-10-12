===========
logconfdump
===========

Python module useful to dump current configuration of logging module to file.

**Status:** *Pre-alpha* - working, but pending reorganization.

Motivation
==========

Python has beautiful standard module ``logging``. It has easy usage interface.
Besides this it has very flexible configuration.
However flexible configuration means that configuration interface is not so easy.
There are several ways to setup log filtering and output:

* Call to ``logging.basicConfig()`` can setup several basic parameters.
* Call to ``logging.config.fileConfig()`` can load configuration from INI-format file.
* Call to ``logging.config.dictConfig()`` can load configuration from python dictionary.
  Which itself can be loaded from almost any file format - JSON, YAML and so on.
* At last you can manually create every needed logger, handler and formatter.

There are ``logconf.py`` by Vinay Sajip (original author of logging module)
that can help you prepare configuration file for ``fileConfig()``.

**However there are no way to migrate from one configuration way to another.**

Introduction
============

This module intended to create file for ``fileConfig()`` from current configuration.
Also there are plans for exporting current configuration to dictionary sutable for ``dictConfig()``.
This can be used to:

* Create initial config file from ``basicConfig()``.
* Convert config from one format to another.
* Migrate from manually crafted calls of module factories and methods to one of config file formats.

.. 
   Installation
   ============

   **NB: setup.py not yet implemented!**

   Old-style way::

    git clone https://github.com/pyhedgehog/logconfdump.git
    cd logconfdump
    python setup.py install

   Install stable version (**not yet ready/published**)::

    pip install logconfdump

   Install development version::

    pip install git+https://github.com/pyhedgehog/logconfdump.git#egg=logconfdump

Usage
=====

Simple sample::

 import logging
 import logconfdump
 logging.basicConfig(level=logging.ERROR, filename='example1.log')
 logconfdump.dump_config('example1.ini')

This will create following ``example1.ini`` file::

 [loggers]
 keys=root

 [handlers]
 keys=hand1

 [formatters]
 keys=form1

 [logger_root]
 channel=
 qualname=(root)
 level=ERROR
 parent=
 handlers=hand1

 [handler_hand1]
 class=FileHandler
 args=('example1.log', 'a')
 filename=example1.log
 mode=a
 formatter=form1
 level=NOTSET

 [formatter_form1]
 format=%(levelname)s:%(name)s:%(message)s
 datefmt=

Later you can use it like this::

 import logging.config
 logging.config.fileConfig('example1.ini')

Plans
=====

* Convert from spaghetti code. Implement exporters for standard handlers/formatters.
* Implement ``dump_dict()``.
* Implement internal and pluggable protocol for exporting non-standard handlers/formatters.
* Write CLI converters (``pylog_conf2yaml`` and alike).

