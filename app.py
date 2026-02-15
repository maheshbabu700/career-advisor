from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from deepface import DeepFace
import fitz
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

TECHNICAL_SKILLS = [
    "Python", "Java", "C++", "SQL", "Machine Learning", "Artificial Intelligence",
    "Data Analytics", "Flask", "React", "HTML", "CSS", "JavaScript", "Deep Learning",
    "Cloud Computing", "AWS", "UI/UX Design", "Tableau", "PowerBI"
]

CAREER_SKILLS = {
    "AI/ML Engineer": ["Python", "Machine Learning", "Deep Learning", "Artificial Intelligence"],
    "Data Analyst": ["SQL", "Data Analytics", "Tableau", "PowerBI"],
    "Frontend Developer": ["HTML", "CSS", "JavaScript", "React"],
    "Software Engineer": ["Java", "C++", "Cloud Computing", "AWS"]
}

# ---------------- SKILL EXTRACTION ----------------
def extract_skills_logic(text):
    text = text.lower()
    skill_counts = {}
    found_skills = []

    for skill in TECHNICAL_SKILLS:
        count = text.count(skill.lower())
        if count > 0:
            found_skills.append(skill)
            skill_counts[skill] = count

    if not skill_counts:
        skill_counts = {"No Skills Found": 1}

    return found_skills, skill_counts

# ---------------- CAREER SCORING ----------------
def calculate_career_scores(skills):
    career_scores = {}

    for career, required_skills in CAREER_SKILLS.items():
        matched = len(set(skills) & set(required_skills))
        total = len(required_skills)
        score = int((matched / total) * 100) if total > 0 else 0
        career_scores[career] = score

    if all(score == 0 for score in career_scores.values()):
        career_scores["General Role"] = 10

    return career_scores

def get_best_career(career_scores):
    return max(career_scores, key=career_scores.get)

# ---------------- ADVICE ----------------
def generate_advice(career, skills, missing_skills):
    advice = []

    if career == "AI/ML Engineer":
        advice += [
            "Strengthen Python and Machine Learning fundamentals.",
            "Build Deep Learning & NLP projects.",
            "Learn TensorFlow or PyTorch.",
            "Practice on Kaggle datasets."
        ]

    elif career == "Data Analyst":
        advice += [
            "Improve SQL and Data Visualization skills.",
            "Learn Pandas, NumPy, Power BI/Tableau.",
            "Work on real-world datasets.",
            "Study statistics."
        ]

    elif career == "Frontend Developer":
        advice += [
            "Master HTML, CSS, JavaScript.",
            "Build responsive web apps.",
            "Learn React and UI/UX.",
            "Create portfolio projects."
        ]

    elif career == "Software Engineer":
        advice += [
            "Practice DSA and problem solving.",
            "Build full-stack projects.",
            "Learn system design basics.",
            "Improve OOP concepts."
        ]

    if missing_skills:
        advice.append("Focus on learning: " + ", ".join(missing_skills))

    return advice

# ---------------- PERSONALITY ----------------
def analyze_personality_from_image(image_path):
    try:
        analysis = DeepFace.analyze(
            img_path=image_path,
            actions=['emotion'],
            enforce_detection=False
        )

        emotions = {k: float(v) for k, v in analysis[0]['emotion'].items()}
        personality_traits = []

        if emotions.get('happy', 0) > 40:
            personality_traits += ["Openness", "Agreeableness"]
        if emotions.get('neutral', 0) > 40:
            personality_traits.append("Conscientiousness")
        if emotions.get('sad', 0) > 20:
            personality_traits.append("Emotional Sensitivity")
        if emotions.get('angry', 0) > 20:
            personality_traits.append("Assertiveness")
        if emotions.get('fear', 0) > 20:
            personality_traits.append("Analytical")

        if not personality_traits:
            personality_traits.append("Balanced Personality")

        return {
            "traits": personality_traits,
            "emotion_scores": emotions
        }

    except Exception as e:
        print("DL Error:", e)
        return {
            "traits": ["Professional"],
            "emotion_scores": {}
        }

# ---------------- ROUTES ----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    resume_file = request.files.get('resume')
    image_file = request.files.get('profile_image')

    if not resume_file or not image_file:
        return jsonify({"error": "Please upload both files"}), 400

    # Save resume
    resume_filename = secure_filename(resume_file.filename)
    resume_path = os.path.join(UPLOAD_FOLDER, resume_filename)
    resume_file.save(resume_path)

    # Extract text
    text = ""
    with fitz.open(resume_path) as doc:
        for page in doc:
            text += page.get_text()

    skills, skill_counts = extract_skills_logic(text)
    career_scores = calculate_career_scores(skills)
    best_career = get_best_career(career_scores)

    # Missing skills + advice
    required_skills = CAREER_SKILLS.get(best_career, [])
    missing_skills = list(set(required_skills) - set(skills))
    advice = generate_advice(best_career, skills, missing_skills)

    # Save image
    image_filename = secure_filename(image_file.filename)
    image_path = os.path.join(UPLOAD_FOLDER, image_filename)
    image_file.save(image_path)

    personality = analyze_personality_from_image(image_path)

    return jsonify({
        "status": "success",
        "skill_counts": skill_counts,
        "career_scores": career_scores,
        "suggested_career": best_career,
        "personality_traits": personality["traits"],
        "emotion_scores": personality["emotion_scores"],
        "missing_skills": missing_skills,
        "advice": advice
    })

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)