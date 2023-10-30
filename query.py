import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta
import json
import settings

db_params = {
    'database': 'football_matches',
    'user': 'postgres',
    'password': 'thanhll123',
    'host': 'localhost',  
    'port': '5432',
}


def search_data(connection, cursor, location, begin_time, end_time):
    search_query = sql.SQL(f"SELECT \"booked_time\", \"name\", \"id\" FROM \"pitch\" WHERE \"location\" = '{location}'").format(sql.Literal(location), sql.Literal(begin_time), sql.Literal(end_time))
    cursor.execute(search_query)
    result = cursor.fetchall()
    pitch_available = []
    if result:
        for pitch in result:
            added = True
            for booked_time in pitch[0]: #booked_time is first element of list
                if (end_time >= booked_time['started_time'] and end_time <= booked_time['ended_time']) or (begin_time >= booked_time['started_time'] and begin_time <= booked_time['ended_time']):
                    added = False
                    break
            if added:
                pitch_info = {"id": pitch[2],"pitch_name": pitch[1]}
                pitch_available.append(pitch_info)
    return pitch_available

def selecttest(connection, cursor, id, begin_time):
    select_query_booked = sql.SQL(f"SELECT \"booked_time\" FROM \"pitch\" WHERE \"id\" = {id}").format(sql.Literal(id), sql.Literal(begin_time))
    cursor.execute(select_query_booked)
    result = cursor.fetchall()
    return result

def insert_data(connection, cursor, value):
    insert_query = sql.SQL("INSERT INTO host () VALUES ({})").format(sql.Literal(value))
    cursor.execute(insert_query)
    connection.commit()
    print("Data has added to database.")


# shift time is a dict like item in booked_time
def update_data(connection, cursor, id, begin_time, end_time):
    json_shift = {'started_time' : begin_time, 'ended_time': end_time}
    # query booked_time currently
    select_query_booked = sql.SQL(f"SELECT \"booked_time\" FROM \"pitch\" WHERE \"id\" = {id}").format(sql.Literal(id), sql.Literal(begin_time), sql.Literal(end_time))
    cursor.execute(select_query_booked)
    old_booked_time = cursor.fetchall()

    # update booked_time
    try:
        print(old_booked_time[0][0])
        # get list item from a json data [0][0]
        new_booked_time = old_booked_time[0][0] + [json_shift]
        update_query = "UPDATE \"pitch\" SET \"booked_time\" = %s WHERE \"id\" = %s;"
        cursor.execute(update_query, (json.dumps(new_booked_time), id))
        connection.commit()
        print("Dữ liệu đã được cập nhật thành công.")
        return "success"

    except (Exception, psycopg2.Error) as error:
        print("Lỗi khi cập nhật dữ liệu:", error)
        connection.rollback()
        return "failed"


booked_time = [
    {"started_time" : datetime(2023, 10, 20).timestamp(),
    "ended_time": datetime(2023, 10, 24) },
    {"started_time" : datetime(2023, 9, 20),
    "ended_time": datetime(2020, 9, 25) },
    {"started_time" : datetime(2023, 8, 20),
    "ended_time": datetime(2020, 8, 25) },
    {"started_time" : datetime(2023, 7, 20),
    "ended_time": datetime(2020, 7, 25) },
]

def check_shift_available(finding_time: datetime, booked_time):
    for shift in booked_time:
        if (finding_time> shift.get("started_time") and finding_time < shift.get("ended_time")):
            return "success"
    return "failed"

# res = check_shift_available(datetime.datetime.now(), booked_time)
# print(res)


# {"started_time" : 1697815800.0, "ended_time": 1697826600.0}
print((datetime(2023, 11, 6, 17, 0)).timestamp())
print((datetime(2023, 11, 6, 20, 0)).timestamp())
# print((datetime(2023, 11, 3, 18, 10)).timestamp())
# print(datetime.fromtimestamp(1698600600.0, tz = None))
print(datetime.fromtimestamp(1699207800.0, tz = None))
