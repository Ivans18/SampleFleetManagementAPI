from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pymysql

app = FastAPI()

#vehicle class defined as model for automatic JSON import.
#Requires refactoring or review
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
#Requires refactoring
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
    return 0

#Retrieve details for a specific vehicle by vehicle id.
#Requires refactoring
@app.get("/vehicle/{vehicle_id}")
def vehicle_search(vehicle_id: int):
    for v in fleet:
        if v["vehicle_id"] == vehicle_id:
            return v
    raise HTTPException(status_code=404, detail="Vehicle not found")

@app.post("/vehicle/new/", status_code=201)
def add_vehicle(new_vehicle: VehicleModel):
    # SQL queries
    # Parameterization for SQL injection protection
    check_sql = "SELECT 1 FROM vehicle WHERE vehicle_id = %s"
    insert_sql = """
        INSERT INTO vehicle (vehicle_id, speed, engine_temp, fuel_level)
        VALUES (%s, %s, %s, %s)
    """

    try:
        with db_connect() as conn:
            with conn.cursor() as cursor:

                # Check in DB for existing vehicle record. If exists then raise exception.
                cursor.execute(check_sql, (new_vehicle.vehicle_id,))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Vehicle already in DB")

                # If vehicle check passes, send insert query and commit DB addition.
                cursor.execute(insert_sql, (
                    new_vehicle.vehicle_id,
                    new_vehicle.speed,
                    new_vehicle.engine_temp,
                    new_vehicle.fuel_level
                ))
                conn.commit()
        return {"message": f"Vehicle {new_vehicle.vehicle_id} was added successfully."}
    
    # reraise HTTP exception if triggered.
    except HTTPException:
        raise

    # Exception catch-all
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not connect or write to DB")

    
    



    
