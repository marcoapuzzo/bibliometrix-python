import requests
import json
import pandas as pd

def get_works_by_keyword(search_str, pages_to_get=1, per_page=10):
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

def transform_to_df(data):
    return pd.DataFrame(data)

def transform_to_standard_df(in_df: pd.DataFrame, origin_database_name: str) -> pd.DataFrame:
    """Transform an input dataframe to a strandardized dataframe following WoS column name conventions
    by applying rules contained in a template specific to the origin database from which the dataframe is from.

    Args:
        in_df (pd.DataFrame): Input dataframe
        origin_database_name (str): Name of the database from which the dataframe is from

    Returns:
        pd.DataFrame: Dataframe following WoS naming convention
    """
    
    ### Config
    template = _load_json_from_file("test_conversion_dict.json")
    out_df = pd.DataFrame(columns=list(template.keys()))
    
    
    ### Apply rules from the template
    apply_template(in_df, out_df, template)
    
    
    ### Return result
    return out_df

def _perform_search(search_str):
    search_str = search_str#"motorcycle"
    print(f'Starting OpenAlex search for: {search_str}')
    
    # Get works and save to a file
    results = get_works_by_keyword(search_str=search_str, pages_to_get=2)
    print(f'Results obtained. Entities count: {len(results)}')
    with open(f"open_alex_{search_str}_results.json", "w") as f:
        json.dump(results, f, indent=4)
    print(f'Results successfully written to file!')
    
def _load_json_from_file(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def main():
    print('Start\n')
    df = transform_to_df(_load_json_from_file('open_alex_motorcycle_results.json'))
    print(f'Loaded df:\n{df}')
    print(f'\n\nPRIMARY_LOCATION VALUE: {df['primary_location']}\n\n')
    df_transformed = transform_to_standard_df(df, "")
    print(f'Transformed df:\n{df_transformed}')
    
if __name__ == "__main__":
    main()


#works = get_works_by_keyword("publication_year:2024,default.search:artificial intelligence")