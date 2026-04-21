from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db
from datetime import datetime, date
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_in_production'

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        conn = get_db()
        g.user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("login"))

        flash(error, 'error')
        db.close()

    return render_template('register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))

        flash(error, 'error')
        db.close()

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    crops = db.execute('''
        SELECT c.id, c.name, c.planted_date, c.expected_harvest_date, c.status, g.name as grain_type
        FROM crops c
        JOIN grain_types g ON c.grain_type_id = g.id
        WHERE c.user_id = ?
        ORDER BY c.expected_harvest_date ASC
    ''', (g.user['id'],)).fetchall()
    
    processed_crops = []
    today = date.today()
    
    for crop in crops:
        planted = datetime.strptime(crop['planted_date'], '%Y-%m-%d').date()
        harvest = datetime.strptime(crop['expected_harvest_date'], '%Y-%m-%d').date()
        
        total_days = (harvest - planted).days
        if total_days <= 0:
            total_days = 1 # Avoid division by zero
            
        days_passed = (today - planted).days
        
        if days_passed < 0:
            progress = 0
            days_remaining = total_days
        elif days_passed > total_days:
            progress = 100
            days_remaining = 0
        else:
            progress = int((days_passed / total_days) * 100)
            days_remaining = total_days - days_passed
            
        # Update status if Harvest date has passed but still growing
        status = crop['status']
        if status == 'Growing' and today >= harvest:
            status = 'Ready to Harvest'
            
        processed_crops.append({
            'id': crop['id'],
            'name': crop['name'],
            'grain_type': crop['grain_type'],
            'planted_date': crop['planted_date'],
            'expected_harvest_date': crop['expected_harvest_date'],
            'status': status,
            'progress': progress,
            'days_remaining': days_remaining
        })
        
    db.close()
    return render_template('dashboard.html', crops=processed_crops)

@app.route('/crop/add', methods=('GET', 'POST'))
@login_required
def add_crop():
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        grain_type_id = request.form['grain_type_id']
        planted_date = request.form['planted_date']
        
        # Calculate expected harvest date
        grain = db.execute('SELECT default_days_to_harvest FROM grain_types WHERE id = ?', (grain_type_id,)).fetchone()
        
        if not name or not grain_type_id or not planted_date:
            flash('All fields are required.', 'error')
        else:
            try:
                planted_dt = datetime.strptime(planted_date, '%Y-%m-%d').date()
                from datetime import timedelta
                expected_harvest = planted_dt + timedelta(days=grain['default_days_to_harvest'])
                
                db.execute(
                    'INSERT INTO crops (user_id, grain_type_id, name, planted_date, expected_harvest_date) VALUES (?, ?, ?, ?, ?)',
                    (g.user['id'], grain_type_id, name, planted_dt.strftime('%Y-%m-%d'), expected_harvest.strftime('%Y-%m-%d'))
                )
                db.commit()
                flash('Crop added successfully.', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
                
    grain_types = db.execute('SELECT * FROM grain_types').fetchall()
    db.close()
    return render_template('add_crop.html', grain_types=grain_types)

@app.route('/crop/<int:id>/delete', methods=('POST',))
@login_required
def delete_crop(id):
    db = get_db()
    db.execute('DELETE FROM crops WHERE id = ? AND user_id = ?', (id, g.user['id']))
    db.commit()
    db.close()
    flash('Crop deleted successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/log/add/<int:crop_id>', methods=('GET', 'POST'))
@login_required
def add_log(crop_id):
    db = get_db()
    # Verify crop belongs to user
    crop = db.execute('SELECT * FROM crops WHERE id = ? AND user_id = ?', (crop_id, g.user['id'])).fetchone()
    if crop is None:
        flash('Crop not found.', 'error')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        log_type = request.form['log_type']
        cost = request.form['cost']
        notes = request.form['notes']
        log_date = date.today().strftime('%Y-%m-%d')
        
        if not log_type or cost == '':
            flash('Type and Cost are required.', 'error')
        else:
            try:
                cost = float(cost)
                db.execute(
                    'INSERT INTO logs (crop_id, log_date, log_type, cost, notes) VALUES (?, ?, ?, ?, ?)',
                    (crop_id, log_date, log_type, cost, notes)
                )
                db.commit()
                flash('Log added successfully.', 'success')
                return redirect(url_for('logs'))
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
                
    db.close()
    return render_template('add_log.html', crop=crop)

@app.route('/logs')
@login_required
def logs():
    db = get_db()
    logs = db.execute('''
        SELECT l.id, l.log_date, l.log_type, l.cost, l.notes, c.name as crop_name
        FROM logs l
        JOIN crops c ON l.crop_id = c.id
        WHERE c.user_id = ?
        ORDER BY l.log_date DESC, l.id DESC
    ''', (g.user['id'],)).fetchall()
    db.close()
    return render_template('logs.html', logs=logs)

@app.route('/reports')
@login_required
def reports():
    db = get_db()
    # Get total cost per crop
    crop_costs = db.execute('''
        SELECT c.name, SUM(l.cost) as total_cost
        FROM crops c
        LEFT JOIN logs l ON c.id = l.crop_id
        WHERE c.user_id = ?
        GROUP BY c.id, c.name
        ORDER BY total_cost DESC
    ''', (g.user['id'],)).fetchall()
    
    # Get total cost per log type
    type_costs = db.execute('''
        SELECT l.log_type, SUM(l.cost) as total_cost
        FROM logs l
        JOIN crops c ON l.crop_id = c.id
        WHERE c.user_id = ?
        GROUP BY l.log_type
        ORDER BY total_cost DESC
    ''', (g.user['id'],)).fetchall()
    
    db.close()
    
    total_overall = sum(row['total_cost'] or 0 for row in crop_costs)
    
    return render_template('reports.html', crop_costs=crop_costs, type_costs=type_costs, total_overall=total_overall)

if __name__ == '__main__':
    # Initialize DB on first run
    if not os.path.exists('agrismart.db'):
        init_db()
        from seed import seed
        seed()
    app.run(debug=True, port=5000)
