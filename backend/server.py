import os
from livekit import api
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
from livekit.api import LiveKitAPI, ListRoomsRequest
from file_handler import FileUploadHandler
from db_driver import DatabaseDriver
import json
import logging
import uuid
import os

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db = DatabaseDriver()

@app.route('/api/search-reports', methods=['GET'])
def search_reports():
    """Search interview reports API endpoint"""
    try:
        # Get query parameters
        search_query = request.args.get('q', '').strip()
        position_filter = request.args.get('position', '').strip()
        min_score = int(request.args.get('min_score', 0))
        
        if not search_query and not position_filter and min_score == 0:
            return jsonify({
                'success': False,
                'message': 'Please provide a search query, position filter, or minimum score'
            }), 400
        
        # Search reports
        reports = db.search_interview_reports(
            search_query=search_query,
            position_filter=position_filter,
            min_score=min_score,
            limit=20
        )
        
        # Convert to JSON-serializable format
        results = []
        for report in reports:
            results.append({
                'report_id': report.report_id,
                'candidate_name': report.candidate_name,
                'position': report.position,
                'interview_date': report.interview_date,
                'communication_score': report.communication_score,
                'technical_score': report.technical_score,
                'soft_skills_score': report.soft_skills_score,
                'overall_score': report.overall_score,
                'hiring_recommendation': report.hiring_recommendation,
                'total_questions': report.total_questions,
                'performance_rating': report.performance_rating,
                'avg_skill_score': report.avg_skill_score,
                'created_at': report.created_at
            })
        
        return jsonify({
            'success': True,
            'total': len(results),
            'reports': results
        })
        
    except Exception as e:
        logger.error(f"Error searching reports: {e}")
        return jsonify({
            'success': False,
            'message': f'Search failed: {str(e)}'
        }), 500

@app.route('/api/report/<report_id>', methods=['GET'])
def get_detailed_report(report_id):
    """Get detailed interview report by ID"""
    try:
        report = db.get_full_interview_report(report_id)
        
        if not report:
            return jsonify({
                'success': False,
                'message': 'Report not found'
            }), 404
        
        # Convert to JSON-serializable format
        result = {
            'report_id': report.report_id,
            'candidate_id': report.candidate_id,
            'candidate_name': report.candidate_name,
            'position': report.position,
            'interview_date': report.interview_date,
            'communication_score': report.communication_score,
            'technical_score': report.technical_score,
            'soft_skills_score': report.soft_skills_score,
            'overall_score': report.overall_score,
            'full_analysis_report': report.full_analysis_report,
            'strengths': report.strengths,
            'areas_for_improvement': report.areas_for_improvement,
            'technical_competencies': report.technical_competencies,
            'hiring_recommendation': report.hiring_recommendation,
            'cultural_fit_analysis': report.cultural_fit_analysis,
            'salary_recommendation': report.salary_recommendation,
            'next_steps': report.next_steps,
            'total_questions': report.total_questions,
            'interview_duration_minutes': report.interview_duration_minutes,
            'report_generated_by': report.report_generated_by,
            'created_at': report.created_at,
            'updated_at': report.updated_at
        }
        
        return jsonify({
            'success': True,
            'report': result
        })
        
    except Exception as e:
        logger.error(f"Error getting detailed report: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve report: {str(e)}'
        }), 500
# Initialize file handler
file_handler = FileUploadHandler()  # Will create its own service role client

async def generate_room_name():
    name = "room-" + str(uuid.uuid4())[:8]
    rooms = await get_rooms()
    while name in rooms:
        name = "room-" + str(uuid.uuid4())[:8]
    return name

async def get_rooms():
    api = LiveKitAPI()
    rooms = await api.room.list_rooms(ListRoomsRequest())
    await api.aclose()
    return [room.name for room in rooms.rooms]

@app.route("/api/getToken")
async def get_token():
    name = request.args.get("name", "my name")
    room = request.args.get("room", None)
    
    if not room:
        room = await generate_room_name()
        
    token = api.AccessToken(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET")) \
        .with_identity(name)\
        .with_name(name)\
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room
        ))
    
    return token.to_jwt()

