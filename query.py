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


def search_location_pitch(connection, cursor, location, start_time, end_time):
    search_query = sql.SQL(f"SELECT \"booked_time\", \"name\", \"id\", \"url_img\", \"address\" FROM \"pitch\" WHERE \"location\" = '{location}'").format(sql.Literal(location), sql.Literal(start_time), sql.Literal(end_time))
    cursor.execute(search_query)
    result = cursor.fetchall()
    pitch_available = []
    if result:
        for pitch in result:
            full_intervals = pitch[0]
            pending_in_pitch = fetch_pending_interval(cursor, pitch[2]) #pitch[2] is pitch_id
            full_intervals.extend(pending_in_pitch)
            vacant_shift_dict = convertJsonToDict(full_intervals, start_time, end_time)
            pitch_info = {"id": pitch[2],"name": pitch[1], "url_img": pitch[3], "address": pitch[4], "intervals": vacant_shift_dict }
            pitch_available.append(pitch_info)
    return pitch_available

def search_pitch_name(connection, cursor, pitch_name, start_time, end_time):
    search_query = sql.SQL(f"SELECT \"booked_time\", \"location\", \"id\", \"url_img\" FROM \"pitch\" WHERE \"name\" = '{pitch_name}'").format(sql.Literal(pitch_name), sql.Literal(start_time), sql.Literal(end_time))
    cursor.execute(search_query)
    result = cursor.fetchall()
    pitch_available = []
    if result:
        for pitch in result:
            added = True
            for booked_time in pitch[0]: #booked_time is first element of list
                if (end_time >= booked_time['start_time'] and end_time <= booked_time['end_time']) or (start_time >= booked_time['start_time'] and start_time <= booked_time['end_time']):
                    added = False
                    break
            if added:
                pitch_info = {"id": pitch[2],"pitch_location": pitch[1], "img_url": pitch[3]}
                pitch_available.append(pitch_info)
    return pitch_available

def selecttest(connection, cursor, id, start_time):
    select_query_booked = sql.SQL(f"SELECT \"booked_time\" FROM \"pitch\" WHERE \"id\" = {id}").format(sql.Literal(id), sql.Literal(start_time))
    cursor.execute(select_query_booked)
    result = cursor.fetchall()
    return result

def insert_data(connection, cursor, value):
    insert_query = sql.SQL("INSERT INTO host () VALUES ({})").format(sql.Literal(value))
    cursor.execute(insert_query)
    connection.commit()
    print("Data has added to database.")

# Confirm a rival from a pending match list
def confirmRival(connection, cursor, pending_matching_id, psid):
    # Get data from pending match
    get_data_pending_match_query = sql.SQL(f"SELECT \"pitch_id\", \"user_id\", \"interval_time\" FROM \"pending_matching\" WHERE \"id\" = '{pending_matching_id}'").format(sql.Literal(pending_matching_id))
    try: 
        cursor.execute(get_data_pending_match_query)
        data = cursor.fetchall()
        print(f"Data pending match: {data}")
        pitch_id = data[0][0]
        rival_id = data[0][1]
        interval_time = data[0][2]
        start_time = interval_time["start_time"]
        end_time = interval_time["end_time"]
    except (Exception, psycopg2.Error) as error:
        print("Pending matching id invalid, get data failed: ", error)
        connection.rollback()
        with open('errlog.txt', 'a') as f:
            f.write(str(error) + '\n')
            f.write(str(traceback.format_exc()) + '\n\n\n')
        return "failed"
    
    user_id_confirm = get_user_id_from_psid(cursor, psid)
    if (type(user_id_confirm) != int):
        return user_id_confirm

    res = update_booked_pitch(connection, cursor, pitch_id, start_time, end_time)
    if (res == "failed"):
        return "Add booked time to pitch failed"
    
    #Soft delete in pending matching table
    soft_delete_sql = sql.SQL(f"UPDATE \"pending_matching\" SET \"pending\" = '0' WHERE \"id\" = {pending_matching_id}")
    try:
        cursor.execute(soft_delete_sql)
        connection.commit() 
        print("Soft delete pending matching record.")
    except (Exception, psycopg2.Error) as error:
        print("Delete pending matching failed: ", error)
        connection.rollback()
        with open('errlog.txt', 'a') as f:
            f.write(str(error) + '\n')
            f.write(str(traceback.format_exc()) + '\n\n\n')
        return "Delete pending matching failed!"

    current_time = datetime.now()
    json_time = json.dumps(interval_time)
    print(json_time)
    create_pairing_match_query = sql.SQL(f"INSERT INTO \"pairing_match\" (user_book_match_id, user_pending_id, pitch_id, interval_match, created_at) VALUES ({user_id_confirm}, {rival_id}, {pitch_id}, '{json_time}', '{current_time}')")
    try:
        cursor.execute(create_pairing_match_query)
        connection.commit() 
        print("Pairing match has added to database.")
        return "success"
    except (Exception, psycopg2.Error) as error:
        print("Insert pending match failed: ", error)
        connection.rollback()
        with open('errlog.txt', 'a') as f:
            f.write(str(error) + '\n')
            f.write(str(traceback.format_exc()) + '\n\n\n')
        return "Insert pairing match failed!"

    # try:
    #     update_booked_pitch(connection, cursor, id, )


