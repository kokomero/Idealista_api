import requests
import base64
import logging
import pickle
import configparser
import sys
import re

#Logger functions
logger = logging.getLogger( 'Idealista API')
logger.setLevel(logging.INFO)
#ch = logging.FileHandler('log.log')
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

def check_http_ok(status):
    """
    Check there is no error after HTTP request
    """
    #Check there was no error
    if status != 200:
        logger.error('There was a problem when querying ')
        logger.error( status )
        raise Error()

    return True

def POST_request_to_str(req):
    """
    For debugging purpose, show a HTTP POST request
    """
    out = '-----------START-----------' + '\n'
    out += req.method + ' ' + req.url + '\n'
    out += '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items())
    out += req.body.decode() + '\n'
    return out

def get_bearer_token(apikey, secret, url_oauth):
    """
    Get a OAuth bearer token for the queries. The APIKey and secret
    are provided by idealista API team:
    http://developers.idealista.com/access-request
    api@idealista.com
    """

    #Encode apikey and secret in base64
    authorization = apikey + ":" + secret
    authorization64 = base64.b64encode( authorization.encode('utf-8') )

    #Headers for the POST request
    headers = { 'Content-Type' : 'application/x-www-form-urlencoded;charset=UTF-8',
                'Authorization' : 'Basic ' + authorization64.decode() }

    #Parameters for the request
    payload = { 'grant_type' : 'client_credentials',
                'scope' : 'read'}

    #HTTP post request
    response = requests.post(url_oauth, data = payload, headers = headers)

    #Check response status
    check_http_ok( response.status_code )

    #Return JSON response
    return response.json()

def get_one_page_query(url, token, search_parameters):
    """
    Query idealista API and return one page of the query
    Args:
        url: url of idealista api
        token: authorization token provided by get_bearer_token()
        search_parameters: filter parameters, see PDF provided by
        idealista api team
    """

    headers = { 'Authorization' : r'Bearer ' + token
                #'Content-Type' : 'multipart/form-data;' #Does not work with this on
              }

    #Get multipart content format for query
    #None replace the filename
    filters = { k : (None, v) for (k, v) in search_parameters.items() }

    #HTTP post request
    req = requests.Request('POST', url, headers = headers, files = filters)
    req = req.prepare()
    s = requests.Session()
    response = s.send(req)

    #Log request
    logger.debug('POST request: %s', POST_request_to_str(req) )

    #Check there was no error
    check_http_ok( response.status_code )

    #Return JSON response
    return response.json()

def get_query(url, token, search_parameters):
    """
    Query idealista API and return all pages for the query
    Args:
        url: url of idealista api
        token: authorization token provided by get_bearer_token()
        search_parameters: filter parameters, see PDF provided by
        idealista api team
    """
    elements = []

    #Get first page of the request
    results = get_one_page_query(url, token, search_parameters)

    #Save elements
    elements.extend( results[ 'elementList'] )
    total_pages = results['totalPages']
    logger.info("Number of pages to retrieve: %s", str( total_pages ) )

    for actualPage in range(2, total_pages + 1):
        search_parameters['numPage'] = str( actualPage )
        results = get_one_page_query(url, token, search_parameters)

        #Save results for the current page
        elements.extend( results[ 'elementList' ] )

        #print( results.keys() )
        #interesting_keys = ['total', 'totalPages', 'actualPage', 'itemsPerPage',
        #'numPaginations', 'hiddenResults', 'summary', 'paginable',
        #'upperRangePosition', 'lowerRangePosition']
        #for k in interesting_keys:
        #    print( k, results[ k ] )

    return elements

