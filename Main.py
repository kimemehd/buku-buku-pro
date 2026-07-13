from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
# Hii ni muhimu kwa ajili ya kulinda mifumo ya Login (Session)
app.secret_key = os.urandom(24)

def init_db():
    conn = sqlite3.connect('bukubuku.db')
    cursor = conn.cursor()
    # Jedwali la miamala
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS michango (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jina TEXT NOT NULL,
            simu TEXT NOT NULL,
            kiasi REAL NOT NULL,
            kundi TEXT NOT NULL,
            aina TEXT NOT NULL,
            muda TEXT NOT NULL
        )
    ''')
    # Jedwali la watumiaji (Login info)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watumiaji (
            simu TEXT PRIMARY KEY,
            jina TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'mwanachama' -- 'admin' au 'mwanachama'
        )
    ''')
    
    # Kutengeneza Akaunti ya Kiongozi (Admin) wa kwanza kama haipo
    try:
        cursor.execute("INSERT INTO watumiaji (simu, jina, password, role) VALUES (?, ?, ?, ?)", 
                       ('0700000000', 'Kiongozi Mkuu', 'admin123', 'admin'))
    except sqlite3.IntegrityError:
        pass # Admin tayari yupo
        
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def nyumbani():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('bukubuku.db')
    cursor = conn.cursor()
    
    user_simu = session['user']['simu']
    user_role = session['user']['role']
    
    # Kupiga hesabu za maboksi ya juu
    cursor.execute("SELECT SUM(kiasi) FROM michango WHERE aina='Weka'")
    jumla_weka = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(kiasi) FROM michango WHERE aina='Toa'")
    jumla_toa = cursor.fetchone()[0] or 0
    salio = jumla_weka - jumla_toa
    
    # Kama ni Admin anaona miamala yote, kama ni mwanachama anaona yake tu!
    if user_role == 'admin':
        cursor.execute("SELECT * FROM michango ORDER BY id DESC")
    else:
        cursor.execute("SELECT * FROM michango WHERE simu=? ORDER BY id DESC", (user_simu,))
        
    miamala_raw = cursor.fetchall()
    conn.close()
    
    # Kugeuza data kuwa format ya Dictionary kwa ajili ya HTML
    miamala = []
    for m in miamala_raw:
        miamala.append({'muda': m[6], 'jina': m[1], 'simu': m[2], 'kundi': m[4], 'kiasi': m[3], 'aina': m[5], 'id': m[0]})
        
    return render_template('dashboard.html', miamala=miamala, salio=salio, jumla_weka=jumla_weka, jumla_toa=jumla_toa, user=session['user'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        simu = request.form.get('simu')
        password = request.form.get('password')
        
        conn = sqlite3.connect('bukubuku.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM watumiaji WHERE simu=? AND password=?", (simu, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user'] = {'simu': user[0], 'jina': user[1], 'role': user[3]}
            return redirect(url_for('nyumbani'))
        else:
            return "Namba ya simu au Password sio sahihi!"
            
    return render_template('login.html')

@app.route('/weka_muamala', methods=['POST'])
def weka_muamala():
    if 'user' not in session or session['user']['role'] != 'admin':
        return "Huna ruhusa ya kufanya hivi!", 403
        
    jina = request.form.get('jina')
    simu = request.form.get('simu')
    kiasi = float(request.form.get('kiasi'))
    kundi = request.form.get('kundi')
    aina = request.form.get('aina')
    
    import datetime
    sasa = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    
    conn = sqlite3.connect('bukubuku.db')
    cursor = conn.cursor()
    
    # Hakikisha mwanachama anasajiliwa kwenye mfumo wa login kiotomatiki akijazwa kwa mara ya kwanza
    try:
        cursor.execute("INSERT INTO watumiaji (simu, jina, password) VALUES (?, ?, ?)", (simu, jina, '1234'))
    except sqlite3.IntegrityError:
        pass # Tayari ana akaunti
        
    cursor.execute("INSERT INTO michango (jina, simu, kiasi, kundi, aina, muda) VALUES (?, ?, ?, ?, ?, ?)",
                   (jina, simu, kiasi, kundi, aina, sasa))
    conn.commit()
    conn.close()
    return redirect(url_for('nyumbani'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
