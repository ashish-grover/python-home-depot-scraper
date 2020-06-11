import sys
import os
import requests
import json

import pymsteams

if len(sys.argv) != 3:
    print('Please provide the product number(s) and how many stores to search.')
    print('for example: homedepot.py 1001470384,1001533118 10')
    sys.exit(1)

##set up home depot variables
product_numbers = [str(i) for i in (sys.argv[1]).split(',')]
product_name = ''
total_stores_to_search = sys.argv[2]

##set up ms teams variables
msteams_connector_url = os.environ['MICROSOFT_TEAMS_CONNECTOR_URL']
message_body = ''
send_message = False

headers = {
        'Accept':'application/json'
        ,'user-agent':'PostmanRuntime/7.25.0'
        ,'accept':'*/*'
        ,'accept-encoding':'gzip,deflate,br'
        ,'connection':'keep-alive'
    }

url_stores = 'https://www.homedepot.ca/homedepotcacommercewebservices/v2/homedepotca/stores?pageSize=' + str(total_stores_to_search) + '&currentPage=0&latitude=43.3565&longitude=-79.8084&fields=FULL_SPA&lang=en'
response_stores = requests.request(
        'GET',
        url_stores,
        headers = headers
    )

for product_number in product_numbers:
    ##this is nuts - a separate api call has to be done to get the product name...
    url_product = 'https://www.homedepot.ca/homedepotcacommercewebservices/v2/homedepotca/products/' + product_number + '.json?fields=BASIC_SPA&lang=en'
    response_product = requests.request(
            'GET',
            url_product,
            headers = headers
        )

    if response_product.status_code == 200:
        data = json.loads(response_product.text)
        product_name = json.loads(response_product.text)['manufacturer']+ ' - ' + json.loads(response_product.text)['name']

    message_header = 'Product being searched for: ' + product_name + ' (' + json.loads(response_product.text)['modelNumber'] + ')\n\n'
    message_header += '=================================================== \n\n'
    print(message_header)

    if response_stores.status_code == 200:
        stores = json.loads(response_stores.text)['stores']
            
        if stores:
            message_body = ''
            send_message = False
            for store in stores:
                url = 'https://www.homedepot.ca/homedepotcacommercewebservices/v2/homedepotca/products/' + product_number + '/localized/' + store['name'] + '?fields=BASIC_SPA&lang=en'
                response = requests.request(
                        'GET',
                        url,
                        headers = headers
                    )
                
                if response.status_code == 200:                    
                    stock_level = json.loads(response.text)['storeStock']['stockLevel']
                    if (stock_level > 1):
                        output = 'There are ' + str(stock_level) + ' in stock at store ' + store['name'] + ', located at ' + store['address']['formattedAddress']
                        print(output)
                        message_body += output + '\n\n'
                        send_message = True
                    elif (stock_level == 1):
                        output = 'There is ' + str(stock_level) + ' in stock at store ' + store['name'] + ', located at ' + store['address']['formattedAddress']
                        print(output)
                        message_body += output + '\n\n'
                        send_message = True

    if send_message:
        ##send messages to Microsoft Teams
        myTeamsMessage = pymsteams.connectorcard(msteams_connector_url)
        myTeamsMessage.text(message_header + message_body)
        myTeamsMessage.send()        
    else:
        print('No stock available at any of the closest ' + total_stores_to_search + ' stores\n')
