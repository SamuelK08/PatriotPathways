import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI 
from dotenv import load_dotenv  

load_dotenv() 
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'resources.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

try:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=OPENAI_API_KEY)
    MODEL_CONFIGURED = True
except Exception as e:
    print(f"--- OpenAI API could not be configured: {e} ---")
    MODEL_CONFIGURED = False



class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    website = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts",
    "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
    "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"
}

@app.route('/')
def index():
    return render_template('index.html', states=STATE_NAMES)

@app.route('/<state_code>/<category_name>')
def show_category(state_code, category_name):
    category_map = { 'healthcare': 'Healthcare', 'employment': 'Employment', 'housing': 'Housing', 'mental-health': 'Mental Health' }
    db_category = category_map.get(category_name.lower())
    state_full_name = STATE_NAMES.get(state_code.upper(), "the selected state")
    if db_category:
        search_pattern = f"%, {state_code.upper()} %"
        resources = Resource.query.filter(Resource.category == db_category, Resource.address.like(search_pattern)).order_by(Resource.name).all()
        display_name = db_category
    else:
        resources, display_name = [], "Category Not Found"
    return render_template('category.html', category_name=display_name, state_name=state_full_name, resources=resources)

@app.route('/search', methods=['POST'])
def search():
    if not MODEL_CONFIGURED:
        return render_template('results.html', query=request.form['query'], response="Error: The AI Smart Search is not configured correctly. Please check the API key.")

    user_query = request.form['query']
    
    system_prompt = """
    You are a helpful assistant for the 'Patriot Pathways' website, a platform that helps US veterans.
    Please provide a helpful and comprehensive response. If a user is asking for resources (like clinics, job centers, charities, etc.), please list them.
    For each resource, if possible, provide its Name, a brief Description, and a Website or Phone Number.
    Format your response cleanly using Markdown.
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]
        )
        ai_response_text = completion.choices[0].message.content
    except Exception as e:
        print(f"An error occurred during OpenAI API call: {e}")
        ai_response_text = f"Sorry, there was an error contacting the AI service. Please try again later. Error: {e}"

    return render_template('results.html', query=user_query, response=ai_response_text)


if __name__ == '__main__':
    app.run(debug=True)