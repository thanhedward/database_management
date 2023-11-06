import fastapi, traceback
from fastapi import BackgroundTasks, FastAPI, Request, Response, HTTPException, Query
from query import *
from config import config
import json
import datetime
import psycopg2
import uvicorn
from settings import *

app = FastAPI()


try:
    params = config()
    connection = psycopg2.connect(**params, keepalives=1, keepalives_idle=30, keepalives_interval=10,keepalives_count=5)
    cursor = connection.cursor()
    print("Connect successfully!")
    print('PostgreSQL database version:')
    cursor.execute('SELECT version()')
    db_version = cursor.fetchone()
    print(db_version)
    # print(selecttest(connection, cursor, 1, float(12312312.0)))
    # time_booked_pitch = datetime.datetime(2023, 11, 1, 20, 30).timestamp()
    # update_data(connection, cursor, 1, time_booked_pitch)
    # print(selecttest(connection, cursor, 1))
    # res = search_data(connection, cursor, "My Dinh", 1701281400.0)
    # for item in res:
    #       print(item[0])
    # print(res[0][0][0]['started_time'])
    # print(res)

    # Query database
except (Exception, psycopg2.Error) as error:
    with open('errlog.txt', 'a') as f:
                f.write(str(error) + '\n')
                f.write(str(traceback.format_exc()) + '\n\n\n')
    print("Error when connecting to database:", error)



@app.get("/findByLocationTime/")
async def get(request: Request):
    query_params = request.query_params
    location = query_params.get("location")
    start_time = query_params.get("start_time")
    end_time = query_params.get("end_time")
    pitch = search_location_pitch(connection, cursor, location, float(start_time), float(end_time))
    if len(pitch) != 0:
          return Response(status_code=200, content=json.dumps(pitch))
    return Response(status_code=200, content=json.dumps([]))

@app.get("/findByPitchNameTime/")
async def get(request: Request):
    query_params = request.query_params
    pitch_name = query_params.get("pitch_name")
    start_time = query_params.get("start_time")
    end_time = query_params.get("end_time")
    pitch = search_pitch_name(connection, cursor, pitch_name, float(start_time), float(end_time))
    if len(pitch) != 0:
          return Response(status_code=200, content=json.dumps(pitch))
    return Response(status_code=200, content=json.dumps([]))

    
@app.post("/confirmBookedPitch/")
async def get(request: Request):
    output = await request.json()
    id = output['id']
    start_time = output['start_time']
    end_time = output['end_time']
    res = update_booked_pitch(connection, cursor, int(id), float(start_time), float(end_time))
    if res == "success":
          return Response(status_code=200, content=json.dumps(string_to_json_form("Updated")))
    respone_failed = f"My database doesn't have pitch with id: {id}"
    return Response(status_code=200, content=json.dumps(string_to_json_form(respone_failed)))

@app.post("/createUser")
async def get(request: Request):
    output = await request.json()
    psid = output['psid']
    name = output['name']
    if 'email' in output:
        email = output['email']
    else: 
        email = None
    if 'phone' in output:
        phone = output['phone']
    else:
        phone = None
    res = create_user(connection, cursor, psid, name, email, phone)
    if res == "success":
        return Response(status_code=200, content=json.dumps(string_to_json_form("success!")))
    else:
        return Response(status_code=200, content=json.dumps(string_to_json_form("User has imported before or doesn't have enough required field!")))

@app.post("/createPendingMatch/")
async def get(request: Request):
    output = await request.json()
    psid = output['psid']
    pitch_id = output['pitch_id']
    interval_time = output['interval_time']
    res = create_pending_match(connection, cursor, psid, pitch_id, interval_time)
    if res == "success":
        return Response(status_code=200, content=json.dumps(string_to_json_form("success!")))
    else:
        return Response(status_code=200, content=json.dumps(string_to_json_form(res)))
    
@app.get("/findIntervalsWithPitchID")
async def get(request: Request):
    query_params = request.query_params
    start_time = query_params.get('start_time')
    end_time = query_params.get('end_time')
    pitch_id = query_params.get("pitch_id")
    if float(end_time) - float(start_time) < settings.min_time_match:
         return Response(status_code=200, content=json.dumps(string_to_json_form("Interval times must be longer 45 minutes")))
    intervals = findIntervalPitch(connection, cursor, start_time, end_time, pitch_id)
    respone_dict = {"within_intervals": intervals[0], "outside_intervals": intervals[1]}
    return Response(status_code=200, content=json.dumps(respone_dict))

# TODO: join pitch table and user table to pending match

def string_to_json_form(str):
      return {"message": str}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8200, reload=True)