@app.route("/createCandidate", methods=["POST"])
def create_candidate():
    """Create a new candidate profile"""
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email', '')
        phone = data.get('phone', '')
        
        if not name:
            return jsonify({"error": "name is required"}), 400
        
        # Generate unique candidate ID
        candidate_id = str(uuid.uuid4())
        
        # Default values for interview setup
        position = data.get('position', 'Not specified')
        experience_level = data.get('experience_level', 'Not specified')
        
        # Create candidate in database
        candidate = db.create_candidate(
            candidate_id=candidate_id,
            name=name,
            position=position,
            experience_level=experience_level,
            email=email,
            phone=phone
        )
        
        return jsonify({
            "success": True,
            "candidate_id": candidate.candidate_id,
            "name": candidate.name,
            "message": "Candidate profile created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating candidate: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/uploadResume", methods=["POST"])
def upload_resume():
    """Handle resume file upload to Supabase Storage"""
    try:
        # Check if file is in request
        if 'resume' not in request.files:
            return jsonify({"error": "No resume file provided"}), 400
        
        file = request.files['resume']
        candidate_id = request.form.get('candidate_id')
        
        if not candidate_id:
            return jsonify({"error": "candidate_id is required"}), 400
        
        # Check if candidate exists
        candidate = db.get_candidate_by_id(candidate_id)
        if not candidate:
            return jsonify({"error": "Candidate not found"}), 404
        
        # Upload file to Supabase Storage
        storage_path, file_type = file_handler.save_uploaded_file(file, candidate_id)
        
        # Update candidate with resume path (even if file already existed)
        success = db.update_candidate_resume(
            candidate_id=candidate_id,
            resume_path=storage_path,
            resume_summary="",  # Will be filled when processed
            skills=""  # Will be filled when processed
        )
        
        if not success:
            return jsonify({"error": "Failed to update candidate with resume path"}), 500
        
        return jsonify({
            "success": True,
            "storage_path": storage_path,
            "file_type": file_type,
            "candidate_id": candidate_id,
            "message": "Resume uploaded to Supabase Storage successfully (existing file replaced)"
        })
        
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/processResume", methods=["POST"])
def process_resume():
    """Process uploaded resume with RAG system from Supabase Storage"""
    try:
        data = request.get_json()
        candidate_id = data.get('candidate_id')
        
        if not candidate_id:
            return jsonify({"error": "candidate_id is required"}), 400
        
        # Get candidate and their resume path
        candidate = db.get_candidate_by_id(candidate_id)
        if not candidate:
            return jsonify({"error": "Candidate not found"}), 404
        
        if not candidate.resume_path:
            return jsonify({"error": "No resume found for this candidate"}), 400
        
        # Initialize RAG system if available
        try:
            from resume_rag import ResumeRAG
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                return jsonify({"error": "Google API key not configured"}), 500
            
            rag_system = ResumeRAG(google_api_key)
            
            # Determine file type from storage path
            file_type = candidate.resume_path.split('.')[-1] if '.' in candidate.resume_path else 'txt'
            
            # Process resume from Supabase Storage with timeout protection
            logger.info(f"Starting resume processing for candidate: {candidate_id}")
            
            try:
                resume_info = rag_system.process_resume(
                    candidate_id=candidate_id,
                    storage_path=candidate.resume_path,
                    file_type=file_type
                )
                logger.info(f"Resume processing completed successfully")
            except Exception as e:
                logger.error(f"Resume processing failed: {e}")
                return jsonify({"error": f"Resume processing failed: {str(e)}"}), 500
            
            # Update candidate with processed information
            import json
            skills_json = json.dumps(resume_info.skills)
            success = db.update_candidate_resume(
                candidate_id=candidate_id,
                resume_path=candidate.resume_path,  # Keep existing path
                resume_summary=resume_info.summary,
                skills=skills_json
            )
            
            if not success:
                return jsonify({"error": "Failed to update candidate with processed resume data"}), 500
            
            # Generate interview questions instantly
            logger.info(f"Generating questions instantly for software development role")
            
            try:
                questions = rag_system.generate_fast_questions(3)  # Super fast generation
                logger.info(f"Generated {len(questions)} questions in <1 second")
            except Exception as e:
                logger.warning(f"Fast question generation failed: {e}")
                questions = [
                    "Tell me about your programming experience.",
                    "What's your most complex project?",
                    "How do you debug difficult issues?"
                ]
            
            return jsonify({
                "success": True,
                "candidate_id": candidate_id,
                "resume_info": {
                    "skills": resume_info.skills,
                    "experience_years": resume_info.years_experience,
                    "summary": resume_info.summary,
                    "education": resume_info.education,
                    "projects": resume_info.projects
                },
                "interview_questions": questions,
                "message": "Resume processed successfully with RAG system"
            })
            
        except ImportError:
            return jsonify({"error": "Resume RAG dependencies not installed"}), 500
        
    except Exception as e:
        logger.error(f"Error processing resume: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/processResumeAndStartInterview", methods=["POST"])
def process_resume_and_start_interview():
    """Process resume first, extract info, create profile, and prepare for interview"""
    try:
        # Handle both file upload and text input
        if 'resume_file' in request.files:
            # File upload case
            file = request.files['resume_file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            # Extract text from PDF
            import tempfile
            import pdfplumber
            
            try:
                # Use context manager for proper file handling
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    # Save uploaded file to temp location
                    file.save(temp_file.name)
                    temp_file_path = temp_file.name
                
                # Extract text from PDF (file is now closed)
                resume_text = ""
                try:
                    with pdfplumber.open(temp_file_path) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                resume_text += page_text + "\n"
                finally:
                    # Ensure cleanup happens even if PDF processing fails
                    try:
                        os.unlink(temp_file_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup temp file: {cleanup_error}")
                
                if not resume_text.strip():
                    return jsonify({"error": "Could not extract text from PDF"}), 400
                    
            except Exception as e:
                logger.error(f"Failed to extract PDF text: {e}")
                return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500
                
        else:
            # Text input case
            data = request.get_json()
            resume_text = data.get('resume_text')
            if not resume_text:
                return jsonify({"error": "resume_text is required"}), 400
        
        # Initialize RAG system
        try:
            from resume_rag import ResumeRAG
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                logger.error("Google API key not configured")
                return jsonify({"error": "Google API key not configured"}), 500
            
            rag_system = ResumeRAG(google_api_key)
            logger.info("RAG system initialized successfully")
            
            # Extract candidate information from resume
            candidate_name = rag_system.analyzer.extract_candidate_name(resume_text)
            position = rag_system.analyzer.extract_position_title(resume_text)
            experience_level = rag_system.analyzer.extract_experience_level(resume_text)
            
            # Provide defaults if extraction fails
            if not candidate_name:
                candidate_name = "Candidate"
            if not position:
                position = "Software Developer"
            if not experience_level:
                experience_level = "mid"
            
            logger.info(f"Extracted from resume - Name: {candidate_name}, Position: {position}, Level: {experience_level}")
            
            # Auto-generate unique candidate ID
            import time
            import uuid
            timestamp = str(int(time.time()))
            random_suffix = str(uuid.uuid4())[:8]
            candidate_id = f"CAND_{timestamp}_{random_suffix}"
            
            # Create candidate profile automatically
            try:
                candidate = db.create_candidate(candidate_id, candidate_name, position, experience_level)
                if not candidate:
                    logger.error(f"Failed to create candidate in database: {candidate_id}")
                    return jsonify({"error": "Failed to create candidate profile from resume"}), 500
                logger.info(f"Successfully created candidate: {candidate_id}")
            except Exception as e:
                logger.error(f"Exception creating candidate: {e}")
                return jsonify({"error": f"Failed to create candidate: {str(e)}"}), 500
            
            # Process resume directly from text (no storage needed)
            try:
                # Extract skills and info directly from resume text
                skills = rag_system.analyzer.extract_skills(resume_text)
                experience_years = rag_system.analyzer.estimate_experience_years(resume_text)
                
                # Create minimal resume info without storage
                from resume_rag import ResumeInfo
                resume_info = ResumeInfo(
                    candidate_id=candidate_id,
                    raw_text=resume_text[:1000],  # Store first 1000 chars for summary
                    skills=skills,
                    experience=["Professional experience from resume"],
                    education=["Education background"],
                    projects=["Projects mentioned in resume"],
                    summary=f"{position} with {len(skills)} technical skills and {experience_years} years experience",
                    years_experience=experience_years
                )
                logger.info(f"Resume processed directly, found {len(skills)} skills")
            except Exception as e:
                logger.error(f"Failed to process resume text: {e}")
                return jsonify({"error": f"Failed to process resume: {str(e)}"}), 500
            
            # Update database with resume information (no storage path needed)
            try:
                import json
                skills_json = json.dumps(resume_info.skills)
                success = db.update_candidate_resume(
                    candidate_id,
                    "",  # No storage path needed
                    resume_info.summary,
                    skills_json
                )
                
                if not success:
                    logger.error("Failed to save resume information to database")
                    return jsonify({"error": "Failed to save resume information"}), 500
            except Exception as e:
                logger.error(f"Failed to update candidate with resume info: {e}")
                return jsonify({"error": f"Failed to save resume data: {str(e)}"}), 500
            
            # Generate questions instantly
            try:
                questions = rag_system.generate_fast_questions(3)
                logger.info(f"Generated {len(questions)} questions instantly")
            except Exception as e:
                logger.warning(f"Fast question generation failed: {e}")
                questions = [
                    "Tell me about your programming experience.",
                    "What's your most complex project?",
                    "How do you debug difficult issues?"
                ]
            
            return jsonify({
                "success": True,
                "candidate_id": candidate_id,
                "candidate_name": candidate_name,
                "position": position,
                "experience_level": experience_level,
                "resume_info": {
                    "skills": resume_info.skills,
                    "summary": resume_info.summary,
                    "years_experience": resume_info.years_experience
                },
                "interview_questions": questions,
                "message": f"Hi {candidate_name}! I've processed your resume and created your profile. Ready to start the interview!"
            })
            
        except ImportError:
            return jsonify({"error": "Resume RAG dependencies not installed"}), 500
        
    except Exception as e:
        logger.error(f"Error in process_resume_and_start_interview: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/endInterview", methods=["POST"])
async def end_interview():
    """End the current interview and generate report"""
    try:
        data = request.get_json() or {}
        candidate_id = data.get('candidate_id')
        
        # If no candidate_id provided, try to get the most recent one
        if not candidate_id:
            recent_candidate = db.get_most_recent_candidate()
            if recent_candidate:
                candidate_id = recent_candidate.candidate_id
            else:
                return jsonify({
                    "error": "No candidate found to end interview for",
                    "success": False
                }), 400
        
        # Check if candidate exists
        candidate = db.get_candidate_by_id(candidate_id)
        if not candidate:
            return jsonify({
                "error": "Candidate not found",
                "success": False
            }), 404
        
        # Update interview status to completed
        success = db.update_candidate_status(candidate_id, "completed")
        if not success:
            logger.warning(f"Failed to update candidate status for {candidate_id}")
        
        # Try to generate interview report using the assistant function
        try:
            from api import AssistantFnc, CandidateDetails
            assistant_fnc = AssistantFnc()
            
            # Set up candidate details
            assistant_fnc._candidate_details = {
                CandidateDetails.CANDIDATE_ID: candidate.candidate_id,
                CandidateDetails.NAME: candidate.name,
                CandidateDetails.POSITION: candidate.position,
                CandidateDetails.EXPERIENCE_LEVEL: candidate.experience_level,
                CandidateDetails.EMAIL: candidate.email,
                CandidateDetails.PHONE: candidate.phone,
                CandidateDetails.INTERVIEW_STATUS: "completed"
            }
            
            # Generate the report
            report_result = await assistant_fnc.generate_interview_report(None)
            
            return jsonify({
                "success": True,
                "message": "Interview ended and report generated successfully",
                "candidate_id": candidate_id,
                "candidate_name": candidate.name,
                "report_summary": report_result[:200] + "..." if len(report_result) > 200 else report_result
            })
            
        except Exception as report_error:
            logger.error(f"Failed to generate report: {report_error}")
            return jsonify({
                "success": True,
                "message": "Interview ended but report generation failed",
                "candidate_id": candidate_id,
                "candidate_name": candidate.name,
                "error": str(report_error)
            })
        
    except Exception as e:
        logger.error(f"Error ending interview: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)