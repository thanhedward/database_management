import fastapi, traceback
from fastapi import BackgroundTasks, FastAPI, Request, Response, HTTPException, Query
from query import *
from config import config
import json
import datetime
import psycopg2


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
    print(selecttest(connection, cursor, 1, float(12312312.0)))
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
    begin_time = query_params.get("begin_time")
    end_time = query_params.get("end_time")
    pitch = search_data(connection, cursor, location, float(begin_time), float(end_time))
    if len(pitch) != 0:
          return Response(status_code=200, content=json.dumps(pitch))
    return Response(status_code=200, content="No pitch available!")


    
@app.post("/confirmBookedPitch/")
async def get(request: Request):
    output = await request.json()
    id = output['id']
    begin_time = output['begin_time']
    end_time = output['end_time']
    res = update_data(connection, cursor, int(id), float(begin_time), float(end_time))
    if res == "success":
          return Response(status_code=200, content="Updated")
    return Response(status_code=200, content=f"My database doesn't have pitch with id: {id}")