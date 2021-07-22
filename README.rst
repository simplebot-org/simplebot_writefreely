DeltaChat/WriteFreely Bridge
============================

.. image:: https://img.shields.io/pypi/v/simplebot_writefreely.svg
   :target: https://pypi.org/project/simplebot_writefreely

.. image:: https://img.shields.io/pypi/pyversions/simplebot_writefreely.svg
   :target: https://pypi.org/project/simplebot_writefreely

.. image:: https://pepy.tech/badge/simplebot_writefreely
   :target: https://pepy.tech/project/simplebot_writefreely

.. image:: https://img.shields.io/pypi/l/simplebot_writefreely.svg
   :target: https://pypi.org/project/simplebot_writefreely

.. image:: https://github.com/simplebot-org/simplebot_writefreely/actions/workflows/python-ci.yml/badge.svg
   :target: https://github.com/simplebot-org/simplebot_writefreely/actions/workflows/python-ci.yml

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

`SimpleBot`_ plugin that allows Delta Chat users to publish in WriteFreely instances.

If this plugin has collisions with commands from other plugins in your bot, you can set a command prefix like ``/wf_`` for all commands::

  simplebot -a bot@example.com db simplebot_writefreely/command_prefix wf_

Install
-------

To install run::

  pip install simplebot-writefreely


.. _SimpleBot: https://github.com/simplebot-org/simplebot
