import requests
import json
import pandas as pd
import nltk
import logging

from open_alex import transform_from_open_alex

def get_works_by_keyword(search_str:str, pages_to_get:int = 1, per_page:int = 10) -> list[dict]:
    """Contact the openalex API to retrieve information about the desired topic in JSON format
    
    Args:
        search_str (str): Openalex Search Parameter
        pages_to_get (int): Number of pages to retrieve
        per_page (int): Number of records per page

    Returns:
        list[dict]: Openalex results organized in a list of dicts, ready to be transformed in a DataFrame
        """
    
    if not isinstance(search_str, str):
        raise ValueError(f'Expecting a str for "search_str", got "{type(search_str)}"')
    if not isinstance(pages_to_get, int) or pages_to_get<=0:
        raise ValueError(f'Expected a positive int for "pages_to_get", got "{type(pages_to_get)}"')
    if not isinstance(per_page, int) or per_page<=0:
        raise ValueError(f'Expected a positive int for "per_page", got "{type(per_page)}"')

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

def transform_to_df(data: list[dict]) -> pd.DataFrame:
    if not isinstance(data, list):
        raise TypeError(f'Expected a list, got "{type(data)}"')
    if not data:
        raise ValueError('Error! Data is empty!')
    if not all(isinstance(item, dict) for item in data):
        raise TypeError("All items in the list must be dicts")
    
    return pd.DataFrame(data)

def transform_to_standard_df(in_df: pd.DataFrame, origin_database_name: str) -> pd.DataFrame | None:
    """Transform an input dataframe to a strandardized dataframe following WoS column name conventions
    by applying rules contained in a template specific to the origin database from which the dataframe is from.

    Args:
        in_df (pd.DataFrame): Input dataframe
        origin_database_name (str): Name of the database from which the dataframe is from

    Returns:
        pd.DataFrame | None: Dataframe following WoS naming convention. None if errors occurred
    """
    
    if not isinstance(in_df, pd.DataFrame):
        raise ValueError(f'Expected a pd.DataFrame for "in_df", got "{type(in_df)}"')
    if not isinstance(origin_database_name, str) or not origin_database_name.strip():
        raise ValueError(f'Expected a non-empty string for "origin_database_name", got "{type(origin_database_name)}"')
    
    standardized_df = None
    if origin_database_name == 'openalex':
        standardized_df = transform_from_open_alex(input_df=in_df)
    else:
        logging.warning(f'Origin database "{origin_database_name}" not recognised. Must be either "openalex" or "pubmed"')

    if standardized_df is None:
        logging.warning(f'Result is empty! Please check input dataframe')

    return standardized_df

# def _perform_search(search_str):
#     search_str = search_str#"motorcycle"
#     print(f'Starting OpenAlex search for: {search_str}')
    
#     # Get works and save to a file
#     results = get_works_by_keyword(search_str=search_str, pages_to_get=2)
#     print(f'Results obtained. Entities count: {len(results)}')
#     with open(f"open_alex_{search_str}_results.json", "w") as f:
#         json.dump(results, f, indent=4)
#     print(f'Results successfully written to file!')
    
# def _load_json_from_file(filename):
#     with open(filename, 'r') as f:
#         data = json.load(f)
#     return data

def main():
    nltk.download('wordnet') # Necessary for open_alex transformation process
    logging.basicConfig(level=logging.INFO)

    KEYWORD_TO_SEARCH = "video games"

    logging.info(f'Starting OpenAlex search for: {KEYWORD_TO_SEARCH}')

    results = get_works_by_keyword(KEYWORD_TO_SEARCH, pages_to_get=1, per_page=10)

    results_df = transform_to_df(results)

    results_standard_df = transform_to_standard_df(results_df, origin_database_name='openalex')

    if results_standard_df is None:
        raise ValueError(f'Something went wrong when processing the results for keyword: "{KEYWORD_TO_SEARCH}"')
    
 
    # Get works and save to a file
    logging.info(f'Results obtained. Entities count: {len(results)}')
    with open(f"open_alex_{KEYWORD_TO_SEARCH}_results.json", "w") as f:
        json.dump(results, f, indent=4)
    logging.info(f'Results successfully written to file!')

    logging.info('Writing standardized dataframe to file...')
    with open(f'open_alex_{KEYWORD_TO_SEARCH}_results.csv', 'w', encoding='utf-8') as f:
        f.write(results_standard_df.to_csv())
    logging.info('Successfully wrote result df to file')

    


    # print('Start\n')
    # df = transform_to_df(_load_json_from_file('open_alex_motorcycle_results.json'))
    # print(f'Loaded df:\n{df}')
    # print(f'\n\nPRIMARY_LOCATION VALUE: {df['primary_location']}\n\n')
    # df_transformed = transform_to_standard_df(df, "")
    # print(f'Transformed df:\n{df_transformed}')
    
if __name__ == "__main__":
    main()


#works = get_works_by_keyword("publication_year:2024,default.search:artificial intelligence")