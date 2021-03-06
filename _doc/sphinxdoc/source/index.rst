.. project_name documentation documentation master file, created by
   sphinx-quickstart on Fri May 10 18:35:14 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

pyquickhelper documentation
===========================

   
   
**Links:**
    * `pypi/pyquickhelper <https://pypi.python.org/pypi/pyquickhelper/>`_
    * `GitHub/pyquickhelper <https://github.com/sdpython/pyquickhelper>`_
    * `documentation <http://www.xavierdupre.fr/app/pyquickhelper/helpsphinx/index.html>`_
    * `Windows Setup <http://www.xavierdupre.fr/site2013/index_code.html#pyquickhelper>`_


Description
-----------

This extension gathers three functionalities:
    * a logging function: :func:`fLOG <pyquickhelper.loghelper.flog.fLOG>`
    * a function to synchronize two folders: :func:`pyquickhelper.synchronize_folder <pyquickhelper.sync.synchelper.synchronize_folder>`
    * a function to generate a copy of a module, converting doxygen documentation in rst format: :func:`generate_help_sphinx <pyquickhelper.helpgen.sphinx_main.generate_help_sphinx>` (see also :func:`prepare_file_for_sphinx_help_generation <pyquickhelper.helpgen.utils_sphinx_doc.prepare_file_for_sphinx_help_generation>`)
    
The module is available on `pypi/pyquickhelper <https://pypi.python.org/pypi/pyquickhelper/>`_ and
on `GitHub/pyquickhelper <https://github.com/sdpython/pyquickhelper>`_.

Functionalities
---------------

    * help generation
    * folder synchronization
    * logging
    * import a flat file into a SQLite database
    * help running unit tests
    * functions to convert a pandas DataFrame into a HTML table or a RST table

Indices and tables
==================

+------------------+---------------------+---------------------+------------------+------------------------+------------------------------------------------+
| :ref:`l-modules` |  :ref:`l-functions` | :ref:`l-classes`    | :ref:`l-methods` | :ref:`l-staticmethods` | :ref:`l-properties`                            |
+------------------+---------------------+---------------------+------------------+------------------------+------------------------------------------------+
| :ref:`genindex`  |  :ref:`modindex`    | :ref:`search`       | :ref:`l-license` | :ref:`l-changes`       | :ref:`l-README`                                |
+------------------+---------------------+---------------------+------------------+------------------------+------------------------------------------------+
| :ref:`l-example` |  :ref:`l-FAQ`       | :ref:`l-notebooks`  |                  |                        | `Unit Test Coverage <coverage/index.html>`_    |
+------------------+---------------------+---------------------+------------------+------------------------+------------------------------------------------+
   
Navigation
==========

.. toctree::
    :maxdepth: 1

    doctestunit
    generatedoc
    generatesetup
    installation
    all_example
    all_example_otherpageofexamples
    all_FAQ
    all_notebooks
    glossary
    index_module
    license
    filechanges
    README
    all_indexes
