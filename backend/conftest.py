# This (intentionally near-empty) file does one important job: its presence tells
# pytest that THIS folder (backend/) is the project root, so it adds it to the
# import path. That's what lets `import radar` work from tests/test_radar.py no
# matter how pytest is launched (plain `pytest`, `python -m pytest`, or in CI).
