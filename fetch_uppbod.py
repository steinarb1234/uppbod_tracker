import requests
import json

# Define the URL
url = "https://island.is/api/graphql"

# Prepare the parameters
params = {
    "operationName": "GetSyslumennAuctions",
    "variables": json.dumps({}),  # Empty JSON object
    "extensions": json.dumps({
        "persistedQuery": {
            "version": 1,
            "sha256Hash": "197cbb06a8b49a3e09d61cc97811f7e6e0717f730f2446107717f83925133f91"
        }
    })
}

try:
    # Make the GET request
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        print("Request was successful.")
        print("Status Code:", response.status_code)
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print("Request failed.")
        print("Status Code:", response.status_code)
        print("Response Text:")
        print(response.text)

except requests.exceptions.SSLError as ssl_err:
    print("SSL Error occurred:", ssl_err)
except Exception as e:
    print("An error occurred:", e)
