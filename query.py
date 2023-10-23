import psycopg2
from psycopg2 import sql

db_params = {
    'database': 'football_matches',
    'user': 'postgres',
    'password': 'thanhll123',
    'host': 'localhost',  
    'port': '5432',
}


# try:
#     connection = psycopg2.connect(**db_params)
#     cursor = connection.cursor()
#     print("Connect successfully!")

#     # Query database

# except (Exception, psycopg2.Error) as error:
#     print("Error when connecting to database:", error)

# finally:
#     if connection:
#         cursor.close()
#         connection.close()
        # print("Close connection.")

def search_data(connection, cursor, location, date, shift):
    search_query = sql.SQL(f"SELECT * FROM pitch WHERE location = {location} AND shift = {date}").format(sql.Literal(location))
    cursor.execute(search_query)
    result = cursor.fetchall()
    return result
    # if result:
    #     print("Kết quả tìm kiếm:")
    #     for row in result:
    #         print(row)
    # else:
    #     print("Không tìm thấy kết quả.")

def insert_data(connection, cursor, value):
    insert_query = sql.SQL("INSERT INTO your_table_name (column_name) VALUES ({})").format(sql.Literal(value))
    cursor.execute(insert_query)
    connection.commit()
    print("Data has added to database.")