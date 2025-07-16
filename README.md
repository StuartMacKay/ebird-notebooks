# eBird Notebooks
eBird Notebooks brings together Django and Jupyter Lab to create an easy to
use platform for analysing data from eBird.

# Features

* Load checklists from the [eBird API](https://documenter.getpostman.com/view/664302/S1ENwy59)

## Quickstart

Download and unzip the code.

```shell
cd ebird-notebooks
```

Create the virtual environment:

```shell
uv venv
```

Activate it:

```shell
source .venv/bin/activate
```

Install the project requirements:

```shell
 uv sync
```

Create a copy of the example .env file and edit it to add your
[eBird API key](https://ebird.org/api/keygen):

```shell
 cp .env.example .env
```

Create the database tables:

```shell
 python manage.py migrate
```

Start Jupyter Lab:

```shell
python manage.py shell_plus --notebook
```

Finally, open up the [Getting Started](notebooks/getting-started.ipynb) notebook 
and run all cells.

## Django Admin

THe great thing about Django is the batteries-included philosophy, and, in particular,
the Django Admin which allows you to browse and edit the data in the database.

To use the Django Admin, create a user account (with superpowers):

```shell
python manage.py createsuperuser
```

Now run the django server:

```shell
python manage.py runserver
```

Open a new tab on your browser, visit http://localhost:8000/admin/, log in
using the newly created superuser account. When you run the cells in the 
Getting Started notebook you can then browse the data loaded into the tables.

## Project Information

* Issues: https://todo.sr.ht/~smackay/ebird-notebooks
* Repository: https://git.sr.ht/~smackay/ebird-notebooks
* Announcements: https://lists.sr.ht/~smackay/ebirders-announce
* Discussions: https://lists.sr.ht/~smackay/ebirders-discuss
* Development: https://lists.sr.ht/~smackay/ebirders-develop

The repository is also mirrored on Github:

* Repository: https://github.com/StuartMacKay/ebird-notebooks

# License

The project is made available under the terms of the [MIT](https://opensource.org/licenses/MIT) license.
