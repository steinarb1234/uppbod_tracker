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
        auctions = data.get('data', {}).get('getSyslumennAuctions', [])
        if not auctions:
            print("No auction data found.")
            exit(0)

        # Convert the list of auctions into a DataFrame
        df = pd.DataFrame(auctions)

        # Filter out specific auction types
        df = df[df['auctionType'] != 'Lausafjáruppboð']
        df = df[df['lotType'] != 'Ökutæki']

        # Format 'auctionDate'
        def format_auction_date(date_str):
            try:
                parsed_date = datetime.strptime(date_str, '%m/%d/%Y, %I:%M:%S %p')
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                return date_str

        df['auctionDate'] = df['auctionDate'].apply(format_auction_date)

        # Create and clean 'id'
        df['id'] = df.apply(lambda row: row['lotId'] if row['lotId'] else row['lotName'], axis=1)
        df['id'] = df['id'].apply(lambda x: re.sub(r'[\\/*?:"<>|]', '', x))

        # Handle duplicate IDs
        if df['id'].duplicated().any():
            df['id'] = df.apply(lambda row: f"{row['id']}_{row['auctionDate']}_{row['auctionTime']}", axis=1)

        # Set 'id' as the index
        df.set_index('id', inplace=True)

        # Add 'last_fetched' timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df['last_fetched'] = timestamp

        # Load or combine with existing data
        if os.path.exists('auction_data.csv'):
            df_existing = pd.read_csv('auction_data.csv', index_col='id')

            # Combine and update fields
            df_combined = pd.concat([df_existing, df]).drop_duplicates(keep='last')
            df_combined.update(df)
        else:
            df_combined = df

        # Sort by 'auctionDate'
        df_combined.sort_values(by='auctionDate', inplace=True, ascending=False)

        # Define the first few columns to order
        first_columns = ['auctionType', 'lotName', 'auctionDate', 'auctionTime', 'petitioners', 'last_fetched']

        # Dynamically find the remaining columns
        remaining_columns = [col for col in df_combined.columns if col not in first_columns]

        # Combine to enforce the partial order
        column_order = first_columns + remaining_columns

        # Apply the column order to the DataFrame
        df_combined = df_combined[column_order]        

        # Save the updated data
        df_combined.to_csv('auction_data.csv')
        print("Data saved to auction_data.csv")
    else:
        print("Request failed.")
        print(f"Status Code: {response.status_code}\nResponse Text: {response.text}")

except Exception as e:
    print("An error occurred:", e)
