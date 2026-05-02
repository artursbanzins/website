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
    conn = get_db_connection()
    sludinajumi = conn.execute("""
        SELECT sludinajumi.*, manufacturers.name AS manufacturer_name FROM sludinajumi
        JOIN manufacturers
        ON sludinajumi.manufacturer_id = manufacturers.id
        WHERE quality = 2 OR quality = 3
        """
        ).fetchall()
    conn.close()
    return render_template("home.html", sludinajumi=sludinajumi)

@app.route("/<quality_name>")
def sludinajumi(quality_name):
    conn = get_db_connection()
    sludinajumi = conn.execute("""
        SELECT sludinajumi.*, qualities.quality_name, manufacturers.name AS manufacturer_name FROM sludinajumi
        JOIN manufacturers
        ON sludinajumi.manufacturer_id = manufacturers.id
        JOIN qualities
        ON sludinajumi.quality = qualities.id
        WHERE qualities.quality_name = ?
        """,
        (quality_name,),
        ).fetchall()
    conn.close()
    return render_template("category.html", sludinajumi=sludinajumi)

if __name__ == "__main__":
    app.run(debug=True, port=5001)