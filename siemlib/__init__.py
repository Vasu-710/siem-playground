"""Shared code for the collector and the pipeline.

Both services read and write the same tables and agree on the same event
shape, so that code lives here instead of being written twice.
"""
