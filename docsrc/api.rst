.. py:currentmodule:: cmdstanpy

#############
API Reference
#############

*******
Classes
*******

CmdStanModel
============

A CmdStanModel object encapsulates the Stan program. It manages program compilation and provides the following inference methods:

:meth:`~CmdStanModel.sample`
    runs the HMC-NUTS sampler to produce a set of draws from the posterior distribution.

:meth:`~CmdStanModel.optimize`
    produce a penalized maximum likelihood estimate (point estimate) of the model parameters.

:meth:`~CmdStanModel.variational`
    run CmdStan’s variational inference algorithm to approximate the posterior distribution.

:meth:`~CmdStanModel.generate_quantities`
    runs CmdStan’s generate_quantities method to produce additional quantities of interest based on draws from an existing sample.

.. autoclass:: cmdstanpy.CmdStanModel
   :members:


CmdStanMCMC
===========

.. autoclass:: cmdstanpy.CmdStanMCMC
   :members:

CmdStanMLE
==========

.. autoclass:: cmdstanpy.CmdStanMLE
   :members:

CmdStanGQ
=========

.. autoclass:: cmdstanpy.CmdStanGQ
   :members:

CmdStanVB
=========

.. autoclass:: cmdstanpy.CmdStanVB
   :members:


InferenceMetadata
=================

.. autoclass:: cmdstanpy.InferenceMetadata
   :members:

RunSet
======

.. autoclass:: cmdstanpy.stanfit.RunSet
   :members:

*********
Functions
*********

cmdstan_path
============

.. autofunction:: cmdstanpy.cmdstan_path

install_cmdstan
===============

.. autofunction:: cmdstanpy.install_cmdstan

set_cmdstan_path
================

.. autofunction:: cmdstanpy.set_cmdstan_path

set_make_env
============

.. autofunction:: cmdstanpy.set_make_env

from_csv
========

.. autofunction:: cmdstanpy.from_csv

write_stan_json
===============

.. autofunction:: cmdstanpy.write_stan_json
