import pandas as pd
import json
import numpy as np
from iso4 import abbreviate
import nltk
import logging
from itertools import chain
    
    
def _fetch_value(data: pd.Series, keys:list[str], is_return_list=False):
    '''Retrieve a value for the specified key-path in a pandas' Series object.
    This is intended to be used on a JSON object converted to DataFrame object.

    Args:
        data (pd.Series): Pandas' Series object from which to retrieve the information
        keys (list[str]): Ordered keys from top level to desired level.  Eg. ['Top-level', 'First-nested level', 'Second-nested level', ...]
        is_return_list (Bool): Specify if empty return must be a list or a str

    Returns:
        Any | [] | "": Nested value associated with the specified key or empty list/str for invalid results'''
    
    if not isinstance(data, pd.Series):
        raise ValueError(f'Data is of type {type(data)}. Must be pandas.Series!')
    
    if not isinstance(keys, list):
        raise ValueError(f'Keys is of type {type(keys)}. Must be list of strings!')
    
    for key in keys:
        if not isinstance(key, str):
            raise ValueError(f'Key: {key} from keys: {keys} is of type: {type(key)}. Must be string!')
        
    empty = [] if is_return_list else ""
    value = data.to_dict()

    for key in keys:
        if not isinstance(value, dict):
            logging.warning(
                f'Expected a dict, got {type(value)} for key "{key}" in keys "{keys}" for data:\n{data}'
                f'Returning empty {"list" if is_return_list else "string"}.'
            )
            return empty

        value = value.get(key)

        if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
            logging.warning(
                f'Value is missing or NaN for key "{key}" in keys: "{keys}" in data:\n{data}'
                f'Returning empty {"list" if is_return_list else "string"}.'
            )
            return empty

    return value


def _format_author_name(display_name: str) -> str:
    """Convert 'Firstname [Middlename] Lastname' to 'Lastname FI' format.
    
    Args:
        display_name (str): Author full-name to convert

    Returns:
        str: Author name converted to 'Lastname FI' format
    """
    if not isinstance(display_name, str):
        raise ValueError(f'Expected string for display_name "{display_name}". Got {type(display_name)}')

    if not display_name or not display_name.strip():
        logging.warning(f'Display_name "{display_name}" is empty. Returning "" ')
        return ""
    
    parts = display_name.strip().split()
    
    if len(parts) == 1:
        return parts[0]  # single name, return as-is
    
    surname = parts[-1]
    initials = "".join(f"{p[0]}." for p in parts[:-1])
    
    return f"{surname} {initials}"


def _calculate_JI(name_to_abbreviate: str) -> str:
    """Calculate the abbreviated form of the Journal name following ISO4 standard.
    
    Args:
        name_to_abbreviate (str): Journal name to abbreviate
        
    Returns:
        str: Abbreviated Journal name"""
    logging.debug(f'Invoked _calculate_JI\nArg type:{type(name_to_abbreviate)}\nArg:\n{name_to_abbreviate}\n\n')

    if not isinstance(name_to_abbreviate, str):
        raise ValueError(f'Expected string for name_to_abbreviate "{name_to_abbreviate}". Got {type(name_to_abbreviate)}')

    if not name_to_abbreviate or not name_to_abbreviate.strip():
        logging.warning(f'name_to_abbreviate "{name_to_abbreviate}" is empty. Returning "" ')
        return ""
    
    try:
        return(abbreviate(name_to_abbreviate))
    
    except Exception as e:
        logging.warning(f'WARNING! Got exception \n{e}\nReturning empty value')
        return ""


def _calculate_AU_or_AF(authorship_list: list[dict], fullname=False) -> list[str]:
    """Retrieve the names of the authors in either short or fullname format
    
    Args:
        authorship_list (list[dict]): authorships field in the open_alex json response
        fullname (bool): Flag for returning fullname or short name
        
    Returns:
        list[str]: List containing the names of the authors of the work"""
    logging.debug(f'Invoked _calculate_AU_or_AF\nArg type:{type(authorship_list)}\nArg:\n{authorship_list}\n\n')

    if not isinstance(authorship_list, list):
        logging.warning(f'Expectinga list, (got {type(authorship_list)}). \nAuthorships_list: {authorship_list}\nReturning empty list')
        return []

    if not authorship_list or authorship_list is None:
        logging.warning('Authorship_list is empty or None. Returning empty list')
        return []
    
    authors_list = []

    for authorship in authorship_list:
        if not isinstance(authorship, dict):
            logging.warning(f'Expected a dict, got {type(authorship)}')
            continue
        
        author = authorship.get('author')
        if not isinstance(author, dict):
            logging.warning(f'Expected a dict, got {type(author)}')
            continue

        author_name = author.get('display_name')
        if author_name is None or not author_name.strip():
            logging.warning(f'Missing display_name in authorship entry: {authorship}')
            continue

        authors_list.append(_format_author_name(author_name) if not fullname else author_name)

    return authors_list


