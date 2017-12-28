osimport logging
import requests
import pickle
import configparser
import sys
import json
import pandas as pd
import idealista_api


if __name__ == "__main__":

    #Parse configuration file
    config = configparser.ConfigParser(interpolation = None)
    config.read('idealista_api.ini')

    #Read results
    with open(config['Dump']['filename'], 'rb') as f:
        # The protocol version used is detected automatically, so we do not have to specify it.
        data = pickle.load(f)

    #Get cookies for advanced queries
    cookie = config['Server']['cookie']

    print( data[0] )
    print( '\n' )

    #Create pandas dataframe
    table = pd.DataFrame.from_dict(data, orient='columns', dtype=None)

    #Delete useless columns
    column_to_drop = [  'country', 'externalReference', 'detailedType',
                        'thumbnail', 'province', 'hasVideo', 'hasPlan',
                        'suggestedTexts']
    table.drop(column_to_drop, inplace=True, axis=1)

    print( table )

