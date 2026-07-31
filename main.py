from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pymysql
import time

app = FastAPI(title="Fleet Management API")

#vehicle class defined as model for automatic JSON import.
#Requires refactoring or review
class VehicleModel(BaseModel):
    vehicle_id: int = Field(ge=1)
    speed: float = Field(ge=0, le=160)
    latitude: float
    longitude: float

#DB Creds
DB_HOST = "testfleet.cr284oi8q9mz.ap-southeast-2.rds.amazonaws.com"
DB_USER = "admin"
DB_PASSWORD = "PCBuild202"
DB_NAME = "fleet_db"
DB_PORT = 3306

#connect to DB.
def db_connect():
    try:
        return pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            database=DB_NAME,
            password=DB_PASSWORD,
            port=DB_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e: raise HTTPException(status_code=500, detail="Failed to connect to DB")

#Check vehicle table exists and create if needed.
@app.on_event("startup")
def innit_db():
    try:
        with db_connect() as conn:
            with conn.cursor() as cursor:
                query = """ 
                CREATE TABLE IF NOT EXISTS vehicle 
                    (vehicle_id INT PRIMARY KEY,
                    speed float,
                    latitude float,
                    longitude float);
                """
                cursor.execute(query)
            conn.commit()
            print("Table Ready: vehicle")
    except HTTPException: raise HTTPException(status_code=500, detail="Table: vehicle - init failed.")
    #Exception catch-all
    except Exception as e: raise HTTPException(status_code=500, detail="Startup Error")

#API Health check on root endpoint
@app.get("/", status_code=200)
def root():
    return {"Status":"Healthy", "Message":"Vehicle API is running | Check /docs for testing and /redoc for read-only documentation"}

#Returns entire fleet in DB for quick browsing
@app.get("/vehicle", status_code=200)
def browse_vehicles():
    query = "SELECT * FROM vehicle ORDER BY vehicle_id ASC"
    try:
        with db_connect() as conn:
            with conn.cursor() as cursor:
                    cursor.execute(query)
                    return cursor.fetchall()
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail="Could not retrieve database records.")

#Retrieve details for a specific vehicle by vehicle id.
@app.get("/vehicle/{vehicle_id}", status_code=200)
def vehicle_search(vehicle_id: int):
    #SQL Query
    check_sql = "SELECT * FROM vehicle WHERE vehicle_id = %s"
    try:
        with db_connect() as conn:
            with conn.cursor() as cursor:
                #Fetch record if it exists
                cursor.execute(check_sql, (vehicle_id,))
                vehicle = cursor.fetchone()
                #If record does not exist, return 404 error, else return record.
                if not vehicle:
                    raise HTTPException(status_code=404, detail="Vehicle not found.")
                return vehicle
    #Reraise HTTPException if triggered.
    except HTTPException: raise
    #Exception catch-all
    except Exception as e: raise HTTPException(status_code=500, detail="DB Error")

@app.post("/vehicle/new/", status_code=201)
def add_vehicle(new_vehicle: VehicleModel):
    #SQL queries
    check_sql = "SELECT 1 FROM vehicle WHERE vehicle_id = %s"
    insert_sql = """
        INSERT INTO vehicle (vehicle_id, speed, latitude, longitude)
        VALUES (%s, %s, %s, %s)
    """
    try:
        with db_connect() as conn:
            with conn.cursor() as cursor:
                #Check in DB for existing vehicle record. If exists then raise exception.
                cursor.execute(check_sql, (new_vehicle.vehicle_id,))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Vehicle already in DB")
                #If vehicle check passes, send insert query and commit DB addition.
                cursor.execute(insert_sql, (
                    new_vehicle.vehicle_id,
                    new_vehicle.speed,
                    new_vehicle.latitude,
                    new_vehicle.longitude
                ))
                conn.commit()
        return {"message": f"Vehicle {new_vehicle.vehicle_id} was added successfully."}
    #Reraise HTTP exception if triggered.
    except HTTPException: raise
    #Exception catch-all
    except Exception as e: raise HTTPException(status_code=500, detail="DB Error")

#Remove vehicle from fleet if it exists
@app.delete("/vehicle/{vehicle_id}", status_code=200)
def remove_vehicle(vehicle_id: int):
    delete_sql = "DELETE FROM vehicle WHERE vehicle_id = %s"
    try:
        with db_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(delete_sql, (vehicle_id,))
                #check if any rows were affected to confirm if deletion took
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Vehicle not found.")
                conn.commit()
        return {"message":"Vehicle Deleted", "Vehicle ID":vehicle_id}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail="DB Error")

#Modify vehicle if it exists
@app.put("/vehicle/update/", status_code=200)
def update_vehicle(vehicle: VehicleModel):
    query = """ 
        UPDATE vehicle
        SET speed = %s, latitude = %s, longitude = %s
        WHERE vehicle_id = %s
     """
    try:
        with db_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (vehicle.speed, vehicle.latitude, vehicle.longitude, vehicle.vehicle_id))
                #check if query affected DB
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Could not update record. Check payload format or if vehicle exists.")
                conn.commit()
        return {"message":f"Vehicle with ID {vehicle.vehicle_id} updated successfully"}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail="DB Error")

@app.get("/stress/", status_code=200)
def api_stress_test(iterations: int = 10_000_000):
    start_time = time.time()

    #Simple calculation to create CPU load
    total = 0
    for i in range(0,iterations):
        total += i*i
    
    #Get total run-time as clean round number
    execution_time = round((time.time() - start_time), 4)

    return {
        "status":"completed",
        "iterations":iterations,
        "execution_time_seconds":execution_time
    }