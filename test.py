import json
import requests 
import pandas as pd
import numpy as np

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

def main():
    
    x = {
        'Hello': 'World'
    }
    y = ['Hello', 'World']
    if isinstance(x, dict) and x["Hello"] == 'World':
        print('X OK')
    if isinstance(y, dict) and y["Hello"] == 'World':
        print('Y OK')
    print(y is None)
    print(x['Hello'])
    print(x['World'])
    
if __name__ == "__main__":
    main()