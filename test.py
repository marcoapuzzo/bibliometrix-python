import json
import requests 
import pandas as pd
import numpy as np
from itertools import chain
import time

def transform_to_df(data):
    return pd.DataFrame(data)

def _load_json_from_file(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def get_works_by_keywork(search_str, pages_to_get=1, per_page=10):
    """Fetch works with pagination."""
    
    url = "https://api.openalex.org/works"
    params = {
        "search": search_str,
        "per_page": per_page,
        "cursor": "*"
    }
    current_page_number = 0

    all_works = []
    while current_page_number < pages_to_get:
        try:
            response = requests.get(url, params=params).json()
            all_works.extend(response["results"])

            cursor = response["meta"].get("next_cursor")
            if not cursor:
                break
            params["cursor"] = cursor
            current_page_number+=1
        except Exception as e:
            raise e

    return all_works

def test_typing(x: str) -> list[str]:
    return [char*2 for char in x]

def reconstruct_abstract(abstract_inverted_index):
    max_index = max(chain(*abstract_inverted_index.values()))
    abstract_template = [""] * (max_index+1)

    for word, index_list in abstract_inverted_index.items():
        for index in index_list:
            abstract_template[index] = word
    
    abstract = " ".join(abstract_template)

    return abstract

def main():
    
    abstract_inverted_index = {
            "Mathematical": [
                0
            ],
            "models": [
                1
            ],
            "of": [
                2,
                43,
                48
            ],
            "a": [
                3
            ],
            "motorcycle": [
                4
            ],
            "and": [
                5,
                25,
                53
            ],
            "rider": [
                6
            ],
            "dependent": [
                7
            ],
            "on": [
                8
            ],
            "three": [
                9
            ],
            "alternative": [
                10
            ],
            "assumptions": [
                11
            ],
            "concerning": [
                12
            ],
            "the": [
                13,
                29,
                40,
                44,
                46,
                54
            ],
            "tyre": [
                14
            ],
            "behaviour": [
                15
            ],
            "are": [
                16,
                23,
                37,
                51,
                57
            ],
            "developed.": [
                17
            ],
            "Stability": [
                18
            ],
            "characteristics": [
                19
            ],
            "deduced": [
                20
            ],
            "from": [
                21
            ],
            "them": [
                22
            ],
            "compared,": [
                24
            ],
            "minimum": [
                26
            ],
            "requirements": [
                27
            ],
            "for": [
                28
            ],
            "model": [
                30
            ],
            "greater": [
                31
            ],
            "than": [
                32
            ],
            "have": [
                33
            ],
            "been": [
                34
            ],
            "previously": [
                35
            ],
            "satisfied": [
                36
            ],
            "established.": [
                38
            ],
            "Using": [
                39
            ],
            "most": [
                41
            ],
            "sophisticated": [
                42
            ],
            "models,": [
                45
            ],
            "effects": [
                47
            ],
            "design": [
                49,
                55
            ],
            "changes": [
                50
            ],
            "calculated,": [
                52
            ],
            "implications": [
                56
            ],
            "discussed.": [
                58
            ]
        }

    max_index = max(list(chain(*abstract_inverted_index.values())))
    abstract_template = [""] * (max_index+1)

    print(abstract_template)
    print(len(abstract_template))

    for word, index_list in abstract_inverted_index.items():
        for index in index_list:
            abstract_template[index] = word

    print(abstract_template)

    abstract = " ".join(abstract_template)

    print(abstract)
    
if __name__ == "__main__":
    main()