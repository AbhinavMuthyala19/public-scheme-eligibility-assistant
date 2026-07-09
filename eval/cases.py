"""Golden test profiles for the pipeline.

Each case is a profile plus what we expect the graph to do. We deliberately
assert *structural* correctness (a run completes, the state filter is
respected, no ineligible scheme is shown) rather than exact scheme names,
which vary with the LLMs.
"""

CASES = [
    {
        "name": "SC farmer, Madhya Pradesh",
        "profile": {"age": 45, "gender": "Male", "state": "Madhya Pradesh",
                    "area": "Rural", "category": "SC", "occupation": "Farmer",
                    "annual_income": 120000},
        "expect": "run",
    },
    {
        "name": "Student, Tamil Nadu",
        "profile": {"age": 20, "gender": "Male", "state": "Tamil Nadu",
                    "category": "OBC", "occupation": "Student",
                    "annual_income": 150000},
        "expect": "run",
    },
    {
        "name": "Woman farmer, Punjab (rural)",
        "profile": {"age": 30, "gender": "Female", "state": "Punjab",
                    "area": "Rural", "occupation": "Farmer",
                    "annual_income": 90000},
        "expect": "run",
    },
    {
        "name": "Senior citizen, Kerala",
        "profile": {"age": 68, "gender": "Female", "state": "Kerala",
                    "occupation": "Senior citizen", "annual_income": 60000},
        "expect": "run",
    },
    {
        "name": "Missing state -> should ask for more info",
        "profile": {"age": 30, "gender": "Male", "occupation": "Farmer"},
        "expect": "need_more_info",
    },
]
