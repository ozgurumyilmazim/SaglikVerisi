import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3
from pdf_reader import extract_lab_results

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "supersecret"
DB = 'patients.db'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database helpers
def init_db():
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS patient (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                dob TEXT,
                notes TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                date TEXT,
                hemoglobin REAL,
                glucose REAL,
                creatinine REAL,
                uric_acid REAL,
                sodium REAL,
                potassium REAL,
                urine_ph REAL,
                pdf_file TEXT,
                FOREIGN KEY (patient_id) REFERENCES patient(id)
            )
        ''')

@app.before_first_request
def initialize():
    init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM patient")
        patients = cur.fetchall()
    return render_template('index.html', patients=patients)

@app.route('/patient/<int:pid>')
def patient_detail(pid):
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM patient WHERE id=?", (pid,))
        patient = cur.fetchone()
        cur.execute("SELECT * FROM results WHERE patient_id=? ORDER BY date DESC", (pid,))
        results = cur.fetchall()
    return render_template('patient_detail.html', patient=patient, results=results)

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        notes = request.form['notes']
        with sqlite3.connect(DB) as con:
            cur = con.cursor()
            cur.execute("INSERT INTO patient (name, dob, notes) VALUES (?, ?, ?)", (name, dob, notes))
            con.commit()
        flash('Hasta eklendi!', 'success')
        return redirect(url_for('index'))
    return render_template('add_patient.html')

@app.route('/upload_pdf/<int:pid>', methods=['GET', 'POST'])
def upload_pdf(pid):
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            flash('Dosya bulunamadi', 'danger')
            return redirect(request.url)
        file = request.files['pdf_file']
        if file.filename == '':
            flash('Dosya secilmedi', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # PDF'den verileri cek
            lab_results = extract_lab_results(filepath)
            date = request.form['date']
            with sqlite3.connect(DB) as con:
                cur = con.cursor()
                cur.execute('''
                    INSERT INTO results (patient_id, date, hemoglobin, glucose, creatinine, uric_acid, sodium, potassium, urine_ph, pdf_file)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pid, date,
                    lab_results.get('hemoglobin'),
                    lab_results.get('glucose'),
                    lab_results.get('creatinine'),
                    lab_results.get('uric_acid'),
                    lab_results.get('sodium'),
                    lab_results.get('potassium'),
                    lab_results.get('urine_ph'),
                    filename
                ))
                con.commit()
            flash('PDF yuklendi ve sonuclar eklendi!', 'success')
            return redirect(url_for('patient_detail', pid=pid))
        else:
            flash('Yalnizca PDF dosyasi yukleyebilirsiniz.', 'danger')
            return redirect(request.url)
    return render_template('upload_pdf.html', pid=pid)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True)
