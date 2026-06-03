import requests
import json
import pandas as pd

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

def apply_template(in_df, out_df, template):
    for input_df_index, input_df_row in in_df.iterrows():
        row_to_add = {col: "" for col in in_df.columns}
        
        for template_col_name, template_instruction in template.items():
            pass

def _unpack_template_instruction(template_instruction: dict):
    if isinstance(template_instruction, dict):
        instruction_name = list(template_instruction.keys())[0]
        instruction_value = template_instruction[instruction_name]
        
        return instruction_name, instruction_value
    else:
        raise ValueError(f'Template is of type {type(template_instruction)}. Must be Dict!')
    
    
    
# def apply_template(in_df, out_df, template):
    
#     for in_df_index, in_df_row in in_df.iterrows(): # Take index and row values from input dataframe
#         row_to_add = {col: "" for col in in_df.columns}
    
#         for out_df_col_name, value_instruction in template.items(): # Take output column name and the instruction for its value
#             col_value = None
            
#             if isinstance(value_instruction, dict):
#                 instruction_name = list(value_instruction.keys())[0]
#                 instruction_value = list(value_instruction.values())[0]
                
#                 if isinstance(instruction_value, dict):
#                     sub_instruction_name = list(instruction_value.keys())[0]
#                     if  sub_instruction_name == 'nested_value':
#                         instruction_value = _get_nested_value(in_df_row, instruction_value[sub_instruction_name])
                
#                 if  instruction_name == 'const':
#                     col_value = instruction_value
#                 elif instruction_name == 'rename':
#                     col_value = in_df_row[instruction_value]
                    
                    
#             row_to_add[out_df_col_name] = col_value
                
#         out_df.loc[in_df_index] = row_to_add

def _get_nested_value(data: pd.Series, keys: list):
    # Convert data to JSON
    if isinstance(data, pd.Series):
        data = json.loads(data.to_json())
    else:
        raise ValueError(f'Data is of type {type(data)}. Must be pandas.Series!')
    
    for key in keys:
        if isinstance(data, dict):
            data = data[key]
            if isinstance(data, str):
                return data
            if isinstance(data, list):
                if len(data) == 0:
                    return ""
            continue
        

# def _get_nested_value(data: pd.Series, keys: list):
#     """Recursively accesses nested values in a JSON object."""
#     if isinstance(data, pd.Series): #Convert to JSON
#         print(f'DATA: {data} - TYPE: {type(data)}\n')
#         data = json.loads(data.to_json())
#         print(f'DATA: {data} - TYPE: {type(data)}\n')
    
    
#     if not keys:
#         print(f'\n\nNEsted value: {data}\n\n')
#         return data
#     key = keys[0]
#     if isinstance(data, list):
#         if len(data) == 0:
#             print(f'Missing value for key: {key}. Returning empty str')
#             return ""
    
#     if isinstance(data, dict) and key in data:
#         return _get_nested_value(data[key], keys[1:])
#     else:
#         raise KeyError(f"Key not found: {' -> '.join(keys)}")

def _perform_search(search_str):
    search_str = search_str#"motorcycle"
    print(f'Starting OpenAlex search for: {search_str}')
    
    # Get works and save to a file
    results = get_works_by_keywork(search_str=search_str, pages_to_get=2)
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


#works = get_works_by_keywork("publication_year:2024,default.search:artificial intelligence")