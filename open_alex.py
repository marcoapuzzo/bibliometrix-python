import pandas as pd
import json
import numpy as np
from iso4 import abbreviate
import nltk
import logging
from itertools import chain
    
def _fetch_value(data: pd.Series, key: str, is_return_list=False):
    '''Retrieve a non-nested value for the specified key in a pandas' Series object.
    This is intended to be used on a JSON object converted to DataFrame object.

    Args:
        data (pd.Series): Pandas' Series object from which to retrieve the information
        key (str): Key name
        is_return_list (Bool): Specify if empty return must be a list or a str

    Returns:
    Any | [] | "": Value associated with the specified key or empty list/str for invalid results'''
    
    if not isinstance(data, pd.Series):
        raise ValueError(f'Data is of type {type(data)}. Must be pandas.Series!')
    
    if not isinstance(key, str):
        raise ValueError(f'Key is of type: {type(key)}. Must be str!')
        
    result = data.get(key)
    
    if not result:
        logging.warning(f'Result is empty for key: {key} in obj:\n{data}\nReturning empty val')
        return [] if is_return_list else ""
    
    return result
    
    
def _fetch_nested_value(data: pd.Series, keys:list[str], is_return_list=False):
    '''Retrieve a nested value for the specified key-path in a pandas' Series object.
    This is intended to be used on a JSON object converted to DataFrame object.

    Args:
        data (pd.Series): Pandas' Series object from which to retrieve the information
        key (list[str]): Ordered keys from top level to desired level.  Eg. ['Top-level', 'First-nested level', 'Second-nested level', ...]
        is_return_list (Bool): Specify if empty return must be a list or a str

    Returns:
    Any | [] | "": Nested value associated with the specified key or empty list/str for invalid results'''
    
    if not isinstance(data, pd.Series):
        raise ValueError(f'Data is of type {type(data)}. Must be pandas.Series!')
    
    if not isinstance(keys, list[str]):
        raise ValueError()
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


def _calculate_C1(authorships_list: list[dict]) -> list[str]:
    """
    Calculate authors affiliations and returns them as a list of strings

    :param Authorships_list: OpenAlex's authorship field
    :returns: A list of the authors affiliations 
    """
    logging.debug(f'Invoked _calculate_C1\nArg type:{type(authorships_list)}\nArg:\n{authorships_list}\n')

    if not isinstance(authorships_list, list):
        logging.warning(f'Expected a list, got {type(authorships_list)}: {authorships_list}\nReturning empty list\n')
        return []

    if not authorships_list:
        logging.warning(f'Empty authorships list. Returning empty list\n')
        return []
    
    affiliations_set = set()
    for authorship in authorships_list:
        try:
            raw_affiliation_strings = authorship.get('raw_affiliation_strings') #List of strings
        except:
            logging.warning(f'Malformed authorship entry (not a dict): {authorship}\n')
            continue

        if not isinstance(raw_affiliation_strings, list):
            logging.warning(
                f'Expected a list for raw_affiliation_strings, '
                f'got {type(raw_affiliation_strings)}: {authorship}\n'
            )
            continue

        affiliations_set.update(raw_affiliation_strings)


    return list(affiliations_set)
    

def _get_first_authorship(authorships_list: list[dict]) -> dict | None:
    '''
    Helper function to get the first authorship of an authorship list if present.

    :param authorships_list An authorships object from an open_alex.json search results file

    :return The authorship if present, otherwise None
    '''

    logging.debug(f'Invoked _get_first_authorship\nArg type:{type(authorships_list)}\nArg:\n{authorships_list}\n')

    if not isinstance(authorships_list, list):
        logging.warning(f'Expected a list, got {type(authorships_list)}: {authorships_list}\nReturning None\n')
        return None

    if not authorships_list:
        logging.warning(f'Empty authorships list. Returning None\n')
        return None
    
    first_authorship = {}
    for authorship in authorships_list: #Loop to find first author

        if not isinstance(authorship, dict):
            logging.warning(f'Malformed authorship entry (not a dict): {authorship}\n')
            continue
        
        author_position = authorship.get('author_position')
        
        if isinstance(author_position, str): 
            if author_position == 'first':
                first_authorship = authorship
                break
        else:
            logging.warning(
                f'Expected a str for author_position, '
                f'got {type(author_position)}: {authorship}\n'
            )
            continue

    if not first_authorship:
        logging.warning(f'No first author found in {authorships_list}\nReturning None')
        return None
    
    return first_authorship

