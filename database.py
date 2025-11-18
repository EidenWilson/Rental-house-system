import sqlite3

# Define the database name
DB_NAME = 'rental.db'

def create_db():
    """Creates the database tables from the schema.sql file."""
    
    # Connect to the database (this will create the file if it doesn't exist)
    conn = sqlite3.connect(DB_NAME)
    
    print(f"Database '{DB_NAME}' created.")
    
    # Create a cursor object to execute SQL
    cursor = conn.cursor()
    
    # Read the SQL commands from the schema.sql file
    with open('schema.sql', 'r') as f:
        sql_script = f.read()
        
    # Execute the entire script
    cursor.executescript(sql_script)
    
    print("Tables created and sample data inserted.")
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_db()