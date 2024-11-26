import requests
import json
import pandas as pd
import os
from datetime import datetime

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
    # Make the request
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        print("Request was successful.")
        data = response.json()
        
        # Extract the list of auctions
        auctions = data['data']['getSyslumennAuctions']
        
        # Convert the list of auctions into a DataFrame
        df_new = pd.DataFrame(auctions)
        
        # Create an 'id' column using 'lotId' if available, otherwise 'lotName'
        df_new['id'] = df_new.apply(lambda row: row['lotId'] if row['lotId'] else row['lotName'], axis=1)
        
        # Ensure the 'id' is unique by combining with 'auctionDate' and 'auctionTime' if necessary
        df_new['id'] = df_new.apply(lambda row: row['id'] + '_' + row['auctionDate'] + '_' + row['auctionTime'] if df_new['id'].duplicated().any() else row['id'], axis=1)
        
        # Set 'id' as the index
        df_new.set_index('id', inplace=True)
        
        # Current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Rename the 'auctionType' column to the current timestamp
        df_new.rename(columns={'auctionType': timestamp}, inplace=True)
        
        # Keep only the timestamp column
        df_new = df_new[[timestamp]]
        
        # Check if the CSV file exists
        if os.path.exists('auction_data.csv'):
            # Load existing data
            df_existing = pd.read_csv('auction_data.csv', index_col='id')
            
            # Merge the new data with the existing data
            df_combined = df_existing.join(df_new, how='outer')
        else:
            # If no existing data, the combined data is the new data
            df_combined = df_new
        
        # Save the combined data back to CSV
        df_combined.to_csv('auction_data.csv')
        
        print("Data saved to auction_data.csv")
        print(df_combined)
    else:
        print("Request failed.")
        print("Status Code:", response.status_code)
        print("Response Text:")
        print(response.text)

except Exception as e:
    print("An error occurred:", e)
