import argparse
import csv
from datetime import datetime
import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_entities import Activity, Base


logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.DEBUG)

load_dotenv()


class DB_DDL:
    def __init__(self):
        self.session = self.get_session()

    def create_all_tables(self):
        Base.metadata.create_all(self.session.bind)
        # print("Tables were created:", Base.metadata.tables)

    def create_table(self, table: Base):
        table.__table__.create(self.session.bind)

    def drop_table(self, table: Base):
        table.__table__.drop(self.session.bind)

    def add_logs_from_csv(self, csv_file_path):

        with open(csv_file_path, mode='r') as file:
            reader = csv.DictReader(file)

            # Read each row in the CSV
            for row in reader:
                # Assuming your CSV columns are named: user_id, activity, start_time, end_time, duration
                activity = Activity(
                    user_id=row['user_id'],
                    activity=row['activity'],
                    start_time=datetime.strptime(row['start_time'], '%Y-%m-%d %H:%M:%S'),
                    # Adjust the format based on your CSV
                    end_time=datetime.strptime(row['end_time'], '%Y-%m-%d %H:%M:%S'),
                    # Adjust the format based on your CSV
                    duration=int(row['duration'])
                )

                self.session.add(activity)

            # Commit the new entries to the database
            self.session.commit()

        self.session.close()

    def check_tables_created(self):
        for table_name, table_class in Base.metadata.tables.items():
            # Get the row count
            row_count = self.session.query(table_class).count()
            print(f"Table: {table_name} - Rows: {row_count}")

            # Print rows limited to 30
            rows = self.session.query(table_class).limit(30).all()
            for row in rows:
                print(f"    {row}")

    @staticmethod
    def get_session():

        # Database setup
        DB_URL = os.environ.get('DB_URL')
        DB_HOST = os.environ.get('DB_HOST')
        engine = create_engine(
            DB_URL,
            connect_args=dict(host=DB_HOST, port=3306)
        )
        Session = sessionmaker(bind=engine)
        return Session()


def reload_data():
    """
    Reloads data from csv file to the database. Removes all the data from the database and replaces it with the data
    from the csv file.
    :param csv_file:
    :return:
    """
    db_ddl = DB_DDL()
    # TODO add a check to see if the csv file exists
    # TODO backup the database before dropping the tables
    db_ddl.drop_table(Activity)
    db_ddl.create_all_tables()
    db_ddl.check_tables_created()


if __name__ == '__main__':
    # ask the user if they want to reload the data from the csv file
    reload = input("Do you want to reload the data from the csv file? "
                   "This will remove all current data in the database! (yes/no): ")
    args = argparse.ArgumentParser()
    args.add_argument('--csv', type=str)
    parsed_args = args.parse_args()
    if reload == 'yes':
        reload_data()
    elif reload == 'no':
        print("Data not reloaded.")
        db_ddl = DB_DDL()
        db_ddl.check_tables_created()
    else:
        print("Invalid input. Please type 'yes' or 'no'.")
