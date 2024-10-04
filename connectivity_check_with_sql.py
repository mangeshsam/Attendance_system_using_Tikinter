import psycopg2

hostname = '127.0.0.1'
database = "postgres"
username = "postgres"
pwd = "admin123"
port = 5432
connection = None
cur = None

try:
    # Establishing the connection
    connection = psycopg2.connect(
        host=hostname,
        database=database,
        user=username,
        password=pwd,
        port=port
    )
    cur = connection.cursor()
    
    print("Connection to the PostgreSQL database established successfully.")

    # Create the students table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id_student SERIAL PRIMARY KEY,  -- Use SERIAL for auto-increment
        name TEXT NOT NULL,
        batch TEXT NOT NULL
    );
    ''')

    # Create the attendance table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id_student INTEGER,
        name TEXT,
        date DATE,  -- Use DATE type for date
        time TIME,  -- Use TIME type for time
        batch TEXT,
        status TEXT,
        FOREIGN KEY (id_student) REFERENCES students (id_student)
    );
    ''')

    # Commit changes
    connection.commit()

except Exception as e:
    # Handle the error if any exception occurs
    print(f"An error occurred while connecting to the database: {e}")

finally:
    if cur is not None:
        cur.close()
    if connection is not None:
        connection.close()
