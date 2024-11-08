eBird Notebooks
===============
eBird Notebooks brings together Django and Jupyter Lab to create an easy to
use platform for analysing data from eBird.

Features
--------
* Load observations from the `eBird Basic Dataset`_
* Load observations from your `eBird account`_
* Load checklists from the `eBird API`_

.. _eBird Basic Dataset: https://support.ebird.org/en/support/solutions/articles/48000838205-download-ebird-data#anchorEBD
.. _eBird account: https://ebird.org/downloadMyData
.. _eBIrd API: https://documenter.getpostman.com/view/664302/S1ENwy59

Quickstart
----------

.. quickstart-start

Download and unzip the code.

.. code-block:: console

    cd ebird-notebooks

Create the virtual environment:

.. code-block:: console

    uv venv

Activate it:

.. code-block:: console

    source .venv/bin/activate

Install the project requirements:

.. code-block:: console

    uv sync

Create a copy of the example .env file and edit it to add your `eBird API key`_:

.. code-block:: console

    cp .env.example .env

Create the database tables:

.. code-block:: console

    python manage.py migrate

Start Jupyter Lab:

.. code-block:: console

    python manage.py shell_plus --notebook

Finally, open up the `Notebook basics`_ and run all cells.

.. _eBird API key: https://ebird.org/api/keygen
.. _Notebook basics: https://github.com/StuartMacKay/ebird-notebooks/tree/master/notebooks/notebook_basics.ipynb

.. quickstart-end

Django Admin
------------
THe great thing about Django is the batteries-included philosophy, and, in particular,
the Django Admin which allows you to browse and edit the data in the database.

To use the Django Admin, create a user account (with superpowers):

.. code-block:: console

    python manage.py createsuperuser

Now run the django server:

.. code-block:: console

    python manage.py runserver

Open a new tab on your browser and visit http://localhost:8000/admin/

Project Information
-------------------
* Issues: https://github.com/StuartMacKay/ebird-notebooks/issues
* Repository: https://github.com/StuartMacKay/ebird-notebooks

The app is tested on Python 3.12, and Django 5.1.

The project is made available under the terms of the `MIT`_ license.

.. _MIT: https://opensource.org/licenses/MIT
