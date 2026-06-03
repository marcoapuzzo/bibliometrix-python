import json
import pandas as pd
import numpy as np

def transform_to_df(data):
    return pd.DataFrame(data)

def _load_json_from_file(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def main():
    
    # df = transform_to_df(_load_json_from_file('open_alex_motorcycle_results.json'))
    
    # template = _load_json_from_file('test_conversion_dict.json')
    # empty_df = pd.DataFrame(columns=list(template.keys()))
    
    # for index, row in df.iterrows():
    #     # Create a new row pre-filled with empty strings
    #     new_row = {col: "" for col in empty_df.columns}
        
    #     # Then overwrite the fields you want
    #     new_row['LA'] = row['id']
    #     new_row['TC'] = row['doi']
    #     new_row['AU'] = row['title']
    #     new_row['DB'] = index
        
    #     empty_df.loc[index] = new_row
        
    # print(empty_df)
    
    print(np.isnan(""))
    print(np.isnan("Test"))
    print(np.isnan([]))
    

    
if __name__ == "__main__":
    main()