def get_search_parameters(config, buy = True, borough = 'Trafalgar'):
    """
    Get search parameter dicctionary from the configuration file
    Args:
        config: configuration object from the .ini file
        buy: True if buy, False if rent
        borough: name of the borough, as defined in .ini configuration file
    """

    #Set search parameters
    parameters = {  #'numPage' : 1,
                    'center' : config['BoroughLocation'][ borough ],
                    #'locationId' : '0-EU-ES-28',
                    'maxItems' : config['SearchFilters']['maxItems'],
                    'propertyType' : config['SearchFilters']['propertyType'],
                    'distance' : config['SearchFilters']['distance'],
                    'maxPrice' : config['SearchFilters']['maxBuyPrice'] if buy else config['SearchFilters']['maxRentPrice'],
                    'minPrice' : config['SearchFilters']['minBuyPrice'] if buy else config['SearchFilters']['minRentPrice'],
                    'bedrooms' : config['SearchFilters']['bedrooms'],
                    'operation' : 'sale' if buy else 'rent'
                 }

    return parameters
	

def get_view_statistic_for_ad(config, property_id):
    """
    Get statistisc for this advertisment
        property_id: identifier for the property
        cookie: cookie text for the request

    Remarks: We can get the cookie opening the url
    https://www.idealista.com/ajax/detailstatsview/37338540/ from Google Chrome,
    then, using developper tools (F12), we can see the Header Response and copy
    cookie text from there. This cookie has embedded session and user data, for
    now I am not able to hand craft one cookie from previous requests...    
    
    Only three fields of the cookie are needed, they are stored in the idealista_api.ini
    """

    url = config['Server']['url_statistics']
    url += r'/' + str( property_id ) + r'/'
    
    out = { }
    try:
        #Get web page
        response = requests.get(url, headers = { 'cookie' : config['Server']['cookie'] } )
        content = response.json()
        html_text = content['plainhtml']
        print(html_text)

        #Extract information with Regular expressions
        #TODO: make something more intelligent
        patterns = list( re.findall(r'[0-9]+', html_text) )
        out['num_visits'] = patterns[1]
        out['num_favorite'] = patterns[-1]
        return out
    
    except :
        logger.info("Error while retrieving statistics: ", url )
        print( 'Error in ', url)
        return { 'num_visits' : None, 'num_favorite' : None}

       
        
if __name__ == "__main__":

    #Parse configuration file
    config = configparser.ConfigParser(interpolation = None)
    config.read('idealista_api.ini')

    #Get the authorization token
    logger.info("Asking for an Authorization Token...")
    token = get_bearer_token( config['Server']['Apikey'],
                                config['Server']['Secret'],
                                config['Server']['url_oauth'] )
    bearer_token = token['access_token']
    logger.info("Authorization granted. Access token: %s",  bearer_token)

    #Get search parameters for buying
    filters = get_search_parameters(config, buy = True, borough = 'Trafalgar')

    #Query idealista API
    logger.info('Querying idealista API...')
    results = get_query(config['Server']['url_search'], bearer_token, filters)
    #print(results)
    
    #For each entry, get ad statistic
    for r in results:
        stats = get_view_statistic_for_ad( config, r['propertyCode'] )
        r[ 'num_favorite' ] = stats[ 'num_favorite' ]
        r[ 'num_visits' ] = stats[ 'num_visits' ]

    #Save results
    with open(config['Dump']['filename'], 'wb') as f:
        #Pickle the 'data' dictionary using the highest protocol available.
        logger.info('Saving results in pickle file...')
        pickle.dump(results, f, pickle.HIGHEST_PROTOCOL)

    #Read results
    with open(config['Dump']['filename'], 'rb') as f:
        # The protocol version used is detected automatically, so we do not
        # have to specify it.
        data = pickle.load(f)

    #print( data )

    #curl -X POST -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzY29wZSI6WyJyZWFkIl0sImV4cCI6MTQ5OTU1NDgyNSwiYXV0aG9yaXRpZXMiOlsiUk9MRV9QVUJMSUMiXSwianRpIjoiMDFlODZiNGUtZGE3NC00YWFlLThlM2MtMjc3MzljYWZiOWJkIiwiY2xpZW50X2lkIjoiaTRvd2R1cHVnOTZ5djQ2N3Y5ZndicjhzdmE2OTVha24ifQ.iDj5JYp28j691QZeXQZvK_T5kJ3segfudBSXTqqvx1U" -H "Content-Type: multipart/form-data;" -F "locationId=0-EU-ES-28" -F "propertyType=homes" -F "distance=15000" -F "operation=sale" "https://api.idealista.com/3.5/es/search" -v