def _calculate_C1(authorships_list: list[dict]) -> list[str]:
    """
    Calculate authors affiliations and returns them as a list of strings.

    Args:
        authorships_list (list[dict]): OpenAlex's response Json's authorship field
    
    Returns:
        list[str]: A list of the authors affiliations 
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
        if not isinstance(authorship, dict):
            logging.warning(f'Expected a dict, got "{type(authorship)}"')
            continue

        raw_affiliation_strings = authorship.get('raw_affiliation_strings')
        if not isinstance(raw_affiliation_strings, list):
            logging.warning(
                f'Expected a list for raw_affiliation_strings, '
                f'got {type(raw_affiliation_strings)}: {authorship}\n'
            )
            continue

        for affiliation_string in raw_affiliation_strings:
            if not isinstance(affiliation_string, str):
                logging.warning(f'Expected a str, got "{type(affiliation_string)}". Skipping...')
                continue
            affiliations_set.add(affiliation_string)

    return list(affiliations_set)
    

def _get_first_authorship(authorships_list: list[dict]) -> dict | None:
    '''
    Helper function to get the first authorship of an authorship list if present.

    Args:
        authorships_list (list[dict]): An authorships object from an open_alex.json search results file

    Returns:
        dict | None: The authorship if present, otherwise None
    '''

    logging.debug(f'Invoked _get_first_authorship\nArg type:{type(authorships_list)}\nArg:\n{authorships_list}\n')

    if not isinstance(authorships_list, list):
        logging.warning(f'Expected a list, got {type(authorships_list)}: {authorships_list}\nReturning None\n')
        return None

    if not authorships_list:
        logging.warning('Empty authorships list. Returning None\n')
        return None
    
    first_authorship = None
    for authorship in authorships_list: #Loop to find first author

        if not isinstance(authorship, dict):
            logging.warning(f'Expecting a dict, got "{type(authorship)}". Skipping...\n')
            continue
        
        author_position = authorship.get('author_position')
        if not isinstance(author_position, str): 
            logging.warning(f'Expected a str for author_position, got "{type(author_position)}". Skipping... ')
            continue

        if author_position == 'first':
            first_authorship = authorship
            break

    if not first_authorship:
        logging.warning(f'No first author found in {authorships_list}\nReturning None')
        return None
    
    return first_authorship


def _calculate_RP(authorships_list: list[dict]) -> str:
    '''
    Create the reprint address for the first author.
    <First Author abbreviated name> (CORRESPONDING AUTHOR) <First affiliation>
    If author is missing will return empty string. If affiliation is missing, will return
    just the author.

    Args:
        authorships_list (list[dict]): OpenAlex's Json response's authorship field
    Returns:
        "" | str: A string containing the first author's name and first affiliation address if present
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

    author_name = first_authorship.get('raw_author_name')
    author_affiliations = first_authorship.get('raw_affiliation_strings')

    if not isinstance(author_name, str):
        logging.warning(
            'Expected a str for raw_author_name, '
            f'got {type(author_name)}: {first_authorship}\n'
        )
        return ""

    reprint_address = f'{_format_author_name(author_name)} (CORRESPONDING AUTHOR)'

    if not isinstance(author_affiliations, list) or not author_affiliations:
        logging.warning(f'Expected a non-empty list, got "{type(author_affiliations)}". Returning incomplete reprint address "{reprint_address}"')
        return reprint_address
   
    first_affiliation = author_affiliations[0]
    if not isinstance(first_affiliation, str):
        logging.warning(f'Expected a str, got "{type(first_affiliation)}". Returning incomplete reprint address "{reprint_address}"')
        return reprint_address

    reprint_address += f" {first_affiliation}"

    return reprint_address


def _calculate_DE_and_ID(keyword_list: list[dict]) -> list[str]:
    '''
    Extract the keywords from Open_alex's json response's keyword field and return them as a list of str
    Args:
        keyword_list (list[dict]): OpenAlex's keyword field
    Returns:
        list[str]: A list containing the work's keywords
    '''
    logging.debug(f'Invoked _calculate_DE_and_ID\nArg type:{type(keyword_list)}\nArg:\n{keyword_list}\n')

    if not isinstance(keyword_list, list):
        logging.warning(f'Expected a list, got {type(keyword_list)}: {keyword_list}\nReturning empty list\n')
        return []

    if not keyword_list:
        logging.warning('Empty keywords list. Returning empty list\n')
        return []
    
    result = []
    for keyword_dict in keyword_list:
        if not isinstance(keyword_dict, dict):
            logging.warning(f'Expected a dict, got "{type(keyword_dict)}" Skipping...')
            continue
        
        keyword = keyword_dict.get('display_name')
        
        if not isinstance(keyword, str) or not keyword.strip():
            logging.warning(f'Expected a non-empty str, got "{type(keyword)}" Skipping...')
            continue
        
        result.append(keyword)
       
            
    return result
    
    
def _calculate_AB(abstract_inverted_index: dict) -> str:
    '''
    This function takes as input open_alex's json responses's "abstarct_inverted_index" field, which is a dict with words as keys 
    and index position as values. It returns the reconstructed sentence.
    Args:
        abstract_inverted_index (dict): A dictionary containing words as keys and their index postion as values
    Returns:
        str: A string of the reconstructed abstract
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
    If some parts are missing they will be excluded from the result

    Args:
        first_authorship (dict): The first authorship dictionary
        release_year (int): The release year of the work
        journal_name (str): The full name of the journal

    Returns:
        The calculated short reference as a str
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
    if not is_journal_name_valid or not journal_name:
        logging.warning('Empty journal_name value. Omitting it in the result')
        is_journal_name_valid = False
    
    # Fetch first author name
    author_name = first_authorship.get('raw_author_name')
    if not isinstance(author_name, str) or not author_name.strip():
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
    
    

def transform_from_open_alex(input_df: pd.DataFrame) -> pd.DataFrame:
    """Transformation function to convert an Open_alex JSON to the bibliometrix standard format.
    
    Args:
        input_df (pd.DataFrame): Open_alex JSON results converted to Pandas DataFrame
    
    Returns:
        pd.DataFrame: Bibliometrix standard format DataFrame"""
    
    logging.debug(f'Invoked "transform_from_open_alex".\n{input_df}\n\n')

    if not isinstance(input_df, pd.DataFrame):
        raise ValueError(f'Expected a pd.DataFrame, got "{type(input_df)}"!')

    result = []
    
    for index, row in input_df.iterrows():
        try:
            authorships = _fetch_value(row, ['authorships'])
            keywords = _fetch_value(row, ['keywords'], is_return_list=True)

            row_template = {
                "DB": "open_alex",
                "UT":   _fetch_value(row, ["id"]),
                "DI":   _fetch_value(row, ["doi"]),
                "PMID": _fetch_value(row, ["ids", "pmid"]),
                "TI":   _fetch_value(row, ["title"]),
                "SO":   _fetch_value(row, ['primary_location', 'source', 'display_name']),
                "JI":   _calculate_JI(_fetch_value(row, ['primary_location', 'source', 'display_name'])),
                "PY":   _fetch_value(row, ['publication_year']),
                "DT":   _fetch_value(row, ['type']),
                "LA":   _fetch_value(row, ['language']),
                "TC":   _fetch_value(row, ['cited_by_count']),
                "AU":   _calculate_AU_or_AF(authorships),
                "AF":   _calculate_AU_or_AF(authorships, fullname=True),
                "C1":   _calculate_C1(authorships),
                "RP":   _calculate_RP(authorships),
                "CR":   _fetch_value(row,[ 'referenced_works'], is_return_list=True), 
                "DE":   _calculate_DE_and_ID(keywords),
                "ID":   _calculate_DE_and_ID(keywords), 
                "AB":   _calculate_AB(_fetch_value(row, ['abstract_inverted_index'])),
                "VL":   _fetch_value(row, ['biblio', 'volume']),
                "IS":   _fetch_value(row, ['biblio', 'issue']),
                "BP":   _fetch_value(row, ['biblio', 'first_page']),
                "EP":   _fetch_value(row, ['biblio', 'last_page']),
                "SR":   _calculate_SR(
                    first_authorship=_get_first_authorship(authorships),
                    release_year=_fetch_value(row, ['publication_year']),
                    journal_name=_fetch_value(row, ['primary_location', 'source', 'display_name'])
                )
            }

            logging.debug(f'Row "#{index}":\n{row_template}\n\n')

            result.append(row_template)

        except Exception as e:
            logging.warning(f'Omitting row "#{index}" due to exception:\n{e}\n\n')
        
    return pd.DataFrame(result)

#nltk.download('wordnet')

# def transform_to_df(data):
#     return pd.DataFrame(data)

# def _load_json_from_file(filename):
#     with open(filename, 'r') as f:
#         data = json.load(f)
#     return data
# input_df = transform_to_df(_load_json_from_file('open_alex_motorcycle_results.json'))
# output_df = transform_from_open_alex(input_df)
# print(output_df.head(20))
# with open('open_alex_result.csv', 'w', encoding='utf-8') as f: # Print to file to check
#     f.write(output_df.to_csv())