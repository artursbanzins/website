from flask import Flask, render_template
import sqlite3
from pathlib import Path

app = Flask(__name__)

def get_db_connection():

    db = Path(__file__).parent / "database.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def sakums():
    return render_template("home.html")

@app.route("/sludinajumi")
def sludinajumi():
    conn = get_db_connection()
    sludinajumi = conn.execute("""
        SELECT sludinajumi.*, manufacturers.name AS manufacturer_name FROM sludinajumi
        JOIN manufacturers
        ON sludinajumi.manufacturer_id = manufacturers.id
        WHERE sludinajumi.quality = 2
        """).fetchall()
    conn.close()
    return render_template("sludinajumi.html", sludinajumi=sludinajumi)

@app.route("/luxus-auto")
def luxus_auto():
    conn = get_db_connection()
    sludinajumi = conn.execute("SELECT * FROM sludinajumi WHERE quality = 2").fetchall()
    conn.close()
    return render_template("sludinajumi.html", sludinajumi=sludinajumi)

if __name__ == "__main__":
    app.run(debug=True, port=5001)