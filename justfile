
default:
    @just --list

# Clean the cell outputs in all notebooks
clean-notebooks:
  for filename in notebooks/*.ipynb; do \
    jupyter nbconvert --clear-output --inplace $filename; \
  done

# Run code checks on all notebooks
lint-notebooks:
  nbqa ruff notebooks
