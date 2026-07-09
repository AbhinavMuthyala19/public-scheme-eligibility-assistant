"""Reusable multi-LLM layer: provider adapters + an ensemble that calls
several providers, parses their JSON, and scores their agreement.

Every agent should call the LLM through here so the whole project shares
one interface and one place to add/remove providers.
"""
