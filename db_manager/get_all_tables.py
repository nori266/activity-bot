import configparser
from sqlalchemy import create_engine, text

config = configparser.ConfigParser()
config.read('creds.ini')

DATABASE_URL = config.get('database', 'DB_URL')
engine = create_engine(DATABASE_URL)

# Get a connection from the engine
connection = engine.connect()

# 1. Retrieve a list of all databases
databases = connection.execute(text("SHOW DATABASES;"))
for database in databases:
    db_name = database[0]
    print(f"Database: {db_name}")

    # 2. For each database, retrieve a list of tables
    tables = connection.execute(text(f"SHOW TABLES IN {db_name};"))
    for table in tables:
        table_name = table[0]
        row_count = connection.execute(text(f"SELECT COUNT(*) FROM {db_name}.{table_name};")).scalar()
        print(f"  Table: {table_name} - Rows: {row_count}")

# Close the connection after using it
connection.close()