def get_rival_info(connection, cursor, pending_matching_id):
    get_user_id_query = sql.SQL(f"SELECT \"user_id\" FROM \"pending_matching\" WHERE \"id\" = '{pending_matching_id}'").format(sql.Literal(pending_matching_id))
    try: 
        cursor.execute(get_user_id_query)
        data = cursor.fetchall()
        print(f"Data pending match: {data}")
        rival_id = data[0][0]
    except (Exception, psycopg2.Error) as error:
        print("Pending matching id is invalid, get user_id failed: ", error)
        connection.rollback()
        with open('errlog.txt', 'a') as f:
            f.write(str(error) + '\n')
            f.write(str(traceback.format_exc()) + '\n\n\n')
        return "failed"

    get_user_psid_query = sql.SQL(f"SELECT \"psid\" FROM \"user\" WHERE \"id\" = '{rival_id}'").format(sql.Literal(rival_id))
    try: 
        cursor.execute(get_user_psid_query)
        data = cursor.fetchall()
        print(f"Data pending match: {data}")
        rival_psid = data[0][0]
        return rival_psid
    except (Exception, psycopg2.Error) as error:
        print("User id is invalid, get user_psid failed: ", error)
        connection.rollback()
        with open('errlog.txt', 'a') as f:
            f.write(str(error) + '\n')
            f.write(str(traceback.format_exc()) + '\n\n\n')
        return "failed"
    
# shift time is a dict like item in booked_time
def update_booked_pitch(connection, cursor, id, start_time, end_time):
    json_shift = {'start_time' : start_time, 'end_time': end_time}
    # query booked_time currently
    select_query_booked = sql.SQL(f"SELECT \"booked_time\" FROM \"pitch\" WHERE \"id\" = {id}").format(sql.Literal(id), sql.Literal(start_time), sql.Literal(end_time))
    cursor.execute(select_query_booked)
    old_booked_time = cursor.fetchall()

    # update booked_time
    try:
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
    
def get_user_id_from_psid(cursor, psid):
    get_user_id_query = sql.SQL(f"SELECT id FROM \"user\" WHERE psid = '{psid}'")
    try: 
        cursor.execute(get_user_id_query)
        user_id = int(cursor.fetchall()[0][0])
        print(f"User id: {user_id}")
        return user_id
    except (Exception, psycopg2.Error) as error:
        print("Query user id failed: ", error)
        with open('errlog.txt', 'a') as f:
            f.write(str(error) + '\n')
            f.write(str(traceback.format_exc()) + '\n\n\n')
        return "Query user id failed"

def create_pending_match(connection, cursor, psid, pitch_id, interval_time):
    # check user exist
    user_id = get_user_id_from_psid(cursor, psid)
    if (type(user_id) != int):
        return user_id
    #check interval valid
    try:
        begin_interval = interval_time['start_time']
        end_interval = interval_time['end_time']    
        full_interval_pitch = fetch_pending_interval(cursor, pitch_id)
        print(full_interval_pitch)
        if len(full_interval_pitch) > 0:
            vacant_shift_dict = convertJsonToDict(full_interval_pitch, begin_interval, end_interval)
            if len(vacant_shift_dict) != 1 or vacant_shift_dict[0]['start_time'] != begin_interval or vacant_shift_dict[0]['end_time'] != end_interval:
                return "Your interval is preempted"
    except (Exception, psycopg2.Error) as error:
        print("Your interval is preempted: ", error)
        connection.rollback()
        with open('errlog.txt', 'a') as f:
            f.write(str(error) + '\n')
            f.write(str(traceback.format_exc()) + '\n\n\n')
        return "Error with intervals"

    
    current_time = datetime.now().timestamp() 
    json_interval = json.dumps(interval_time)
    sql_query = sql.SQL(f"INSERT INTO \"pending_matching\" (user_id, pitch_id, interval_time, pending, created_at) VALUES ({user_id}, {pitch_id}, '{json_interval}', '1', to_timestamp({current_time}))")


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
        return "User doesn't exist in database!"
    
# def findPendingMatch(connection, cursor, location, finding_time):
#     search_query = sql.SQL(f"SELECT \"user_id\", \"pitch_id\",  WHERE \"name\" = '{pitch_name}'").format(sql.Literal(pitch_name), sql.Literal(start_time), sql.Literal(end_time))


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
        if (finding_time> shift.get("start_time") and finding_time < shift.get("end_time")):
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

