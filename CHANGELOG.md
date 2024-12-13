# Change Log
All notable changes to this project will be documented in this file.
Only changes for the API functions are described here. Changes made
to the internals and developing the package are not included. Check
the git log for details.

The format is based on [Keep a Changelog](http://keepachangelog.com/).
This project adheres to [PEP440](https://www.python.org/dev/peps/pep-0440/)
and by implication, [Semantic Versioning](http://semver.org/).

## [0.0.4] - 2024-12-18
- Updated environment variables so connections can be made to a database server.
- Updated notebooks for working with checklists and observations to display data in HTML tables.

## [0.0.3] - 2024-12-16
- Renamed 'working with the database' notebook to 'working with checklists'.
- Added a helper class, ObservationQuery for fetching Observations.

## [0.0.2] - 2024-12-15
- Added a helper class, ChecklistQuery for fetching Checklists.
- Updated settings to simplify loader script and eBird API notebook.

## [0.0.1] - 2024-12-12
Initial release with database models, example notebooks on how to
download records from eBird and load them into the database.
