from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Tutorial, Step, Progress
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tutorials.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

genai.configure(api_key="AIzaSyA5tWjXreSWnvXzJC3jsk9yXyM1TqB8yek")

def gemini_code_tutor(prompt):
    try:
        model = genai.GenerativeModel("gemini-pro-vision")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI error: {str(e)}"

with app.app_context():
    db.create_all()

# ----------------- Routes ----------------- #
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            return "Username already exists"
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    tutorials = Tutorial.query.all()
    return render_template('dashboard.html', tutorials=tutorials)

@app.route('/tutorial/create', methods=['GET', 'POST'])
def create_tutorial():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        tutorial = Tutorial(title=title, description=description, author_id=session['user_id'])
        db.session.add(tutorial)
        db.session.commit()
        return redirect(url_for('add_steps', tutorial_id=tutorial.id))
    return render_template('tutorial_create.html')

@app.route('/tutorial/<int:tutorial_id>/add_steps', methods=['GET', 'POST'])
def add_steps(tutorial_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    if request.method == 'POST':
        content = request.form['content']
        step_number = Step.query.filter_by(tutorial_id=tutorial_id).count() + 1
        step = Step(tutorial_id=tutorial_id, step_number=step_number, content=content)
        db.session.add(step)
        db.session.commit()
        return redirect(url_for('add_steps', tutorial_id=tutorial_id))
    steps = Step.query.filter_by(tutorial_id=tutorial_id).all()
    return render_template('add_steps.html', tutorial=tutorial, steps=steps)

@app.route('/tutorial/<int:tutorial_id>')
def tutorial_view(tutorial_id):
    tutorial = Tutorial.query.get_or_404(tutorial_id)
    steps = Step.query.filter_by(tutorial_id=tutorial_id).order_by(Step.step_number).all()
    completed_steps = []
    if 'user_id' in session:
        progress = Progress.query.filter_by(user_id=session['user_id'], tutorial_id=tutorial_id).first()
        if progress:
            completed_steps = progress.get_completed_steps()
    return render_template('tutorial_view.html', tutorial=tutorial, steps=steps, completed_steps=completed_steps)

@app.route('/tutorial/<int:tutorial_id>/step/<int:step_id>/complete', methods=['POST'])
def complete_step(tutorial_id, step_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user_id = session['user_id']
    progress = Progress.query.filter_by(user_id=user_id, tutorial_id=tutorial_id).first()
    if not progress:
        progress = Progress(user_id=user_id, tutorial_id=tutorial_id)
        db.session.add(progress)
    progress.mark_step_complete(step_id)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/tutorial/<int:tutorial_id>/step/<int:step_id>/incomplete', methods=['POST'])
def incomplete_step(tutorial_id, step_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user_id = session['user_id']
    progress = Progress.query.filter_by(user_id=user_id, tutorial_id=tutorial_id).first()
    if not progress:
        return jsonify({'error': 'No progress found'}), 404
    progress.mark_step_incomplete(step_id)
    db.session.commit()
    return jsonify({'success': True})

# ----------------- AI Tutorial Generation ----------------- #
@app.route('/generate_tutorial', methods=['GET', 'POST'])
def generate_tutorial():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    steps = []
    if request.method == 'POST':
        topic = request.form['topic']
        prompt = f"Create a step-by-step tutorial for '{topic}' in 5–6 steps."
        try:
            result = gemini_code_tutor(prompt)
            steps = [result]
        except Exception as e:
            steps = [f"AI error: {str(e)}"]
    return render_template('generate_tutorial.html', steps=steps)

@app.route('/ai_tutor', methods=['GET', 'POST'])
def ai_tutor():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    ai_response = None
    user_code = ''
    error = None
    if request.method == 'POST':
        user_code = request.form['user_code']
        prompt = f"Act as a tutor. The user submitted this code/problem:\n\n{user_code}\n\nExplain what it does, find errors if any, and give step-by-step suggestions to improve or fix it."
        try:
            ai_response = gemini_code_tutor(prompt)
        except Exception as e:
            error = f"AI error: {str(e)}"
    return render_template('ai_tutor.html', ai_response=ai_response, user_code=user_code, error=error)

if __name__ == '__main__':
    app.run(debug=True)
