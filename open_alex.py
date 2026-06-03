import pandas as pd
import json
import numpy as np

def _fetch_value(data: pd.Series, key: str, is_return_list=False):
    if isinstance(data, pd.Series):
       try:
           result = data[key]
           if pd.isna(result):
               return [] if is_return_list else ""
           return result
       except Exception as e:
           print(f'WARNING! Got exception \n{e}\nReturning empty value')
           return [] if is_return_list else ""
    else:
        raise ValueError(f'Data is of type{type(data)}. Must be pandas.Series!')
    
def _fetch_nested_value(data: pd.Series, keys:list, is_return_list=False):
    if isinstance(data, pd.Series):
        try:
            value = data.to_dict()
            for key in keys:
                value = value.get(key, None)
                if value is None:
                    return [] if is_return_list else ""
            if pd.isna(value):
                return [] if is_return_list else ""
            return value
        except Exception as e:
            print(f'WARNING! Got exception \n{e}\nReturning empty value')
            return [] if is_return_list else ""
    else:
        raise ValueError(f'Data is of type{type(data)}. Must be pandas.Series!')
    

def _calculate_JI():
    return "JI"

def transform_from_open_alex(input_df: pd.DataFrame):
    result = []
    
    for index, row in input_df.iterrows():
        row_template = {
            "DB": "open_alex",
            "UT": _fetch_value(row, "id"),
            "DI": _fetch_value(row, "doi"),
            "PMID": "",
            "TI": _fetch_value(row, "title"),
            "SO": _fetch_nested_value(row, ['primary_location', 'source', 'display_name']),
            "JI": _calculate_JI(),
            "PY": _fetch_value(row, 'publication_year'),
            "DT": _fetch_value(row, 'type'),
            "LA": _fetch_value(row, 'language'),
            "TC": _fetch_value(row, 'cited_by_count'),
            # "AU": _calculate_AU(),
            # "AF": _calculate_AF(),
            # "C1": _calculate_C1(),
            # "RP": _calculate_RP(),
            # "CR": TODO
            # "DE": _calculate_DE(),
            # "ID": TODO 
            # "AB": _calculate_AB(),
            "VL": _fetch_nested_value(row, ['biblio', 'volume']),
            "IS": _fetch_nested_value(row, ['biblio', 'issue']),
            "BP": _fetch_nested_value(row, ['biblio', 'first_page']),
            "EP": _fetch_nested_value(row, ['biblio', 'last_page']),
            # "SR": _calculate_SR()
        }
        result.append(row_template)
        
        print(f'Row#{index}:\n{row_template}\n')
        
    return pd.DataFrame(result)


def transform_to_df(data):
    return pd.DataFrame(data)

def _load_json_from_file(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

input_df = transform_to_df(_load_json_from_file('open_alex_motorcycle_results.json'))
output_df = transform_from_open_alex(input_df)
print(output_df.head(20))