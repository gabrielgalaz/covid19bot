from flask import Flask, request
import requests
import json
import time
import datetime
import requests
from datetime import datetime as datesplit

app = Flask(__name__)


ACCESS_TOKEN = '[CISCO WEBEX TEAM BOT ACCESS TOKEN]'
BOT_ID = '[CISCO WEBEX TEAM BOT ID]'
BOT_PERSONID = '[CISCO WEBEX TEAMS PERSON ID]'

#------------------------ HHTPS SSL CONTEXT -------------

certpem = '[Certificate/Path]/cert.pem'
keypem = '[Key/Path]/key.pem'

#--------------------------------------------------------


class covid19:
    def __init__(self,con):
        self.country = con.replace(' ','-').lower()
    def confirmed(self):
        url = "https://api.covid19api.com/live/country/"+self.country+"/status/confirmed"
        #print(url)
        response = requests.request("GET", url, data="", headers={})
        return json.loads(response.text)

    def recovered(self):
        url = "https://api.covid19api.com/live/country/"+self.country+"/status/recovered"
        response = requests.request("GET", url, data="", headers={})
        return json.loads(response.text)
    def deaths(self):
        url = "https://api.covid19api.com/live/country/"+self.country+"/status/deaths"
        response = requests.request("GET", url, data="", headers={})
        return json.loads(response.text)

def countryCovid19(c):
    country = c.replace(' ','-').lower()

    if (country == 'usa') or (country == 'united states'):
        country == 'us'

    url = "https://api.covid19api.com/live/country/"+country+"/status/confirmed"

    response = requests.request("GET", url, data="", headers={})
    return json.loads(response.text)


def globalCovid19():
    url = "https://api.covid19api.com/summary"
    response = requests.request("GET", url, data="", headers={})
    alldata = response.json()

    GlobalCovid = alldata['Global']
    GlobalCovid['Date'] = alldata['Date']
    return GlobalCovid


def readmsgTeams(roomId):
    url = "https://api.ciscospark.com/v1/messages"
    querystring = {"roomId":roomId}

    headers = {
        'Authorization': "Bearer "+ACCESS_TOKEN,
        'Content-Type': "application/json"
        }

    response = requests.request("GET", url, headers=headers, params=querystring)
    return(response.json())

def writemsgTeams(roomId, message, card=None):
    url = "https://api.ciscospark.com/v1/messages"

    attachments = []
    if card != None:
        attachments.append(card)

    payload = { "roomId":roomId,
                "text":message, 
                "attachments": attachments}
    
    payload = str(payload).replace("'",'\"')

    headers = {
        'Authorization': "Bearer "+ACCESS_TOKEN,
        'Content-Type': "application/json"
        }

    response = requests.request("POST", url, data=payload, headers=headers)

    return(response.json())

def createcardTeams(cardtitle=None,cardbody=None,cardaction=None,banner=False):
    body =[]
    actions =[]

    if banner:
        body.append({
            "type": "Image",
            "url": "http://www.hiway.cl/webexbots/resources/baner_covidbot.jpg",
            "size": "auto"
        })
    if cardtitle != None:
        body.append({
            "type": "TextBlock",
            "text": cardtitle,
            "size": "large"
        })
    if cardbody != None:
        body.append({
            "type": "TextBlock",
            "text": cardbody,
            "size": "small"
        })

    if cardaction != None:
        actions.append({
            "type": "Action.OpenUrl",
            "url": cardaction['url'],
            "title": cardaction['title']
        })

    attachment = {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "content": {
        "type": "AdaptiveCard",
        "version": "1.0",
        "body": body,
        "actions": actions
      }
    }

    return attachment

def dialogflowQuery(query,sessionId):
    url = "https://api.dialogflow.com/v1/query"

    querystring = {"v":"20150910"}

    payload = { "lang": "en",
                "query": query,
                "sessionId": sessionId,
                "timezone": "Santiago/America"}

    payload = str(payload).replace('"','\"')

    headers = {
        'Authorization': "Bearer b3537e81fd764ad285d2f8479d1055f3",
        'Content-Type': "application/json",
        }

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

    return(response.json())

