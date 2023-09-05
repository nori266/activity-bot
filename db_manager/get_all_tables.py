from os import environ

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = environ.get('DB_URL')
engine = create_engine(DATABASE_URL)

# Get a connection from the engine
connection = engine.connect()

db_name = DATABASE_URL.split("/")[-1]

print(f"Database: {db_name}")

# Retrieve a list of tables for the database
tables = connection.execute(text(f"SHOW TABLES IN {db_name};"))
for table in tables:
    table_name = table[0]
    row_count = connection.execute(text(f"SELECT COUNT(*) FROM {db_name}.{table_name};")).scalar()
    print(f"  Table: {table_name} - Rows: {row_count}")

# Close the connection after using it
connection.close()
