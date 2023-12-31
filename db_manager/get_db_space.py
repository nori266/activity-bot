from os import environ

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.sql import text


load_dotenv()

db_url = environ.get('DB_URL')
db_host = environ.get('DB_HOST')
engine = create_engine(
            db_url,
            connect_args=dict(host=db_host, port=3306)
        )

# Define the SQL query to fetch table size information
query = text("SHOW TABLE STATUS")

# Execute the query and fetch all rows corresponding to tables
with engine.connect() as connection:
    result = connection.execute(query)
    rows = result.fetchall()

# Calculate the total size of the database
print(rows)
total_size_bytes = sum(row[6] + row[8] for row in rows)
total_size_mb = total_size_bytes / (1024 * 1024)  # Convert bytes to megabytes

print(f"Total database size: {total_size_mb:.2f} MB")