def fechalarga(datex):

    objDate = datesplit.strptime(datex, '%Y-%m-%dT%H:%M:%SZ')

    return datesplit.strftime(objDate,'%A, %B %d %Y at %H:%M (UTC0)')

@app.route("/")
def hello():
    return "Hello World!"

@app.route('/api',methods=['POST'])
def formulario():
    req = request.json

    data = req['data']
    botpersonid = data['personId']

    if botpersonid != BOT_PERSONID:

        messages = readmsgTeams(data['roomId'])

        for msg in messages['items']:
            if (msg['created'] == data['created']) and (msg['id'] == data['id']):
                msg_text = msg['text']
                sessionId = msg['personId']
                break


        dialogflow_response = dialogflowQuery(msg_text, sessionId)

        intent_name = dialogflow_response['result']['metadata']['intentName']
        country = ''
        if intent_name == 'getCases':
            country = dialogflow_response['result']['parameters']['geo-country']

        response = dialogflow_response['result']['fulfillment']['speech']

        #--------------------------------- selector de acciones -----------------------------------------
        flagCard = False

        if  (country == '') and (response == 'getCasesSuccess'):
            summarycovid = globalCovid19()

            lastupdate = fechalarga(summarycovid['Date'])
            
            response = ['The last update on ',lastupdate,
                        ', indicates that in the world',
                        ' the total confirmed cases of COVID-19 are ',str(summarycovid['TotalConfirmed']), 
                        ' (',str(summarycovid['NewConfirmed']),' new cases)'
                        ', of which ',str(summarycovid['TotalRecovered']),' recovered',
                        ' and ',str(summarycovid['TotalDeaths']),' died.'
                        ]
            response =''.join(response)

            bodyCard = ['Last update: ',lastupdate,
                        '\n - Total Confirmed: '+str(summarycovid['TotalConfirmed']),
                        '\n - New Confirmed: '+str(summarycovid['NewConfirmed']),
                        '\n\n - Total Recovered: '+str(summarycovid['TotalRecovered']),
                        '\n - New Recovered: '+str(summarycovid['NewRecovered']),
                        '\n\n - TotalDeaths:    '+str(summarycovid['TotalDeaths']),
                        '\n - New Deaths:    '+str(summarycovid['NewDeaths']),
                        '\n'
                        ]
            titleCard = 'COVID-19 Cases in the World'

            flagCard = True


        elif (country != '') and (response == 'getCasesSuccess'):

            cases = countryCovid19(country)
            lastcases_confirmed = cases[-1]['Confirmed']
            lastcases_recovered = cases[-1]['Recovered']
            lastcases_deaths = cases[-1]['Deaths']
            lastcases_active = cases[-1]['Active']

            lastupdate = str(fechalarga(cases[-1]['Date']))
            response = ['The last update on ',lastupdate,
                        ', indicates that in ',country,
                        ' the total confirmed cases of COVID-19 are ',str(lastcases_confirmed),
                        ', of which ',str(lastcases_recovered),' recovered',
                        ' and ',str(lastcases_deaths),' died.'
                        ]
            response =''.join(response)

            bodyCard = ['Last update: ',lastupdate,
                        '\n - Confirmed: '+str(lastcases_confirmed),
                        '\n - Recovered: '+str(lastcases_recovered),
                        '\n - Deaths:    '+str(lastcases_deaths),
                        '\n - Active:    '+str(lastcases_active),
                        '\n'
                        ]
            titleCard = 'COVID-19 Cases in '+country

            flagCard = True
        else:
            pass

        #------------------------------------------------------------------------------------------------
        writemsgTeams(data['roomId'],response)
        if flagCard:
            
            casesCard = createcardTeams(cardtitle = titleCard,
                                        cardbody = ''.join(bodyCard),
                                        cardaction = { 
                                                        'url':'https://google.com/covid19-map/?hl=en',
                                                        'title':'Google COVID-19 Map'
                                                    },
                                        banner=True)
            writemsgTeams(data['roomId'],'Look this.',card=casesCard)

        return 'ok'

    else:
        print('Mensaje de COVIDBOT')
        return 'ok'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, ssl_context=(certpem, keypem))