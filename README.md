# eBird Notebooks

eBird Notebooks is collection of Jupyter notebooks for analysing data
from the eBird basic Dataset or downloaded using the eBird API. The
project can process records from three different sources:

1. The eBird Basic Dataset
2. Records from "Download My Data" in your eBird account
3. Records downloaded from the eBird API 2.0

## Getting Started

Download and unzip the code, or click on the "Use this template" button
to create a new repository.

The project uses [uv](https://docs.astral.sh/uv/) to manage the project, but you can also
use pip, if you like. Instructions for installing the project using
Conda will be added later.

```shell
cd ebird-notebooks
```

uv works exactly like pip, except it's faster. A lot faster.

If you are new to uv, you will probably have to install a python
version first:
```shell
uv python install 3.12
```

Now create the virtual environment and activate it:
```shell
uv venv
source .venv/bin/activate
```
The project file, pyproject.toml lists python 3.12 or late, but any recent
python version will do.

If you install [direnv](https://direnv.net/), you can activate the virtualenv
automatically when you change to the project directory.

Next install the project requirements:
```shell
uv sync
```

## Running the notebooks

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

There are three notebooks, one for each of the data sources:
* [working_with_ebird_basic_dataset.ipynb](notebooks/working_with_ebird_basic_dataset.ipynb)
* [working_with_my_ebird_data.ipynb](notebooks/working_with_my_ebird_data.ipynb)
* [working_with_ebird_api.ipynb](notebooks/working_with_ebird_api.ipynb)
which take you through the steps of creating the sqlite3 database and
loading the first set of observations. If you are going to use the eBird
Basic Dataset, then there is a copy of the sample data provided by eBird
in the `data/downloads/`directory.

Separate databases are used for each. The data from My eBIrd Data, and the
API are a subset of the Basic Dataset, but they are less accurate:

1. Not all the records will have been reviewed
2. Observers are identified by name only

Checklists are updated all the time. Sometimes records are only reviewed,
years after the initial submission. So some fuzziness, particularly with
unusual observations, or rare birds will always be subject to change.

The second point more serious, if you use data from the API. If there is
more than one observer with the same name, then all the checklists will
belong to the same person.

You can load data periodically using the API - there is a script included
so you can do daily downloads using a scheduler such as cron See the
"[working_with_ebird_basic_dataset.ipynb](notebooks/working_with_ebird_basic_dataset.ipynb)"
for more details.

If you want to load My eBird Data you will need to delete all existing
records, otherwise you will end up with duplicate records.

For these reasons, observations from the eBird API should only be used
to get the latest information, which is subject to change. For more
detailed analysis use the eBird Basic Dataset. The downside, of course,
is that it is only updated once per month.

## Links

* Issues: https://github.com/StuartMacKay/ebird-notebooks/issues
* Repository: https://github.com/StuartMacKay/ebird-notebooks

## Licence

eBird Notebooks is available under the terms of the [MIT](https://opensource.org/licenses/MIT) licence.
