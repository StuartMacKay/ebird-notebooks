# eBird Notebooks

eBird Notebooks is collection of Jupyter notebooks for analysing data
from the eBird basic Dataset or downloaded using the eBird API.

## Getting Started

Download and unzip the code, or click on the "Use this template" button
to create a new repository.

```shell
cd ebird-notebooks
```

There are two options for installing the project:

1. Using pip
2. Using [uv](https://docs.astral.sh/uv/)

Instructions for installing the project using Conda will be added later.

### Install using pip

Create a virtual environment and activate it:
```shell
python3.12 -m venv .venv
source .venv/bin/activate
```
The virtualenv was created using python 3.12 but any recent python
version will do.

Install the requirements:
```shell
pip install -r requirements.txt
```
Now you can run the notebooks.


### Install using uv
Alternatively you can set up the project using uv, which works exactly
like pip, except it's faster. A lot faster.

If you are new to uv, you will probably have to install a python version first:
```shell
uv python install 3.12
```

```shell
uv venv
source .venv/bin/activate
```
The virtualenv was created using python 3.12 but any recent python version
will do. uv will use the python version from the file,`.python-version`.

Next install the project requirements:
```shell
uv sync
uv pip install -e .
```
The first command installs the project dependencies. The second, installs
the code in the src directory so you can easily import it into a notebook.

## Running the notebooks

If you install [direnv](https://direnv.net/), you can activate the virtualenv
automatically when you change to the project directory.

Create a copy of the file containing the project's environment variables,:
```shell
cp .env.example .env
```

If you sre going to use the eBird API, edit the `.env` file to add your
[API key](https://ebird.org/api/keygen).

Finally run jupyter lab
```shell
jupyter lab
```

### Set up the database

There are two notebooks, [working_with_ebird_api.ipynb](notebooks/working_with_ebird_api.ipynb),
and [working_with_ebird_basic_dataset.ipynb](notebooks/working_with_ebird_basic_dataset.ipynb),
which take you through the steps of creating the sqlite3 database and
loading the first set of observations. If you are going to use the eBird
Basic Dataset, then there is a copy of the sample data provided by eBird
in the `data/downloads/`directory.

Separate databases are used for the eBird Basic Dataset and the eBird API.
The data from the API is a subset of the Basic Dataset, but is less accurate
in three ways:

1. Not all the records will have been reviewed
2. Observers are identified by name only
3. Observations are identified by species

Checklists are updated all the time. Sometimes records are only reviewed,
years after the initial submission. So some fuzziness, particularly with
unusual observations, or rare birds will always be subject to change.

The second and third points are more serious. If there is more than one
observer with the same name, then all the checklists will belong to the
same person. Also, each observation is identified by a species code,
e.g. horlar1, (Horned Lark). That means if a species changes, because of
a mis-identification, the original record will remain. The eBird Basic
Dataset does not have this problem as an observation has a unique code,
so the species can be changed at any time. You could consider this to be
a bug, however the solution is to continually download all the checklists
to see if the number of species has changed. That's simply not practical.

For these reasons, observations from the eBird API should only be used
to get the latest information, which is subject to change. For more
detailed analysis use the eBird Basic Dataset. The downside, of course,
is that it is only updated once per month.

## Links

* Issues: https://github.com/StuartMacKay/ebird-notebooks/issues
* Repository: https://github.com/StuartMacKay/ebird-notebooks

## Licence

eBird Notebooks is available under the terms of the [MIT](https://opensource.org/licenses/MIT) licence.
