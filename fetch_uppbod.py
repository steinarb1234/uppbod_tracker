import requests
import json
import pandas as pd
import os
from datetime import datetime
import re

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
        df = pd.DataFrame(auctions)
        
        # Filter out auctions where 'auctionType' is 'Lausafjáruppboð'
        df = df[df['auctionType'] != 'Lausafjáruppboð']
        df = df[df['LotType'] != 'Ökutæki']
        
        # Parse and reformat 'auctionDate' to match 'last_fetched' format
        def format_auction_date(date_str):
            try:
                # Parse the date string assuming it's in the format 'M/D/YYYY, 12:00:00 AM'
                parsed_date = datetime.strptime(date_str, '%m/%d/%Y, %I:%M:%S %p')
                # Reformat to 'YYYY-MM-DD HH:MM:SS'
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                # If parsing fails, return the original string
                return date_str
        
        df['auctionDate'] = df['auctionDate'].apply(format_auction_date)
        

        # Create an 'id' column using 'lotId' if available, otherwise 'lotName'
        df['id'] = df.apply(lambda row: row['lotId'] if row['lotId'] else row['lotName'], axis=1)
        
        # Clean 'id' to remove any special characters that might cause issues
        df['id'] = df['id'].apply(lambda x: re.sub(r'[\\/*?:"<>|]', '', x))
        
        # Ensure the 'id' is unique by combining with 'auctionDate' and 'auctionTime' if duplicates exist
        if df['id'].duplicated().any():
            df['id'] = df.apply(lambda row: f"{row['id']}_{row['auctionDate']}_{row['auctionTime']}", axis=1)
        
        # Set 'id' as the index
        df.set_index('id', inplace=True)
        
        # Current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Add a column for the current timestamp indicating the fetch time
        df['last_fetched'] = timestamp
        
        # Check if the CSV file exists
        if os.path.exists('auction_data.csv'):
            # Load existing data
            df_existing = pd.read_csv('auction_data.csv', index_col='id')
            
            # Update existing data with new data
            df_combined = df_existing.combine_first(df)
            
            # Update dynamic fields
            dynamic_fields = ['auctionType', 'auctionDate', 'auctionTime', 'publishText', 'auctionTakesPlaceAt', 'last_fetched']
            df_combined.update(df[dynamic_fields])
            
            # Identify auctions that are in df_existing but not in df_new
            missing_auctions = df_combined.index.difference(df.index)
            
            # Exclude auctions with 'auctionType' == 'Sölu lokið' from being marked as 'cancelled'
            auctions_to_cancel = df_combined.loc[missing_auctions]
            auctions_to_cancel = auctions_to_cancel[auctions_to_cancel['auctionType'] != 'Sölu lokið'].index
            
            # Mark 'auctionType' as 'cancelled' for eligible missing auctions
            df_combined.loc[auctions_to_cancel, 'auctionType'] = 'cancelled'
        else:
            # If no existing data, the combined data is the new data
            df_combined = df

        df_combined.sort_values(by=['auctionDate'], inplace=True)
        
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
