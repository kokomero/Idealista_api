import requests
import json

url = r'https://api.spotify.com'
user_id = r'1150207993'
playlist_id = '6oB8fRhDMPgtfwNxLTk7AQ'

#Para conseguir OAuth TOken:
#https://developer.spotify.com/web-api/authorization-guide/
#o bien estos de ejemplos que caducan:
#https://developer.spotify.com/web-api/console/get-track/
auth_token = 'BQAkb74Kjl3JNKGpkDE89F8lk2_6fPZOQT1IybhCyRotUcfEBUQRgyZv-gGls1Upgeo0cw7hUrYRQhszpDaCdVTxr7BV4tEnw7spQeGtsdZbDoMOTji-1yCZJe7G5Pkp-jt5VK5Uhkr7djOHNVxgT4VzQngN_EScsmt9qgo'

#Headers for the GET request
headers = { 'Accept' : 'application/json',
            'Authorization' : 'Bearer ' + auth_token}

#Build url
url += r'/v1/users/' + user_id + r'/playlists/' + playlist_id + r'/tracks?'

def process_response( json_response ):
    """Process a playlist response from the Spotify Web api
    """
    tracks = []

    #For each track
    for t in json_response['items']:
        track = t['track']
        track_info = {}
        track_info['album_name'] = track['album']['name']
        track_info['image_url'] = track['album']['images'][0]['url']
        track_info['artist_name'] = track['album']['artists'][0]['name']
        track_info['track_name'] = track['name']
        track_info['track_duration'] = track['duration_ms']
        tracks.append( track_info )

    return tracks

tracks = []

#Do first requests
payload = {'limit': 100, 'offset': 0}
response = requests.get(url, params=payload, headers = headers)
jData = json.loads(response.content)
tracks.extend( process_response( jData ) )

#For each subsequent requests
while jData['next'] is not None:

    #Do following request
    response = requests.get( jData['next'], headers = headers )
    jData = json.loads(response.content)
    tracks.extend( process_response( jData ) )


print( tracks )
print( len( tracks ))

#print(response.url)
#print(response.text)


#>>> jData.keys()
#dict_keys(['href', 'items', 'limit', 'next', 'offset', 'previous', 'total'])


#curl -X GET "https://api.spotify.com/v1/users/1150207993/playlists/6oB8fRhDMPgtfwNxLTk7AQ/tracks?limit=100&offset=0"
#-H "Accept: application/json"
#-H "Authorization: Bearer BQBBuMsgAzyWKweg9_7SVIt7tYEEaTf0yIPEqflduta76qBtjxUWR4zKchudKnmPX_OklO4z80quZE-_EW7ick8SJFZ-4VfAVYxeRLRz188A_cRG2vcM-kNX2mUxnR3kq1IPnJAGcVrRWKJ87HXEdp30KnNMOoje9rS_f3I"
