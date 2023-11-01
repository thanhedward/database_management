import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta
import json
import settings
import traceback

db_params = {
    'database': 'football_matches',
    'user': 'postgres',
    'password': 'thanhll123',
    'host': 'localhost',  
    'port': '5432',
}


def search_location_pitch(connection, cursor, location, begin_time, end_time):
    search_query = sql.SQL(f"SELECT \"booked_time\", \"name\", \"id\", \"url_img\", \"address\" FROM \"pitch\" WHERE \"location\" = '{location}'").format(sql.Literal(location), sql.Literal(begin_time), sql.Literal(end_time))
    cursor.execute(search_query)
    result = cursor.fetchall()
    pitch_available = []
    if result:
        for pitch in result:
            vacant_shift_dict = convertJsonToDict(pitch[0], begin_time, end_time)
            pitch_info = {"id": pitch[2],"name": pitch[1], "url_img": pitch[3], "address": pitch[4], "intervals": vacant_shift_dict }
            pitch_available.append(pitch_info)
    return pitch_available

def search_pitch_name(connection, cursor, pitch_name, begin_time, end_time):
    print(11111)
    search_query = sql.SQL(f"SELECT \"booked_time\", \"location\", \"id\", \"url_img\" FROM \"pitch\" WHERE \"name\" = '{pitch_name}'").format(sql.Literal(pitch_name), sql.Literal(begin_time), sql.Literal(end_time))
    print(search_query)
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
                pitch_info = {"id": pitch[2],"pitch_location": pitch[1], "img_url": pitch[3]}
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
def update_booked_pitch(connection, cursor, id, begin_time, end_time):
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
        with open('errlog.txt', 'a') as f:
            f.write(str(error) + '\n')
            f.write(str(traceback.format_exc()) + '\n\n\n')
        return "failed"

def create_pending_match(connection, cursor, user_id, pitch_id, booked_time):
    current_time = datetime.now()   
    sql_query = sql.SQL(f"INSERT INTO \"pending_matching\" (user_id, pitch_id, booked_time, pending, created_at) VALUES ({user_id}, '{pitch_id}', '{booked_time}', '1', '{current_time}')").format(sql.Literal(user_id), sql.Literal(pitch_id), sql.Literal(booked_time))
    try:
        cursor.execute(sql_query)
        connection.commit()
        print("Pending match has added to database.")
        return "success"
    except (Exception, psycopg2.Error) as error:
        print("Insert pending match failed: ", error)
        connection.rollback()
        with open('errlog.txt', 'a') as f:
            f.write(str(error) + '\n')
            f.write(str(traceback.format_exc()) + '\n\n\n')
        return "failed"
    
# def findPendingMatch(connection, cursor, location, finding_time):
#     search_query = sql.SQL(f"SELECT \"user_id\", \"pitch_id\",  WHERE \"name\" = '{pitch_name}'").format(sql.Literal(pitch_name), sql.Literal(begin_time), sql.Literal(end_time))


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

def create_user(connection, cursor, psid, name, email, phone):
    current_time = datetime.now()   
    sql_create_user = sql.SQL(f"INSERT INTO \"user\" (psid, name, email, phone, created_at, deleted) VALUES ({psid}, '{name}', '{email}', '{phone}', '{current_time}', '0')").format(sql.Literal(psid), sql.Literal(name), sql.Literal(email), sql.Literal(phone))
    try:
        cursor.execute(sql_create_user)
        connection.commit()
        print("Data has added to database.")
        return "success"
    except (Exception, psycopg2.Error) as error:
        print("Insert user failed: ", error)
        connection.rollback()
        with open('errlog.txt', 'a') as f:
            f.write(str(error) + '\n')
            f.write(str(traceback.format_exc()) + '\n\n\n')
        return "failed"
        


# res = check_shift_available(datetime.datetime.now(), booked_time)
# print(res)


# {"started_time" : 1697815800.0, "ended_time": 1697826600.0}
# print((datetime(2023, 11, 6, 17, 0)).timestamp())
# print((datetime(2023, 11, 6, 20, 0)).timestamp())
# print((datetime(2023, 11, 3, 18, 10)).timestamp())
# print(datetime.fromtimestamp(1698600600.0, tz = None))

def convertJsonToDict(pitchs_booked_time, begin_time, end_time):
    res = []
    list = sortTimeStamp(pitchs_booked_time)
    time_stamps = findVacantTime(list, begin_time, end_time)
    for shift in time_stamps:
        res.append({"start_time": shift[0], "end_time": shift[1]})
    return res

def sortTimeStamp(dict_of_time):
    list_pair_timestamp = []
    print(dict_of_time)
    for dict in dict_of_time:
        list_pair_timestamp.append((dict.get("started_time"), dict.get("ended_time")))
    list_pair_timestamp.sort(key=sortMethod)
    return list_pair_timestamp

def sortMethod(e):
    return(e[0])

def findVacantTime(list_pair_timestamp: list, begin_time: float, end_time: float) -> list:
    shift_available = []
    last = begin_time
    # Remove shift outside interval time
    for i in range(len(list_pair_timestamp)):
        if (last < end_time and last >= begin_time):
            shift_available.append((last, min(end_time, list_pair_timestamp[i][0])))
        last = list_pair_timestamp[i][1]
    print( list_pair_timestamp[-1][1], end_time)
    if len(list_pair_timestamp) and list_pair_timestamp[-1][1] >= begin_time and list_pair_timestamp[-1][1] <= end_time:
        print(":D")
        shift_available.append((list_pair_timestamp[-1][1], end_time))
    return shift_available

# print(datetime.fromtimestamp(1699030800.0, tz = None))
# print(datetime.fromtimestamp(1699041600.0, tz = None))
# print("______")
# print(datetime.fromtimestamp(1699045200.0, tz = None))
# print(datetime.fromtimestamp(1699052400.0, tz = None))
# print("______")
# print(datetime.fromtimestamp(1699120800.0, tz = None))
# print(datetime.fromtimestamp(1699131600.0, tz = None))
# print("____________")


# print(datetime.fromtimestamp(1699041600.0, tz = None))
# print(datetime.fromtimestamp(1699131600.0 , tz = None))