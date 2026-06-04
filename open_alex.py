import pandas as pd
import json
import numpy as np
from iso4 import abbreviate
import nltk
import logging
import traceback

def _fetch_value(data: pd.Series, key: str, is_return_list=False):
    if isinstance(data, pd.Series):
       try:
           result = data[key]
           if not isinstance(result, (list, dict)) and pd.isna(result):
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
            if not isinstance(value, (list, dict)) and pd.isna(value):
                return [] if is_return_list else ""
            return value
        except Exception as e:
            print(f'WARNING! Got exception \n{e}\nReturning empty value')
            return [] if is_return_list else ""
    else:
        raise ValueError(f'Data is of type{type(data)}. Must be pandas.Series!')
    
def _format_author_name(display_name: str) -> str:
    """Convert 'Firstname [Middlename] Lastname' to 'Lastname FI' format."""
    if not display_name or not display_name.strip():
        return ""
    
    parts = display_name.strip().split()
    
    if len(parts) == 1:
        return parts[0]  # single name, return as-is
    
    surname = parts[-1]
    initials = "".join(f"{p[0]}." for p in parts[:-1])
    
    return f"{surname} {initials}"

def _calculate_JI(name_to_abbreviate: str) -> str:
    if not name_to_abbreviate or not name_to_abbreviate.strip():
        return ""
    
    try:
        return(abbreviate(name_to_abbreviate))
    except Exception as e:
        logging.warning(f'WARNING! Got exception \n{e}\nReturning empty value')
        return ""

def _calculate_AU_or_AF(authorship_list: list[dict], fullname=False) -> list[str]:
    logging.debug(f'Invoked _calculate_AU\nArg type:{type(authorship_list)}\nArg:\n{authorship_list}\n\n')

    if not authorship_list:
        return []
    
    authors_list = []
    for authorship in authorship_list:
        try:
            author = authorship.get('author') or {}
            author_name = author.get('display_name')
            if author_name:
                authors_list.append(_format_author_name(author_name) if not fullname else author_name)
            else:
                logging.warning(f'Missing display_name in authorship entry: {authorship}')
        except:
            logging.warning(f'Malformed authorship entry (not a dict): {authorship}')
            continue

    return authors_list

def transform_from_open_alex(input_df: pd.DataFrame):
    result = []
    
    for index, row in input_df.iterrows():
        row_template = {
            "DB": "open_alex",
            "UT": _fetch_value(row, "id"),
            "DI": _fetch_value(row, "doi"),
            "PMID": _fetch_nested_value(row, ["ids", "pmid"]),
            "TI": _fetch_value(row, "title"),
            "SO": _fetch_nested_value(row, ['primary_location', 'source', 'display_name']),
            "JI": _calculate_JI(_fetch_nested_value(row, ['primary_location', 'source', 'display_name'])),
            "PY": _fetch_value(row, 'publication_year'),
            "DT": _fetch_value(row, 'type'),
            "LA": _fetch_value(row, 'language'),
            "TC": _fetch_value(row, 'cited_by_count'),
            "AU": _calculate_AU_or_AF(_fetch_value(row, 'authorships')),
            "AF": _calculate_AU_or_AF(_fetch_value(row, 'authorships'), fullname=True),
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

nltk.download('wordnet')
input_df = transform_to_df(_load_json_from_file('open_alex_motorcycle_results.json'))
output_df = transform_from_open_alex(input_df)
print(output_df.head(20))
with open('open_alex_result.csv', 'w', encoding='utf-8') as f: # Print to file to check
    f.write(output_df.to_csv())