def _calculate_RP(authorships_list: list[dict]) -> str:
    '''
    Create the reprint address for the first author
    :param authorships_list: OpenAlex's authorship field
    :returns A string containing the first author's name and first affiliation address if present
    '''
    logging.debug(f'Invoked _calculate_RP\nArg type:{type(authorships_list)}\nArg:\n{authorships_list}\n')

    if not isinstance(authorships_list, list):
        logging.warning(f'Expected a list, got {type(authorships_list)}: {authorships_list}\nReturning empty str\n')
        return ""

    if not authorships_list:
        logging.warning(f'Empty authorships list. Returning empty str\n')
        return ""
    
    first_authorship = _get_first_authorship(authorships_list)

    if not first_authorship:
        logging.warning(f'No first authorship found! \n{authorships_list}\nReturning empty str')
        return ""

    try:
        author_name = first_authorship.get('raw_author_name')
        author_affiliations = first_authorship.get('raw_affiliation_strings')
    except AttributeError:
        logging.warning(f'Malformed authorship entry (not a dict): {first_authorship}\n')
        return ""

    if not isinstance(author_name, str):
        logging.warning(
            f'Expected a str for raw_author_name, '
            f'got {type(author_name)}: {first_authorship}\n'
        )
        return ""

    reprint_address = f'{_format_author_name(author_name)} (CORRESPONDING AUTHOR)'

    if not isinstance(author_affiliations, list):
        logging.warning(f'Malformed raw_affiliation_strings (not a list): {first_authorship}')
        return reprint_address

    try:
        first_affiliation = author_affiliations[0]
    except IndexError:
        logging.warning(f'First affiliation is empty: {author_affiliations}')
        return reprint_address

    if not isinstance(first_affiliation, str):
        logging.warning(f'Malformed first affiliation (not a str): {first_affiliation}')
        return reprint_address

    reprint_address += f" {first_affiliation}"

    return reprint_address

    
def _calculate_DE_and_ID(keyword_list: list[dict]) -> list[str]:
    '''
    Extract the keywords from Open_alex keyword object and return them as a list of str
    :param keyword_list: OpenAlex's keyword field
    :returns A list containing the work's keywords
    '''
    logging.debug(f'Invoked _calculate_DE\nArg type:{type(keyword_list)}\nArg:\n{keyword_list}\n')

    if not isinstance(keyword_list, list):
        logging.warning(f'Expected a list, got {type(keyword_list)}: {keyword_list}\nReturning empty list\n')
        return []

    if not keyword_list:
        logging.warning(f'Empty keywords list. Returning empty list\n')
        return []
    
    result = []
    for keyword_dict in keyword_list:
        try:
            keyword = keyword_dict.get('display_name', None)
            
            if not isinstance(keyword, str):
                logging.warning(f'Warning! Malformed keyword: {keyword_dict}. Skipping...')
                continue
            
            result.append(keyword)
        except Exception as e:
            logging.warning(f'Malformed argument! {keyword_list}')
            
    return result
    
    