def findIntervalPitch(connection, cursor, start_time, end_time, pitch_id):
    fetch_sql = sql.SQL(f"SELECT interval_time, id from pending_matching where pitch_id = {pitch_id} and pending = '1'")
    cursor.execute(fetch_sql)
    result = cursor.fetchall()
    within_interval = []
    outside_interval = []
    if result:
        # interval_time < min time of a match
        for interval_time in result:
            interval_time[0]['pending_matching_id']  = interval_time[1]
            if float(interval_time[0]['end_time']) < float(start_time) or float(interval_time[0]['start_time']) > float(end_time):
                outside_interval.append((interval_time[0]))
            else:
                within_interval.append((interval_time[0]))
    return (within_interval, outside_interval)




# {"started_time" : 1697815800.0, "ended_time": 1697826600.0}
# print((datetime(2023, 11, 6, 17, 0)).timestamp())
# print((datetime(2023, 11, 6, 12, 0)).timestamp())
# print((datetime(2023, 11, 6, 23, 10)).timestamp())
# print(datetime.fromtimestamp(1698600600.0, tz = None))

def fetch_pending_interval(cursor, pitch_id): 
    fetch_pending_intervals_query = sql.SQL(f"SELECT interval_time from pending_matching where pitch_id = {pitch_id} and pending = '1'")
    cursor.execute(fetch_pending_intervals_query)
    result = cursor.fetchall()
    start_end_time = []
    for interval in result:
        start_end_time.append(interval[0])
    return start_end_time


def convertJsonToDict(pitchs_booked_time, start_time, end_time):
    res = []
    list = []
    if (len(pitchs_booked_time) > 1):
        list = sortTimeStamp(pitchs_booked_time)
    else:
        list = [(pitchs_booked_time[0]['start_time'], pitchs_booked_time[0]['end_time'])]
    time_stamps = findVacantTime(list, start_time, end_time)
    for shift in time_stamps:
        res.append({"start_time": shift[0], "end_time": shift[1]})
    return res

def sortTimeStamp(dict_of_time):
    list_pair_timestamp = []
    for dict in dict_of_time:
        list_pair_timestamp.append((dict.get("start_time"), dict.get("end_time")))
    list_pair_timestamp.sort(key=sortMethod)
    return list_pair_timestamp

def sortMethod(e):
    return(e[0])

def findVacantTime(list_pair_timestamp: list, start_time: float, end_time: float) -> list:
    shift_available = []
    # Check whether loop into intervals or not
    flag = False
    appendLastIn = False
    # Remove shift outside interval time
    for i in range(len(list_pair_timestamp)):
        if (list_pair_timestamp[i][0] >= end_time):
            if appendLastIn == True and start_time < end_time:
                shift_available.append((start_time, end_time))
            continue
        if (list_pair_timestamp[i][1] <= start_time):
            continue
        if (list_pair_timestamp[i][1] > start_time and list_pair_timestamp[i][0] < start_time):
            flag = True
            start_time = list_pair_timestamp[i][1]
        if (list_pair_timestamp[i][0] > start_time):
            appendLastIn = True
            shift_available.append((start_time, list_pair_timestamp[i][0]))
            start_time = list_pair_timestamp[i][1]
        if (start_time >= end_time):
            break

    if len(shift_available) == 0 and flag == False:
        shift_available.append((start_time, end_time))
    return shift_available



# def confirmOpponent()

# print((datetime(2023, 12, 6, 17, 0)).timestamp())
# print((datetime(2023, 12, 6, 19, 0)).timestamp())
# print(datetime.fromtimestamp(1699012800.0, tz = None))
# print(datetime.fromtimestamp(1699055940.0, tz = None))


# print(datetime.fromtimestamp(1699030800.0, tz = None))
# print(datetime.fromtimestamp(1699041600.0, tz = None))
# print(datetime.fromtimestamp(1699045200.0, tz = None))
# print(datetime.fromtimestamp(1699052400.0, tz = None))
# print(datetime.fromtimestamp(1699120800.0, tz = None))
# print(datetime.fromtimestamp(1699131600.0, tz = None))
# print("___________")
# print(datetime.fromtimestamp(1699012800.0, tz = None))
# print(datetime.fromtimestamp(1699030800.0, tz = None))
# print(datetime.fromtimestamp(1699041600.0, tz = None))
# print(datetime.fromtimestamp(1699045200.0, tz = None))

# print(datetime.fromtimestamp(1699474962.0, tz = None))

# print("______")
# print(datetime.fromtimestamp(1700193494.472, tz = None))
# print(datetime.fromtimestamp(1699052400.0, tz = None))
# print("______")
# print(datetime.fromtimestamp(1700654400.0, tz = None))
# print(datetime.fromtimestamp(1699131600.0, tz = None))
# print("____________")


# print(datetime.fromtimestamp(1699041600.0, tz = None))
# print(datetime.fromtimestamp(1699131600.0 , tz = None))