from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from PyPDF2 import PdfReader
import re
from flask import send_file
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

# Configure Google Gemini API
genai.configure(api_key="AIzaSyDr3wt0ylDF96d-_vKB0M-d3aDeT1jwxD8")
model = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)
CORS(app)

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.pdf'):
        return jsonify({"error": "Invalid file type. Only PDF is allowed"}), 400

    if len(file.read()) > 5 * 1024 * 1024:
        return jsonify({"error": "File size exceeds 5MB"}), 400

    file.seek(0)  # Reset file pointer

    # Extract text from the PDF
    reader = PdfReader(file)
    resume_text = "\n".join([page.extract_text() for page in reader.pages])

    # Define job description
    job_description = (
        "As a Full Stack Engineer Intern, you’ll apply your expertise in both frontend and backend development to design, develop, and maintain ScoutBetter’s web-based intelligence platform. You’ll work alongside our team to create scalable, reliable, and high-performing solutions using Python and React., "
        """Responsibilities
        Develop Full-Stack Solutions: Build end-to-end solutions with a focus on Python (backend) and React (frontend) to support core platform functionalities.
        Collaborate with the Team: Work closely with other engineers and cross-functional teams to ensure timely delivery of new features, updates, and bug fixes.
        Code Quality & Testing: Write clean, efficient code and actively participate in code reviews, testing, and quality assurance processes.
        Gain Business Domain Knowledge: Develop a strong understanding of ScoutBetter’s business goals to ensure the platform aligns with strategic objectives.
        Stay Current: Continuously explore and implement new technologies and trends to drive platform innovation and efficiency. 
        """
        """Requirements
        Education: Currently pursuing or holding a degree in Computer Science, Software Engineering, or a related field.
        Programming Proficiency: Strong expertise in Python and React, with backend experience in Django or Flask and frontend skills in JavaScript/TypeScript, HTML, and CSS.
        Database Knowledge: Solid understanding of database design, modeling, SQL, and familiarity with NoSQL databases (e.g., MongoDB).
        Cloud & DevOps: Familiarity with AWS and Azure cloud services, as well as basic knowledge of DevOps practices, including CI/CD pipelines, containerization (Docker), and orchestration (Kubernetes).
        API & Architecture: Experience with designing and integrating RESTful APIs and a foundational understanding of microservices architecture.
        Version Control & Collaboration: Proficiency with Git and experience using collaboration tools like GitHub, GitLab, or Bitbucket.
        Front-End Frameworks & Libraries: Knowledge of state management libraries (e.g., Redux, MobX) and experience building responsive, user-friendly UI
        Problem-Solving Skills:Excellent analytical and problem-solving skills, with the ability to troubleshoot issues across the stack.
        """
    )

    # Use Gemini API to analyze resume relevance and formatting
    relevance_prompt = (
        f"Evaluate this resume for relevance to the job description:\n\n"
        f"Job Description:\n{job_description}\n\nResume:\n{resume_text}\n\n"
        "Provide a score (0-100) for relevance and key strengths/weaknesses."
    )
    formatting_prompt = (
        f"Analyze the formatting of this resume:\n\n{resume_text}\n\n"
        "Provide feedback on clarity, readability, and quality."
    )
    scoring_criteria = (
            "The overall score is calculated by combining relevance (70%) and "
            "formatting quality (30%). Relevance measures how closely the resume aligns "
            "with the job description based on skills, experience, and projects. Formatting "
            "assesses the clarity, readability, and inclusion of essential sections."
        )
    try:
        # Generate relevance analysis
        relevance_response = model.generate_content(relevance_prompt)
        # print(relevance_response)
        relevance_feedback = relevance_response.text
        # print(relevance_feedback)
        score_match = re.search(r"Relevance Score: (\d+)/100", relevance_feedback)
        relevance_score = int(score_match.group(1))
        # print("Relevance Score:", relevance_score)
        

        # Generate formatting analysis
        formatting_response = model.generate_content(formatting_prompt)
        # print(formatting_response)
        formatting_feedback = formatting_response.text

        # Calculate missing sections
        required_sections = ["summary", "skills", "experience", "education"]
        missing_sections = [s for s in required_sections if s not in resume_text.lower()]

        # Formatting score based on missing sections
        formatting_score = 100 - len(missing_sections) * 10
        overall_score = int(0.7 * relevance_score + 0.3 * formatting_score)

        def extract_section(text, section_name):
            """
            Extracts a specific section from the given text based on the section name.
            """
            # Create a pattern that matches the section heading and captures content up to the next heading
            pattern = rf"\*\*{section_name}:\*\*\n\n(.*?)(?=\n\n\*\*|$)"
            match = re.search(pattern, text, re.DOTALL)  # Use DOTALL to match across multiple lines
            return match.group(1).strip() if match else None

        # Fetch the content from the response
        response_text = relevance_response.text

        # Extract sections
        strengths = extract_section(response_text, "Strengths")
        #print(strengths)
        weaknesses = extract_section(response_text, "Weaknesses")
        #print(weaknesses)
        recommendations = extract_section(response_text, "Recommendations for Improvement")
        #print(recommendations)

        return jsonify({
            "score": overall_score,
            "relevance_score": relevance_score,
            "formatting_score": formatting_score,
            "missing_sections": missing_sections,
            "scoring_criteria": scoring_criteria,
            "strengths": strengths,
            "weeknesses": weaknesses,
            "suggestions": recommendations,
            "formatting_suggestions":formatting_feedback,
        })
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/download', methods=['POST'])
def download_report():
    try:
        # Extract data from the request
        data = request.json
        score = data.get('score', 0)
        relevance_score = data.get('relevance_score', 0)
        formatting_score = data.get('formatting_score', 0)
        missing_sections = data.get('missing_sections', [])
        scoring_criteria = data.get('scoring_criteria', "")
        strengths = data.get('strengths', "N/A")
        weaknesses = data.get('weeknesses', "N/A")
        suggestions = data.get('suggestions', "N/A")
        formatting_feedback = data.get('formatting_suggestions', "N/A")

        # Create a buffer for the PDF
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)

        # Define styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading2']
        normal_style = styles['BodyText']

        # Build the report content
        elements = []

        # Add title
        elements.append(Paragraph("Resume Analysis Report", title_style))
        elements.append(Spacer(1, 12))

        # Add scores
        score_table = [
            ["Overall Score", score],
            ["Relevance Score", relevance_score],
            ["Formatting Score", formatting_score],
        ]
        table = Table(score_table, colWidths=[150, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        # Add missing sections
        elements.append(Paragraph("Missing Sections:", heading_style))
        elements.append(Paragraph(", ".join(missing_sections) or "None", normal_style))
        elements.append(Spacer(1, 12))

        # Add scoring criteria
        elements.append(Paragraph("Scoring Criteria:", heading_style))
        elements.append(Paragraph(scoring_criteria, normal_style))
        elements.append(Spacer(1, 12))

        # Add strengths
        formatted_strengths = [
            strength.strip() for strength in strengths.split("\n") if strength.strip()
        ]

        elements.append(Paragraph("Strengths:", heading_style))
        for strength in formatted_strengths:
            elements.append(Paragraph(strength, normal_style))
            elements.append(Spacer(1, 12))
        
        

        # Add weaknesses
        formatted_weeknesses = [
            weakness.strip() for weakness in weaknesses.split("\n") if weakness.strip()
        ]

        elements.append(Paragraph("Weaknesses:", heading_style))
        for weakness in formatted_weeknesses:
            elements.append(Paragraph(weakness, normal_style))
            elements.append(Spacer(1, 12))
        
        

        formatted_suggestions = [
            suggestion.strip() for suggestion in suggestions.split("\n") if suggestion.strip()
        ]

        # Add "Suggestions" heading
        elements.append(Paragraph("Suggestions:", heading_style))
        for suggestion in formatted_suggestions:
            elements.append(Paragraph(suggestion, normal_style))
            elements.append(Spacer(1, 6))

        # Build the PDF
        doc.build(elements)

        # Serve the PDF
        pdf_buffer.seek(0)
        return send_file(pdf_buffer, as_attachment=True, download_name="resume_analysis_report.pdf", mimetype="application/pdf")
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    

if __name__ == '__main__':
    app.run(debug=True)
