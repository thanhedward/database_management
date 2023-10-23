import fastapi, traceback
from fastapi import BackgroundTasks, FastAPI, Request, Response, HTTPException, Query
from query import *
from config import config
import psycopg2

app = FastAPI()


try:
    params = config()
    connection = psycopg2.connect(**params)
    cursor = connection.cursor()
    print("Connect successfully!")
    print('PostgreSQL database version:')
    cursor.execute('SELECT version()')
    db_version = cursor.fetchone()
    print(db_version)

    # Query database
except (Exception, psycopg2.Error) as error:
    with open('errlog.txt', 'a') as f:
                f.write(str(error) + '\n')
                f.write(str(traceback.format_exc()) + '\n\n\n')
    print("Error when connecting to database:", error)


@app.get("/findByLocationTime/")
async def get(request: Request):
    query_params = request.query_params
    location = query_params.get("location") # fake
    shift = query_params.get("shift") # fake
    date = query_params.get("date")
    pitch = search_data(connection, cursor, location, date, shift)
    return pitch

# @app.get

# @app.post("/logInfoMatch/")
# async def get(request: Request):
    
