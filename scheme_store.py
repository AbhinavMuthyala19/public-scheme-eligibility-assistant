"""Loads the scheme CSV once and looks up a scheme's full text by id.

The vector DB only stores chunks + light metadata, so agents that need a
scheme's complete eligibility / application text come here.
"""

import pandas as pd

from config import DATA_PATH


class SchemeStore:
    def __init__(self, path: str = DATA_PATH):
        self.df = pd.read_csv(path)

    def get(self, scheme_id) -> dict:
        # scheme_id was stored as the CSV row position during the DB build.
        row = self.df.iloc[int(scheme_id)]
        return {
            "scheme_id": str(scheme_id),
            "scheme_name": str(row["scheme_name"]),
            "state": str(row["state"]),
            "level": str(row["level"]),
            "eligibility": str(row["eligibility"]),
            "benefits": str(row["benefits"]),
            "application_process_text": str(row["application_process_text"]),
        }
