from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pathlib import Path
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / "static" / "images"
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'webp'}

def get_db_connection():
    db = Path(__file__).parent / "database.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/")
def sakums():
    conn = get_db_connection()
    sludinajumi = conn.execute("""
        SELECT sludinajumi.*, qualities.quality_name, manufacturers.name AS manufacturer_name FROM sludinajumi
        JOIN manufacturers ON sludinajumi.manufacturer_id = manufacturers.id
        JOIN qualities ON sludinajumi.quality = qualities.id
        WHERE quality = 2 OR quality = 3
        ORDER BY sludinajumi.id DESC
        LIMIT 6
        """).fetchall()
    conn.close()
    return render_template("home.html", sludinajumi=sludinajumi)

@app.route("/<quality_name>")
def kategorijas(quality_name):
    conn = get_db_connection()
    sludinajumi = conn.execute("""
        SELECT sludinajumi.*, qualities.*, manufacturers.name AS manufacturer_name FROM sludinajumi
        JOIN manufacturers ON sludinajumi.manufacturer_id = manufacturers.id
        JOIN qualities ON sludinajumi.quality = qualities.id
        WHERE qualities.quality_name = ?
        """, (quality_name,)).fetchall()
    quality = conn.execute("SELECT * FROM qualities WHERE quality_name = ?", (quality_name,)).fetchone()
    conn.close()
    return render_template("category.html", sludinajumi=sludinajumi, quality=quality)

@app.route("/<quality_name>/<int:sludinajums_id>")
def sludinajums(quality_name, sludinajums_id):
    conn = get_db_connection()
    sludinajums = conn.execute("""
        SELECT sludinajumi.*, qualities.quality_name, manufacturers.name AS manufacturer_name,
            engine.type AS engine_type, engine.fuel, engine.size, engine.power, engine.extra_info
        FROM sludinajumi
        JOIN manufacturers ON sludinajumi.manufacturer_id = manufacturers.id
        JOIN qualities ON sludinajumi.quality = qualities.id
        LEFT JOIN engine ON sludinajumi.engine_id = engine.id
        WHERE qualities.quality_name = ?
        AND sludinajumi.id = ?
        """, (quality_name, sludinajums_id)).fetchone()
    conn.close()
    return render_template("listing.html", sludinajums=sludinajums)

# ── CREATE ─────────────────────────────────────────────────────────────────────
@app.route("/ievietot", methods=["GET", "POST"])
def ievietot():
    conn = get_db_connection()
    manufacturers = conn.execute("SELECT * FROM manufacturers").fetchall()
    qualities = conn.execute("SELECT * FROM qualities").fetchall()

    if request.method == "POST":
        model       = request.form["model"]
        price       = request.form["price"]
        year        = request.form["year"]
        quality_id  = request.form["quality"]

        # Manufacturer — existing or new "other"
        manufacturer_id = request.form.get("manufacturer_id")
        other_name      = request.form.get("manufacturer_other", "").strip()

        if manufacturer_id == "other" and other_name:
            cur = conn.execute("INSERT INTO manufacturers (name) VALUES (?)", (other_name,))
            manufacturer_id = cur.lastrowid
        
        # Image upload
        image_name = "placeholder"
        file = request.files.get("image")
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            # Use manufacturer + model as filename, sanitized
            raw_name = f"{other_name or dict(next(m for m in manufacturers if str(m['id']) == str(manufacturer_id)))['name']}_{model}".replace(" ", "_")
            image_name = secure_filename(raw_name)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{image_name}.{ext}"))
            image_name = f"{image_name}"  # stored without extension to match existing convention

        conn.execute("""
            INSERT INTO sludinajumi (model, price, image, year, quality, manufacturer_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (model, price, image_name, year, quality_id, manufacturer_id))
        conn.commit()
        conn.close()

        # Redirect to the correct category page
        quality_name = dict(next(q for q in qualities if str(q['id']) == str(quality_id)))['quality_name']
        return redirect(url_for('kategorijas', quality_name=quality_name))

    conn.close()
    return render_template("addlisting.html", manufacturers=manufacturers, qualities=qualities)

# ── UPDATE ─────────────────────────────────────────────────────────────────────
@app.route("/<quality_name>/<int:sludinajums_id>/labot", methods=["GET", "POST"])
def labot(quality_name, sludinajums_id):
    conn = get_db_connection()
    manufacturers = conn.execute("SELECT * FROM manufacturers").fetchall()
    qualities = conn.execute("SELECT * FROM qualities").fetchall()
    sludinajums = conn.execute("""
        SELECT sludinajumi.*, qualities.quality_name FROM sludinajumi
        JOIN qualities ON sludinajumi.quality = qualities.id
        WHERE sludinajumi.id = ?
        """, (sludinajums_id,)).fetchone()

    if request.method == "POST":
        model      = request.form["model"]
        price      = request.form["price"]
        year       = request.form["year"]
        quality_id = request.form["quality"]

        manufacturer_id = request.form.get("manufacturer_id")
        other_name      = request.form.get("manufacturer_other", "").strip()

        if manufacturer_id == "other" and other_name:
            cur = conn.execute("INSERT INTO manufacturers (name) VALUES (?)", (other_name,))
            manufacturer_id = cur.lastrowid

        # Image — only update if a new file was uploaded
        image_name = sludinajums["image"]
        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            raw_name = f"{other_name or dict(next(m for m in manufacturers if str(m['id']) == str(manufacturer_id)))['name']}_{model}".replace(" ", "_")
            image_name = secure_filename(raw_name)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], f"{image_name}.{ext}"))

        conn.execute("""
            UPDATE sludinajumi
            SET model=?, price=?, image=?, year=?, quality=?, manufacturer_id=?
            WHERE id=?
            """, (model, price, image_name, year, quality_id, manufacturer_id, sludinajums_id))
        conn.commit()
        conn.close()

        new_quality_name = dict(next(q for q in qualities if str(q['id']) == str(quality_id)))['quality_name']
        return redirect(url_for('sludinajums', quality_name=new_quality_name, sludinajums_id=sludinajums_id))

    conn.close()
    return render_template("editlisting.html", sludinajums=sludinajums, manufacturers=manufacturers, qualities=qualities)

# ── DELETE ─────────────────────────────────────────────────────────────────────
@app.route("/<quality_name>/<int:sludinajums_id>/dzest", methods=["POST"])
def dzest(quality_name, sludinajums_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM sludinajumi WHERE id = ?", (sludinajums_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('kategorijas', quality_name=quality_name))

if __name__ == "__main__":
    app.run(debug=True, port=5001)
