from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pymysql

app = FastAPI()

#vehicle class defined as model for automatic JSON import.
class VehicleModel(BaseModel):
    vehicle_id: int = Field(ge=1)
    speed: int = Field(ge=0, le=160)
    engine_temp: int = Field(ge=0, le=150)
    fuel_level: int = Field(ge=0, le=100)

#AWS RDS DB CREDS.
DB_HOST = "testfleet.cr284oi8q9mz.ap-southeast-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASSWORD = "PCBuild202"
DB_NAME = "fleet_db"
DB_PORT = 3306

#connect to AWS RDS DB.
def db_connect():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        database=DB_NAME,
        password=DB_PASSWORD,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )

#Check vehicle table exists and create if needed.
@app.on_event("startup")
def innit_db():
    try:
        conn = db_connect()
        with conn.cursor() as cursor:
            statement = """ 
            CREATE TABLE IF NOT EXISTS vehicle 
                (vehicle_id INT PRIMARY KEY,
                speed INT,
                engine_temp INT,
                fuel_level INT);
             """
            cursor.execute(statement)
        conn.commit()
        print("Table Ready: vehicle")
    except:
        raise HTTPException(status_code=500, detail="Table: vehicle - init failed.")
    finally:
        conn.close()


#Root page returns full fleet details.
@app.get("/")
def root():
    return NULL

#Retrieve details for a specific vehicle by vehicle id.
@app.get("/vehicle/{vehicle_id}")
def vehicle_search(vehicle_id: int):
    for v in fleet:
        if v["vehicle_id"] == vehicle_id:
            return v
    raise HTTPException(status_code=404, detail="Vehicle not found")

@app.post("/vehicle/new/")
def add_vehicle(new_vehicle: VehicleModel):
    
    #Get vehicle table.
    qstatement = "SELECT * FROM vehicle"
    try:
        conn = db_connect()
        with conn.cursor() as cursor:
            cursor.execute(qstatement)
            v_table = cursor.fetchall()

            #Check new vehicle id is not already in vehicle table.
            #If new vehicle id is not unique: raise exception.
            #If new vehicle id is unqiue: add new vehicle to DB.
            for v in v_table:
                if v["vehicle_id"] == new_vehicle.vehicle_id:
                    raise HTTPException(status_code=400,detail="Vehicle already in DB")

            qstatement = """
                INSERT INTO vehicle(vehicle_id, speed, engine_temp, fuel_level) 
                VALUES(%s,%s,%s,%s)
                """

            vehicle_tuple = (
                new_vehicle.vehicle_id,
                new_vehicle.speed,
                new_vehicle.engine_temp,
                new_vehicle.fuel_level
            )

            cursor.execute(qstatement, vehicle_tuple)
            print (f"Vehicle Added: {new_vehicle}")

            #Commit DB changes. 
            conn.commit()
    except HTTPException: raise
    except Exception: 
        raise HTTPException(status_code=500, detail="Could not connect or write to DB")
    #Close DB connection. 
    finally: 
        conn.close()
    



    
