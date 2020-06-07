import sys
import os
import requests
from requests.auth import HTTPBasicAuth
import json

from twilio.rest import Client

if not len(sys.argv) != 2:
    print('Please provide the product number and how many stores to search.')
    print('for example: homedepot.py 1001238260 10')
    sys.exit(1)

##set up home depot variables
product_number = sys.argv[1]
product_name = ''
total_stores_to_search = sys.argv[2]

##set up twilio variables
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)
message_body = ''
send_message = False

headers = {
        'Accept':'application/json'
        ,'user-agent':'PostmanRuntime/7.25.0'
        ,'cookie':'hap=s2; GROUTEID=.1; GCLB=COLu1Jq115Kvaw; bm_sz=AD84B54B91E552BCBA8D55B3DAC3CE83~YAAQVUKWuAT7v0tyAQAALP4dkAhx5wKc2UhTsNrE/jbnxgUW40mNPwYqogl+fMpBMISfDvAUsb4jFgddeYWmvPmcWprnOXcP/ZlIxOP/Ta8vZr3h0fqXS7Em9L5YaHw1HAlBUKhOgxR60lSglauUCCX+s+Nmb9mzEZBwUXdi/DSMPh+L+JzlTSIBJVj1SzNFkxg=; _abck=A6651D12D400B766FEFFD36DDC627776~-1~YAAQVUKWuAX7v0tyAQAALP4dkASWbjVz4PWJ32Hy997sQGedkHvt3T3tAPcsWYDdfnaT2t3jQYuTF78mSWtmbmYdILBHbKxzxDWyX11rbKCXmmCVbhOggUdX88IhewkIki1wxh6Ld34/ZV8/hVvzImlV1LOPgWDsIirqAY6hqzbaOaWsVJ9aeSwLLXedDLB8/4TNyolqmJpkn18FQFnJVZYwPrj62WAyRs/dTU9DBdeP7JCD1blk9Au7EPXSjfPrCyxAYSXRAH2cBefmZ5a4S1fCS6eYRoMLq1UHt2ECYeGAQJGn01xGq7eDxZU=~-1~-1~-1; payopt=OP; ak_bmsc=06A0845FAED53AC3A0EFD49EF8737875B89642559D510000B956DD5E1582266B~pllBrItAj97/Wwd1/5PMCO3mNkJ5DI7GuNYyYstDAQWa+SH/qhSd+ww1+hxKmaO9IIaa/2yMucXbiVA59dVDLGJARTPZKlOHkuy97LA5ZECAKoxpx+O0nYfCVzeBZuEMDzvOjgShTM/sNC9isizQMq/As1xhOJy0Nhi6sVZobdhXwYIWVNArq+qLrnH5D+Tc8XQw64Gw13e1DkOLY/aL9IqhlBKrg8P+XO9ZNI+8qNyBQ='
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

message_header = 'Product being searched for: ' + product_name + '\n\n'
print(message_header)

if response_stores.status_code == 200:
    stores = json.loads(response_stores.text)['stores']
        
    if stores:
        for store in stores:
            url = 'https://www.homedepot.ca/homedepotcacommercewebservices/v2/homedepotca/products/' + product_number + '/localized/' + store['name'] + '?fields=BASIC_SPA&lang=en'
            response = requests.request(
                    'GET',
                    url,
                    headers = headers
                )
            
            if response.status_code == 200:
                send_message = False
                stock_level = json.loads(response.text)['storeStock']['stockLevel']
                if (stock_level > 1):
                    output = 'There are ' + str(stock_level) + ' in stock at store ' + store['name'] + ', located at ' + store['address']['formattedAddress']
                    print(output)
                    message_body += output + '\n'
                    send_message = True
                elif (stock_level == 1):
                    output = 'There is ' + str(stock_level) + ' in stock at store ' + store['name'] + ', located at ' + store['address']['formattedAddress']
                    print(output)
                    message_body += output + '\n'
                    send_message = True                

if send_message:
    message = client.messages.create(
                            body = message_header + message_body,
                            from_ = '+16477230044',
                            to = '+19055994652'
                        )
else:
    print('No stock available at any of the closest ' + total_stores_to_search + ' stores')
