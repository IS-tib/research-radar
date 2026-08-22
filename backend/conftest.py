# Marks backend/ as the pytest rootdir so it's added to the import path,
# regardless of how pytest is invoked (plain `pytest`, `python -m pytest`, CI).
# That's what lets `import radar` resolve from tests/test_radar.py.