def _calculate_AB(abstract_inverted_index: dict) -> str:
    '''
    This function takes as input open_alex's "abstarct_inverted_index", which is a list of words
    and their position in the sentence. It returns the reconstructed sentence.
    :param abstract_inverted_index A dictionary containing words as keys and their index as values
    :return A string of the reconstructed abstract
    '''
    
    logging.debug(f'Invoked _calculate_AB\nArg type:{type(abstract_inverted_index)}\nArg:\n{abstract_inverted_index}\n')
    
    if not isinstance(abstract_inverted_index, dict):
        logging.warning(f'Expected a dict, got {type(abstract_inverted_index)}: {abstract_inverted_index}\nReturning empty str\n')
        return ""
    
    if not abstract_inverted_index:
        logging.warning(f'Dictionary is empty: {abstract_inverted_index}\nReturning empty str\n')
        return ""
    
    try:
        max_index = max(list(chain(*abstract_inverted_index.values())))
        abstract_template = [""] * (max_index+1)

        for word, index_list in abstract_inverted_index.items():
            for index in index_list:
                abstract_template[index] = word
        
        abstract = " ".join(abstract_template)
    except ValueError as e:
        logging.warning(f'Unexpected error!\n\n {e} \n\nReturning empty str')
        return ""

    return abstract
    

def _calculate_SR(first_authorship: dict, release_year: int, journal_name: str) -> str:
    '''
    Calculate the Short Reference -> "<First author name>, <release year>, <journal name>"

    :param first_authorship The first authorship dictionary
    :param release_year The release year of the work
    :param journal_name The full name of the journal

    :return The calculated short reference as a str
    '''
    logging.debug(f'Invoked _calculate_SR\nArg type:{type(first_authorship)}\nArg:\n{first_authorship}\n')
    logging.debug(f'Arg type:{type(release_year)}\nArg:\n{release_year}\nArg type:{type(journal_name)}\nArg:\n{journal_name}\n')

    is_release_year_valid = True
    is_journal_name_valid = True


    # Correct type checks
    if not isinstance(first_authorship, dict):
        logging.warning(f'Expected a dict for first_authorship, got a {type(first_authorship)} -> {first_authorship}\nReturning empty str')
        return ""
    if not isinstance(release_year, int):
        logging.warning(f'Expected an int for release_year, got a {type(release_year)} -> {release_year}\nOmitting it in the result.')
        is_release_year_valid = False
    if not isinstance(journal_name, str):
        logging.warning(f'Expected a str for journal_name, got a {type(journal_name)} -> {journal_name}\nOmitting it in the result.')
        is_journal_name_valid = False

    # Empty args check
    if not first_authorship:
        logging.warning('Empty first_authorship value. Returning empty str')
        return ""
    if not journal_name:
        logging.warning('Empty journal_name value. Omitting it in the result')
        is_journal_name_valid = False
    
    # Fetch first author name
    author_name = first_authorship.get('raw_author_name')
    if not author_name:
        logging.warning(f'First author name could not be found! {first_authorship}\n Returning empty str')
        return ""
    author_name = _format_author_name(author_name)

    short_reference_template = [author_name]
    if is_release_year_valid:
        short_reference_template.append(str(release_year))
    if is_journal_name_valid:
        short_reference_template.append(journal_name)

    short_reference = ", ".join(short_reference_template)

    return short_reference
    
    

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
            "C1": _calculate_C1(_fetch_value(row, 'authorships')),
            "RP": _calculate_RP(_fetch_value(row, 'authorships')),
            "CR": _fetch_value(row, 'referenced_works', is_return_list=True), 
            "DE": _calculate_DE_and_ID(_fetch_value(row, 'keywords', is_return_list=True)),
            "ID":  _calculate_DE_and_ID(_fetch_value(row, 'keywords', is_return_list=True)), 
            "AB": _calculate_AB(_fetch_value(row, 'abstract_inverted_index')),
            "VL": _fetch_nested_value(row, ['biblio', 'volume']),
            "IS": _fetch_nested_value(row, ['biblio', 'issue']),
            "BP": _fetch_nested_value(row, ['biblio', 'first_page']),
            "EP": _fetch_nested_value(row, ['biblio', 'last_page']),
            "SR": _calculate_SR(
                first_authorship=_get_first_authorship(_fetch_value(row, 'authorships')),
                release_year=_fetch_value(row, 'publication_year'),
                journal_name=_fetch_nested_value(row, ['primary_location', 'source', 'display_name'])
            )
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