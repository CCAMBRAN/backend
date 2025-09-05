from flask_mysqldb import MySQL
import os
from dotenv import load_dotenv

load_dotenv()

mysql = MySQL() # Initialize MySQL instance

def init_db (app):
    # Configure MySQL connection using environment variables
    app.config['MYSQL_HOST'] = os.getenv('DB_HOST')
    app.config['MYSQL_USER'] = os.getenv('DB_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('DB_NAME')  # Replace with your database name
    app.config['MYSQL_PORT'] = int(os.getenv('DB_PORT', 3306))  # Default to 3306 if not set

    mysql.init_app(app)  # Initialize MySQL with the Flask app

def get_db_connection():
    try:
        connection = mysql.connection
        return connection.cursor()
    except Exception as e:
        raise Exception(f"Error connecting to the database: {e}")
        