from livekit.agents import llm, function_tool, RunContext
import enum
import logging
import uuid
import time
from dotenv import load_dotenv
from db_driver import DatabaseDriver
from file_handler import FileUploadHandler
import json
import os

# Load environment variables
load_dotenv()

logger = logging.getLogger("user-data")
logger.setLevel(logging.INFO)

DB = DatabaseDriver()
file_handler = FileUploadHandler()  # Will create its own service role client

# Initialize RAG system when dependencies are available
rag_system = None
try:
    from resume_rag import ResumeRAG
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if google_api_key:
        rag_system = ResumeRAG(google_api_key)
        logger.info("Resume RAG system initialized")
except ImportError:
    logger.warning("Resume RAG dependencies not installed. Install with: pip install -r requirements.txt")

class InterviewPhase(enum.Enum):
    INITIAL = "initial"
    PROFILE_CREATED = "profile_created"
    RESUME_UPLOADED = "resume_uploaded"
    PERSONALIZED_GREETING = "personalized_greeting"
    INTRODUCTION = "introduction"
    PROJECTS = "projects"
    PROJECTS_SKILLS_QUESTIONS = "projects_skills_questions"
    EXPERIENCE = "experience"
    ACHIEVEMENTS = "achievements"
    WRAP_UP = "wrap_up"
    COMPLETED = "completed"

class CandidateDetails(enum.Enum):
    CANDIDATE_ID = "candidate_id"
    NAME = "name"
    POSITION = "position"
    EXPERIENCE_LEVEL = "experience_level"
    EMAIL = "email"
    PHONE = "phone"
    INTERVIEW_STATUS = "interview_status"
    

class AssistantFnc:
    def __init__(self):
        self._candidate_details = {
            CandidateDetails.CANDIDATE_ID: "",
            CandidateDetails.NAME: "",
            CandidateDetails.POSITION: "",
            CandidateDetails.EXPERIENCE_LEVEL: "",
            CandidateDetails.EMAIL: "",
            CandidateDetails.PHONE: "",
            CandidateDetails.INTERVIEW_STATUS: "scheduled"
        }
        self._interview_questions = []
        self._resume_processed = False
        self._generated_questions = []
        self._current_phase = InterviewPhase.INITIAL
        self._candidate_name_from_resume = ""
    
    def get_candidate_str(self):
        candidate_str = ""
        for key, value in self._candidate_details.items():
            candidate_str += f"{key.value}: {value}\n"
            
        return candidate_str
    
    @function_tool
    async def lookup_candidate(self, context: RunContext, candidate_id: str):
        """lookup a candidate by their ID
        
        Args:
            candidate_id: The ID of the candidate to lookup
        """
        logger.info("lookup candidate - ID: %s", candidate_id)
        
        result = DB.get_candidate_by_id(candidate_id)
        if result is None:
            return "Candidate not found"
        
        self._candidate_details = {
            CandidateDetails.CANDIDATE_ID: result.candidate_id,
            CandidateDetails.NAME: result.name,
            CandidateDetails.POSITION: result.position,
            CandidateDetails.EXPERIENCE_LEVEL: result.experience_level,
            CandidateDetails.EMAIL: result.email,
            CandidateDetails.PHONE: result.phone,
            CandidateDetails.INTERVIEW_STATUS: result.interview_status
        }
        
        return f"The candidate details are: {self.get_candidate_str()}"
    
    @function_tool
    async def get_candidate_details(self, context: RunContext):
        """get the details of the current candidate"""
        logger.info("get candidate details")
        return f"The candidate details are: {self.get_candidate_str()}"
    
    @function_tool
    async def process_resume_and_start_interview(
        self,
        context: RunContext,
        resume_text: str,
        file_type: str = "txt",
        filename: str = "resume.txt"
    ):
        """Process resume first, extract info, create profile, and start interview
        
        Args:
            resume_text: The content of the resume
            file_type: Type of file (txt, pdf, docx) 
            filename: Original filename
        """
        if not rag_system:
            return "Resume analysis system not available. Please contact support."
        
        try:
            # Extract candidate information from resume
            candidate_name = rag_system.analyzer.extract_candidate_name(resume_text)
            position = rag_system.analyzer.extract_position_title(resume_text)
            experience_level = rag_system.analyzer.extract_experience_level(resume_text)
            
            logger.info(f"Extracted from resume - Name: {candidate_name}, Position: {position}, Level: {experience_level}")
            
            # Auto-generate unique candidate ID
            timestamp = str(int(time.time()))
            random_suffix = str(uuid.uuid4())[:8]
            candidate_id = f"CAND_{timestamp}_{random_suffix}"
            
            # Create candidate profile automatically
            result = DB.create_candidate(candidate_id, candidate_name, position, experience_level)
            if result is None:
                return "Failed to create candidate profile from resume"
            
            # Store candidate details
            self._candidate_details = {
                CandidateDetails.CANDIDATE_ID: result.candidate_id,
                CandidateDetails.NAME: result.name,
                CandidateDetails.POSITION: result.position,
                CandidateDetails.EXPERIENCE_LEVEL: result.experience_level,
                CandidateDetails.EMAIL: result.email,
                CandidateDetails.PHONE: result.phone,
                CandidateDetails.INTERVIEW_STATUS: result.interview_status
            }
            
            # Process resume directly from text (no storage needed)
            try:
                # Extract skills and info directly from resume text
                skills = rag_system.analyzer.extract_skills(resume_text)
                experience_years = rag_system.analyzer.estimate_experience_years(resume_text)
                
                # Create minimal resume info without storage
                from resume_rag import ResumeInfo
                resume_info = ResumeInfo(
                    candidate_id=candidate_id,
                    raw_text=resume_text[:1000],  # Store first 1000 chars
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
                return f"Failed to process resume: {str(e)}"
            
            # Update database with resume information (no storage path needed)
            skills_json = json.dumps(resume_info.skills)
            success = DB.update_candidate_resume(
                candidate_id,
                "",  # No storage path needed
                resume_info.summary,
                skills_json
            )
            
            if success:
                self._resume_processed = True
                self._current_phase = InterviewPhase.RESUME_UPLOADED
                self._candidate_name_from_resume = candidate_name
                
                # Generate questions instantly
                self._generated_questions = rag_system.generate_fast_questions(3)
                logger.info(f"Generated {len(self._generated_questions)} questions instantly")
                
                # Start interview immediately with personalized greeting
                return f"Hi {candidate_name}! Nice to meet you. I've reviewed your resume and I can see you're applying for a {position} role. Let's get started - can you give me a brief introduction about yourself and your background?"
            else:
                return "Failed to save resume information. Please try again."
                
        except Exception as e:
            logger.error(f"Error processing resume and starting interview: {e}")
            return f"Error processing your resume: {str(e)}. Please try again."

    @function_tool
    async def create_candidate_profile(
        self, 
        context: RunContext,
        name: str,
        position: str,
        experience_level: str,
        email: str = "",
        phone: str = ""
    ):
        """Create a new candidate profile with auto-generated ID
        
        Args:
            name: Full name of the candidate
            position: Position they are interviewing for
            experience_level: Their experience level (entry, mid, senior, etc.)
            email: Email address (optional)
            phone: Phone number (optional)
        """
        # Auto-generate unique candidate ID
        timestamp = str(int(time.time()))
        random_suffix = str(uuid.uuid4())[:8]
        candidate_id = f"CAND_{timestamp}_{random_suffix}"
        
        logger.info("create candidate profile - auto-generated ID: %s, name: %s, position: %s, experience: %s", candidate_id, name, position, experience_level)
        result = DB.create_candidate(candidate_id, name, position, experience_level, email, phone)
        if result is None:
            return "Failed to create candidate profile"
        
        self._candidate_details = {
            CandidateDetails.CANDIDATE_ID: result.candidate_id,
            CandidateDetails.NAME: result.name,
            CandidateDetails.POSITION: result.position,
            CandidateDetails.EXPERIENCE_LEVEL: result.experience_level,
            CandidateDetails.EMAIL: result.email,
            CandidateDetails.PHONE: result.phone,
            CandidateDetails.INTERVIEW_STATUS: result.interview_status
        }
        
        self._current_phase = InterviewPhase.PROFILE_CREATED
        
        return "Perfect! I've created your candidate profile. Now, to personalize our interview, please share your resume. You can copy and paste your resume text here."

    @function_tool
    async def create_candidate(
        self, 
        context: RunContext,
        candidate_id: str,
        name: str,
        position: str,
        experience_level: str,
        email: str = "",
        phone: str = ""
    ):
        """create a new candidate profile
        
        Args:
            candidate_id: Unique identifier for the candidate
            name: Full name of the candidate
            position: Position they are interviewing for
            experience_level: Their experience level (entry, mid, senior, etc.)
            email: Email address (optional)
            phone: Phone number (optional)
        """
        logger.info("create candidate - ID: %s, name: %s, position: %s, experience: %s", candidate_id, name, position, experience_level)
        result = DB.create_candidate(candidate_id, name, position, experience_level, email, phone)
        if result is None:
            return "Failed to create candidate profile"
        
        self._candidate_details = {
            CandidateDetails.CANDIDATE_ID: result.candidate_id,
            CandidateDetails.NAME: result.name,
            CandidateDetails.POSITION: result.position,
            CandidateDetails.EXPERIENCE_LEVEL: result.experience_level,
            CandidateDetails.EMAIL: result.email,
            CandidateDetails.PHONE: result.phone,
            CandidateDetails.INTERVIEW_STATUS: result.interview_status
        }
        
        self._current_phase = InterviewPhase.PROFILE_CREATED
        
        return "Candidate profile created successfully! Now, please share your resume so I can personalize our conversation. You can copy and paste your resume text here."
    
    @function_tool
    async def record_interview_question(
        self,
        context: RunContext,
        question: str,
        answer: str = "",
        score: int = 0,
        notes: str = ""
    ):
        """record an interview question and response
        
        Args:
            question: The interview question asked
            answer: The candidate's answer (optional)
            score: Score for the answer from 1-10 (optional)
            notes: Additional notes about the response (optional)
        """
        candidate_id = self._candidate_details[CandidateDetails.CANDIDATE_ID]
        if not candidate_id:
            return "No candidate profile found. Please create or lookup a candidate first."
        
        logger.info("recording interview question for candidate: %s", candidate_id)
        result = DB.save_interview_question(candidate_id, question, answer, score, notes)
        self._interview_questions.append(result)
        
        return f"Interview question recorded successfully. Question ID: {result.question_id}"
    
    @function_tool
    async def update_interview_status(
        self,
        context: RunContext,
        status: str
    ):
        """update the interview status for the current candidate
        
        Args:
            status: New status (scheduled, in_progress, completed, cancelled)
        """
        candidate_id = self._candidate_details[CandidateDetails.CANDIDATE_ID]
        if not candidate_id:
            return "No candidate profile found. Please create or lookup a candidate first."
        
        logger.info("updating interview status for candidate %s to %s", candidate_id, status)
        success = DB.update_candidate_status(candidate_id, status)
        
        if success:
            self._candidate_details[CandidateDetails.INTERVIEW_STATUS] = status
            return f"Interview status updated to: {status}"
        else:
            return "Failed to update interview status"
    
    @function_tool
    async def upload_resume(
        self,
        context: RunContext,
        resume_text: str,
        file_type: str = "txt",
        filename: str = "resume.txt"
    ):
        """Process uploaded resume text and extract information
        
        Args:
            resume_text: The content of the resume
            file_type: Type of file (txt, pdf, docx)
            filename: Original filename
        """
        candidate_id = self._candidate_details[CandidateDetails.CANDIDATE_ID]
        if not candidate_id:
            return "No candidate profile found. Please create a candidate profile first."
        
        if not rag_system:
            return "Resume analysis system not available. Please contact support."
        
        try:
            # Process resume directly from text (no storage needed)
            skills = rag_system.analyzer.extract_skills(resume_text)
            experience_years = rag_system.analyzer.estimate_experience_years(resume_text)
            
            # Create minimal resume info
            from resume_rag import ResumeInfo
            resume_info = ResumeInfo(
                candidate_id=candidate_id,
                raw_text=resume_text[:1000],
                skills=skills,
                experience=["Professional experience"],
                education=["Education background"],
                projects=["Projects from resume"],
                summary=f"Candidate with {len(skills)} technical skills",
                years_experience=experience_years
            )
            
            # Extract candidate name from resume
            self._candidate_name_from_resume = rag_system.analyzer.extract_candidate_name(resume_text)
            logger.info(f"Extracted candidate name from resume: {self._candidate_name_from_resume}")
            
            logger.info(f"Resume processing completed in <1 second")
            
            # Update database with resume information (no storage path)
            skills_json = json.dumps(resume_info.skills)
            success = DB.update_candidate_resume(
                candidate_id,
                "",  # No storage path needed
                resume_info.summary,
                skills_json
            )
            
            if success:
                self._resume_processed = True
                self._current_phase = InterviewPhase.RESUME_UPLOADED
                position = self._candidate_details[CandidateDetails.POSITION]
                logger.info(f"Resume processed successfully. Position: {position}")
                
                # Generate questions instantly without LLM
                self._generated_questions = rag_system.generate_fast_questions(3)
                logger.info(f"Generated {len(self._generated_questions)} questions instantly")
                
                # Return personalized greeting with candidate's name from resume
                name_to_use = self._candidate_name_from_resume or self._candidate_details[CandidateDetails.NAME]
                return f"Perfect! Hi {name_to_use}! Nice to meet you. I've reviewed your resume and I'm excited to learn more about your background. Let's start - can you give me a brief introduction about yourself?"
            else:
                return "Failed to save resume information to database."
                
        except Exception as e:
            logger.error(f"Error processing resume: {e}")
            return f"Error processing resume: {str(e)}"
    
    @function_tool
    async def get_resume_based_question(
        self,
        context: RunContext,
        question_number: int = 1
    ):
        """Get a quick resume-based interview question"""
        if not self._resume_processed:
            return "Please upload your resume first."
        
        # Use pre-generated questions or fallback
        if self._generated_questions:
            question_index = question_number - 1
            if 0 <= question_index < len(self._generated_questions):
                return self._generated_questions[question_index]
        
        # Simple fallback questions
        fallback_questions = [
            "Tell me about your most relevant technical experience.",
            "What's the most challenging project you've worked on?",
            "How do you approach learning new technologies?",
            "Describe a time you solved a difficult problem.",
            "What are your career goals?"
        ]
        
        question_index = (question_number - 1) % len(fallback_questions)
        return fallback_questions[question_index]
    
    @function_tool
    async def analyze_answer_with_resume(
        self,
        context: RunContext,
        question: str,
        candidate_answer: str
    ):
        """Analyze candidate's answer in context of their resume
        
        Args:
            question: The interview question that was asked
            candidate_answer: The candidate's response
        """
        if not self._resume_processed or not rag_system:
            return "Resume analysis not available. Please upload resume first."
        
        try:
            analysis = rag_system.answer_question_with_context(question, candidate_answer)
            
            # Record the Q&A in database
            candidate_id = self._candidate_details[CandidateDetails.CANDIDATE_ID]
            DB.save_interview_question(candidate_id, question, candidate_answer, 0, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing answer: {e}")
            return "Thank you for your answer. Let's continue with the next question."
    
    @function_tool
    async def advance_interview_phase(
        self,
        context: RunContext,
        current_response: str = ""
    ):
        """Advance to the next interview phase and ask relevant follow-up questions based on candidate's response
        
        Args:
            current_response: The candidate's actual response to build upon
        """
        if self._current_phase == InterviewPhase.RESUME_UPLOADED or self._current_phase == InterviewPhase.PERSONALIZED_GREETING:
            self._current_phase = InterviewPhase.INTRODUCTION
            return "Great! Now tell me about yourself - what's your background and what motivates you in your software development career?"
        
        elif self._current_phase == InterviewPhase.INTRODUCTION:
            self._current_phase = InterviewPhase.PROJECTS
            # Build on what they just said about their background
            if current_response and len(current_response.strip()) > 5:
                return f"That's interesting! Based on what you mentioned about {current_response[:50]}..., can you tell me about a specific project you've worked on that relates to this experience?"
            else:
                return "That's wonderful! Now I'd love to hear about your projects. Can you tell me about a specific project you've worked on that you're particularly proud of?"
        
        elif self._current_phase == InterviewPhase.PROJECTS:
            self._current_phase = InterviewPhase.PROJECTS_SKILLS_QUESTIONS
            # Ask follow-up questions based on the project they mentioned
            if current_response and len(current_response.strip()) > 10:
                return f"That sounds like an impressive project! You mentioned {current_response[:60]}... - what specific technologies or programming languages did you use, and what was the most challenging part?"
            else:
                return "That's interesting! What specific technologies or skills did you use in that project, and what challenges did you face?"
        
        elif self._current_phase == InterviewPhase.PROJECTS_SKILLS_QUESTIONS:
            self._current_phase = InterviewPhase.EXPERIENCE
            # Connect to their technical skills they just mentioned
            if current_response and len(current_response.strip()) > 10:
                return f"Excellent! The {current_response[:40]}... skills you mentioned are valuable. Now let's talk about your professional experience - how have you applied these skills in your career?"
            else:
                return "Excellent! Now let's talk about your professional experience. Can you walk me through your career journey and your most impactful roles?"
        
        elif self._current_phase == InterviewPhase.EXPERIENCE:
            self._current_phase = InterviewPhase.ACHIEVEMENTS
            # Build on their career experience
            if current_response and len(current_response.strip()) > 10:
                return f"That's great experience! From what you shared about {current_response[:50]}..., what specific achievement or accomplishment are you most proud of?"
            else:
                return "That's great experience! Now I'd like to hear about your achievements. What accomplishment are you most proud of in your career?"
        
        elif self._current_phase == InterviewPhase.ACHIEVEMENTS:
            self._current_phase = InterviewPhase.WRAP_UP
            # Acknowledge their achievement
            if current_response and len(current_response.strip()) > 10:
                return f"That's really impressive - {current_response[:50]}... shows great skill! Do you have any questions about the role or the company before we wrap up?"
            else:
                return "Thank you for sharing all that information with me! Do you have any questions about the role or the company before we wrap up?"
        
        elif self._current_phase == InterviewPhase.WRAP_UP:
            self._current_phase = InterviewPhase.COMPLETED
            return "It was great talking with you today! We'll be in touch soon regarding next steps. Have a wonderful day!"
        
        return "Thank you for your response. Let's continue with our discussion."

    @function_tool
    async def load_recent_candidate(self, context: RunContext):
        """Load the most recently created candidate for the interview"""
        try:
            # Get the most recent candidate from database
            recent_candidate = DB.get_most_recent_candidate()
            
            if recent_candidate:
                # Load candidate details
                self._candidate_details = {
                    CandidateDetails.CANDIDATE_ID: recent_candidate.candidate_id,
                    CandidateDetails.NAME: recent_candidate.name,
                    CandidateDetails.POSITION: recent_candidate.position,
                    CandidateDetails.EXPERIENCE_LEVEL: recent_candidate.experience_level,
                    CandidateDetails.EMAIL: recent_candidate.email,
                    CandidateDetails.PHONE: recent_candidate.phone,
                    CandidateDetails.INTERVIEW_STATUS: recent_candidate.interview_status
                }
                
                # Set phase to personalized greeting (not asking for introduction yet)
                self._current_phase = InterviewPhase.PERSONALIZED_GREETING
                
                # Parse skills if available
                if recent_candidate.skills:
                    try:
                        import json
                        skills_list = json.loads(recent_candidate.skills)
                        skills_summary = ", ".join(skills_list[:3]) if skills_list else "various technical skills"
                    except:
                        skills_summary = "various technical skills"
                else:
                    skills_summary = "various technical skills"
                
                logger.info(f"Loaded recent candidate: {recent_candidate.name} ({recent_candidate.candidate_id})")
                
                # Return ONLY personalized greeting - let advance_interview_phase handle the questions
                return f"Hi {recent_candidate.name}! Nice to meet you. I've reviewed your resume and can see you're applying for a {recent_candidate.position} role with skills in {skills_summary}. I'm excited to learn more about you!"
            else:
                return "Welcome! I don't see any recent resume uploads. Please make sure you've uploaded your resume first, then we can begin the interview."
                
        except Exception as e:
            logger.error(f"Error loading recent candidate: {e}")
            return "Welcome! Let's start our interview. Can you please tell me your name and the position you're applying for?"
    
    @function_tool
    async def generate_interview_report(self, context: RunContext):
        """Generate a comprehensive interview analysis report using LLM and save to database"""
        try:
            # Get all interview questions and answers for this candidate
            if not self._candidate_details.get(CandidateDetails.CANDIDATE_ID):
                return "No candidate information available for report generation."
                
            candidate_id = self._candidate_details[CandidateDetails.CANDIDATE_ID]
            interview_data = DB.get_interview_questions(candidate_id)
            
            if not interview_data:
                return "No interview data found for report generation."
            
            # Prepare conversation transcript
            conversation_text = ""
            for qa in interview_data:
                conversation_text += f"Question: {qa.question}\n"
                if qa.answer:
                    conversation_text += f"Answer: {qa.answer}\n\n"
            
            # Get candidate details
            candidate_name = self._candidate_details[CandidateDetails.NAME]
            position = self._candidate_details[CandidateDetails.POSITION]
            experience_level = self._candidate_details[CandidateDetails.EXPERIENCE_LEVEL]
            
            # Create comprehensive analysis prompt
            analysis_prompt = f"""
            You are an expert HR interviewer analyzing a complete interview transcript. Please provide a comprehensive assessment of the candidate.
            
            CANDIDATE INFORMATION:
            - Name: {candidate_name}
            - Position Applied: {position}
            - Experience Level: {experience_level}
            
            INTERVIEW TRANSCRIPT:
            {conversation_text}
            
            Please analyze this interview and provide a detailed report in this EXACT JSON format:
            {{
                "communication_score": [1-10],
                "technical_score": [1-10],
                "soft_skills_score": [1-10],
                "overall_score": [1-10],
                "strengths": ["strength1 with example", "strength2 with example", "strength3 with example"],
                "areas_for_improvement": ["area1", "area2"],
                "technical_competencies": ["tech1", "tech2", "tech3"],
                "hiring_recommendation": "Strong Hire|Hire|Maybe|No Hire",
                "cultural_fit_analysis": "detailed analysis of cultural fit",
                "salary_recommendation": "salary range and level suggestion",
                "next_steps": "recommended next steps in hiring process",
                "detailed_analysis": "comprehensive analysis covering communication skills, technical competency, soft skills, specific responses, and overall assessment with specific examples from the conversation"
            }}
            
            Provide specific examples from the candidate's responses to support your analysis.
            """
            
            # Generate LLM analysis
            try:
                # Use the same RAG system that's already available
                if rag_system:
                    try:
                        # Use existing Gemini configuration through RAG system
                        response = rag_system.llm.invoke(analysis_prompt)
                        analysis_text = str(response.content)
                        
                        # Try to parse JSON response
                        import json
                        import re
                        
                        logger.info(f"AI Analysis Response (first 500 chars): {analysis_text[:500]}...")
                        
                        # Extract JSON from response - try multiple patterns
                        json_patterns = [
                            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested braces
                            r'\{.*\}',  # Original pattern
                            r'```json\s*\{.*?\}\s*```',  # JSON in code blocks
                        ]
                        
                        analysis_data = None
                        json_text = None
                        
                        for pattern in json_patterns:
                            json_match = re.search(pattern, analysis_text, re.DOTALL)
                            if json_match:
                                json_text = json_match.group()
                                # Clean up code block markers if present
                                json_text = re.sub(r'```json\s*', '', json_text)
                                json_text = re.sub(r'\s*```', '', json_text)
                                
                                try:
                                    analysis_data = json.loads(json_text)
                                    logger.info(f"Successfully parsed JSON with pattern: {pattern}")
                                    break
                                except json.JSONDecodeError as je:
                                    logger.warning(f"JSON parsing failed for pattern {pattern}: {je}")
                                    continue
                        
                        if analysis_data:
                            # Save to database
                            report = DB.save_interview_report(
                                candidate_id=candidate_id,
                                candidate_name=candidate_name,
                                position=position,
                                communication_score=analysis_data.get('communication_score', 5),
                                technical_score=analysis_data.get('technical_score', 5),
                                soft_skills_score=analysis_data.get('soft_skills_score', 5),
                                overall_score=analysis_data.get('overall_score', 5),
                                full_analysis_report=analysis_data.get('detailed_analysis', analysis_text),
                                strengths=analysis_data.get('strengths', []),
                                areas_for_improvement=analysis_data.get('areas_for_improvement', []),
                                technical_competencies=analysis_data.get('technical_competencies', []),
                                hiring_recommendation=analysis_data.get('hiring_recommendation', 'Maybe'),
                                cultural_fit_analysis=analysis_data.get('cultural_fit_analysis', ''),
                                salary_recommendation=analysis_data.get('salary_recommendation', ''),
                                next_steps=analysis_data.get('next_steps', ''),
                                total_questions=len(interview_data)
                            )
                            
                            if report:
                                logger.info(f"Generated and saved interview analysis report for candidate: {candidate_id}")
                                return f"""🎯 INTERVIEW ANALYSIS COMPLETED!
                                
✅ Report Generated for: {candidate_name}
📊 Overall Score: {analysis_data.get('overall_score', 5)}/10
🎯 Recommendation: {analysis_data.get('hiring_recommendation', 'Maybe')}
📝 Report ID: {report.report_id}

{analysis_data.get('detailed_analysis', 'Analysis completed successfully.')}

💾 Report saved to database for HR review."""
                            else:
                                logger.error(f"Failed to save report to database for candidate: {candidate_id}")
                                return f"Analysis completed but failed to save to database. Here's the analysis:\n\n{analysis_text}"
                        else:
                            logger.warning(f"Could not parse JSON from AI response for candidate: {candidate_id}")
                            # Improved fallback: analyze interview content for better scoring
                            improved_scores = self._analyze_interview_content(interview_data, analysis_text)
                            
                            report = DB.save_interview_report(
                                candidate_id=candidate_id,
                                candidate_name=candidate_name,
                                position=position,
                                communication_score=improved_scores['communication_score'],
                                technical_score=improved_scores['technical_score'],
                                soft_skills_score=improved_scores['soft_skills_score'],
                                overall_score=improved_scores['overall_score'],
                                full_analysis_report=analysis_text,
                                strengths=improved_scores['strengths'],
                                areas_for_improvement=improved_scores['areas_for_improvement'],
                                technical_competencies=improved_scores['technical_competencies'],
                                hiring_recommendation=improved_scores['hiring_recommendation'],
                                total_questions=len(interview_data)
                            )
                            
                            if report:
                                logger.info(f"Generated improved fallback interview analysis report for candidate: {candidate_id}")
                                return f"""🎯 INTERVIEW ANALYSIS COMPLETED!
                            
✅ Report Generated for: {candidate_name}
📊 Overall Score: {improved_scores['overall_score']}/10 (content-based analysis)
🎯 Recommendation: {improved_scores['hiring_recommendation']}
📝 Report ID: {report.report_id}

{analysis_text}

💾 Report saved to database for HR review.

⚠️ Note: Scores based on interview content analysis due to AI parsing limitations."""
                            else:
                                return f"Analysis generated but couldn't parse structured data and failed to save. Raw analysis:\n\n{analysis_text}"
                            
                    except Exception as llm_error:
                        logger.error(f"LLM analysis failed: {llm_error}")
                        return self._generate_basic_report(candidate_name, position, interview_data)
                else:
                    return self._generate_basic_report(candidate_name, position, interview_data)
                
            except Exception as e:
                logger.error(f"Error generating LLM analysis: {e}")
                # Fallback to basic report
                return self._generate_basic_report(candidate_name, position, interview_data)
                
        except Exception as e:
            logger.error(f"Error generating interview report: {e}")
            return f"Error generating report: {str(e)}"
    
    def _generate_basic_report(self, candidate_name, position, interview_data):
        """Generate a basic report without LLM if API fails"""
        report = f"""
        ## BASIC INTERVIEW REPORT
        
        **Candidate:** {candidate_name}
        **Position:** {position}
        **Total Questions Asked:** {len(interview_data)}
        **Interview Date:** {interview_data[0].created_at if interview_data else 'N/A'}
        
        ### Questions & Responses Summary:
        """
        
        for i, qa in enumerate(interview_data, 1):
            report += f"""
        
        **Q{i}:** {qa.question}
        **A{i}:** {qa.answer or 'No response recorded'}
        """
        
        report += """
        
        ### Notes:
        - This is a basic report. Full LLM analysis was unavailable.
        - Manual review recommended for detailed assessment.
        """
        
        return report
        
    def _analyze_interview_content(self, interview_data, analysis_text):
        """Analyze interview content for improved scoring when LLM parsing fails"""
        if not interview_data:
            return {
                'communication_score': 3,
                'technical_score': 3,
                'soft_skills_score': 3,
                'overall_score': 3,
                'strengths': ["Interview data unavailable"],
                'areas_for_improvement': ["Complete interview required for assessment"],
                'technical_competencies': ["Assessment pending"],
                'hiring_recommendation': "No Hire"
            }
        
        # Count answered vs unanswered questions
        answered_questions = sum(1 for qa in interview_data if qa.answer and qa.answer.strip())
        total_questions = len(interview_data)
        answer_ratio = answered_questions / total_questions if total_questions > 0 else 0
        
        # Calculate average answer length (indicates engagement)
        answer_lengths = [len(qa.answer) if qa.answer else 0 for qa in interview_data]
        avg_answer_length = sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0
        
        # Basic content analysis
        all_answers = " ".join([qa.answer or "" for qa in interview_data]).lower()
        
        # Technical keyword scoring
        technical_keywords = [
            'programming', 'coding', 'python', 'javascript', 'react', 'node', 'database',
            'algorithm', 'data structure', 'api', 'framework', 'library', 'git', 'sql',
            'aws', 'cloud', 'docker', 'testing', 'debug', 'performance', 'optimization'
        ]
        technical_mentions = sum(1 for keyword in technical_keywords if keyword in all_answers)
        
        # Communication quality indicators
        communication_indicators = [
            'example', 'experience', 'project', 'team', 'worked', 'developed',
            'implemented', 'achieved', 'improved', 'learned', 'challenge'
        ]
        communication_mentions = sum(1 for indicator in communication_indicators if indicator in all_answers)
        
        # Calculate scores based on actual content
        # Communication score (1-10) based on answer ratio and quality indicators
        communication_score = min(10, max(1, int(
            (answer_ratio * 5) +  # 50% weight for answering questions
            (min(communication_mentions, 10) * 0.3) +  # 30% for communication indicators
            (min(avg_answer_length / 50, 5) * 0.2)  # 20% for answer depth
        )))
        
        # Technical score based on technical content
        technical_score = min(10, max(1, int(
            (answer_ratio * 3) +  # 30% for basic engagement
            (min(technical_mentions, 15) * 0.4) +  # 40% for technical mentions
            (min(avg_answer_length / 40, 6) * 0.3)  # 30% for detailed responses
        )))
        
        # Soft skills based on engagement and communication
        soft_skills_score = min(10, max(1, int(
            (answer_ratio * 4) +  # 40% for participation
            (min(communication_mentions, 8) * 0.4) +  # 40% for examples/experience
            (2 if avg_answer_length > 30 else 1) * 0.2  # 20% for detailed responses
        )))
        
        # Overall score as weighted average
        overall_score = int((communication_score * 0.3 + technical_score * 0.4 + soft_skills_score * 0.3))
        
        # Determine recommendation based on overall score
        if overall_score >= 8:
            hiring_recommendation = "Strong Hire"
        elif overall_score >= 7:
            hiring_recommendation = "Hire"
        elif overall_score >= 5:
            hiring_recommendation = "Maybe"
        else:
            hiring_recommendation = "No Hire"
        
        # Generate realistic strengths and areas based on content
        strengths = []
        areas_for_improvement = []
        technical_competencies = []
        
        if answer_ratio >= 0.8:
            strengths.append("Good engagement and participation in interview")
        if technical_mentions >= 5:
            strengths.append("Demonstrates technical knowledge and experience")
            technical_competencies.append("Technical terminology usage")
        if avg_answer_length >= 50:
            strengths.append("Provides detailed responses with examples")
        
        if answer_ratio < 0.6:
            areas_for_improvement.append("More active participation and detailed responses needed")
        if technical_mentions < 3:
            areas_for_improvement.append("Could demonstrate more technical depth")
        if avg_answer_length < 30:
            areas_for_improvement.append("Provide more specific examples and details")
        
        # Default fallbacks if no specific areas identified
        if not strengths:
            strengths = ["Completed interview process"]
        if not areas_for_improvement:
            areas_for_improvement = ["Continue developing technical communication skills"]
        if not technical_competencies:
            technical_competencies = ["Assessment requires more detailed responses"]
        
        return {
            'communication_score': communication_score,
            'technical_score': technical_score,
            'soft_skills_score': soft_skills_score,
            'overall_score': overall_score,
            'strengths': strengths[:3],  # Limit to top 3
            'areas_for_improvement': areas_for_improvement[:3],
            'technical_competencies': technical_competencies[:3],
            'hiring_recommendation': hiring_recommendation
        }
    
    @function_tool
    async def search_interview_reports(self, 
                                     context: RunContext,
                                     search_query: str = "",
                                     position_filter: str = "",
                                     min_score: int = 0):
        """Search for interview reports by candidate name, position, or score
        
        Args:
            search_query: Candidate name to search for
            position_filter: Filter by position (optional)
            min_score: Minimum overall score (1-10)
        """
        try:
            reports = DB.search_interview_reports(
                search_query=search_query,
                position_filter=position_filter,
                min_score=min_score,
                limit=20
            )
            
            if not reports:
                return f"No interview reports found for search: '{search_query}'"
            
            # Format results
            results = f"""🔍 INTERVIEW REPORTS SEARCH RESULTS
            
📊 Found {len(reports)} reports:

"""
            
            for i, report in enumerate(reports, 1):
                score_emoji = "🎆" if report.overall_score >= 9 else "🎉" if report.overall_score >= 8 else "👍" if report.overall_score >= 7 else "👆" if report.overall_score >= 6 else "😐"
                
                results += f"""
{i}. 👤 {report.candidate_name}
   💼 Position: {report.position}
   {score_emoji} Overall Score: {report.overall_score}/10 ({report.performance_rating})
   🎯 Recommendation: {report.hiring_recommendation}
   📅 Interview Date: {report.interview_date[:10] if report.interview_date else 'N/A'}
   📝 Questions Asked: {report.total_questions}
   📈 Skills Average: {report.avg_skill_score}/10
   🏢 Report ID: {report.report_id}
"""
            
            results += "\n🔍 Use 'get_detailed_report' with Report ID to see full analysis."
            return results
            
        except Exception as e:
            logger.error(f"Error searching interview reports: {e}")
            return f"Error searching reports: {str(e)}"
    
    @function_tool
    async def get_detailed_report(self, context: RunContext, report_id: str):
        """Get detailed interview report by ID
        
        Args:
            report_id: The unique report ID to retrieve
        """
        try:
            report = DB.get_full_interview_report(report_id)
            
            if not report:
                return f"No interview report found with ID: {report_id}"
            
            # Format detailed report
            detailed_result = f"""
📄 DETAILED INTERVIEW ANALYSIS REPORT

👤 Candidate: {report.candidate_name}
💼 Position: {report.position}
📅 Interview Date: {report.interview_date[:16] if report.interview_date else 'N/A'}
🔗 Report ID: {report.report_id}

📈 SCORES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🗨️ Communication: {report.communication_score}/10
💻 Technical Skills: {report.technical_score}/10
🤝 Soft Skills: {report.soft_skills_score}/10
🎯 Overall Score: {report.overall_score}/10

🎆 HIRING RECOMMENDATION: {report.hiring_recommendation}

💪 STRENGTHS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            
            for i, strength in enumerate(report.strengths, 1):
                detailed_result += f"{i}. {strength}\n"
            
            detailed_result += f"\n📈 AREAS FOR IMPROVEMENT:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            for i, area in enumerate(report.areas_for_improvement, 1):
                detailed_result += f"{i}. {area}\n"
            
            detailed_result += f"\n💻 TECHNICAL COMPETENCIES:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            for i, tech in enumerate(report.technical_competencies, 1):
                detailed_result += f"{i}. {tech}\n"
            
            if report.cultural_fit_analysis:
                detailed_result += f"\n🏢 CULTURAL FIT ANALYSIS:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{report.cultural_fit_analysis}\n"
            
            if report.salary_recommendation:
                detailed_result += f"\n💰 SALARY RECOMMENDATION:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{report.salary_recommendation}\n"
            
            if report.next_steps:
                detailed_result += f"\n📨 NEXT STEPS:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{report.next_steps}\n"
            
            detailed_result += f"\n📝 FULL AI ANALYSIS:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{report.full_analysis_report}\n"
            
            detailed_result += f"\n📆 INTERVIEW METADATA:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            detailed_result += f"Questions Asked: {report.total_questions}\n"
            if report.interview_duration_minutes > 0:
                detailed_result += f"Duration: {report.interview_duration_minutes} minutes\n"
            detailed_result += f"Generated By: {report.report_generated_by}\n"
            detailed_result += f"Created: {report.created_at[:16] if report.created_at else 'N/A'}\n"
            
            return detailed_result
            
        except Exception as e:
            logger.error(f"Error getting detailed report: {e}")
            return f"Error retrieving detailed report: {str(e)}"
    
    @function_tool
    async def end_interview_and_generate_report(self, context: RunContext):
        """End the current interview and automatically generate a comprehensive report"""
        try:
            if not self._candidate_details.get(CandidateDetails.CANDIDATE_ID):
                return "No interview session found to end."
            
            candidate_name = self._candidate_details[CandidateDetails.NAME]
            
            # Update interview status to completed
            candidate_id = self._candidate_details[CandidateDetails.CANDIDATE_ID]
            success = DB.update_candidate_status(candidate_id, "completed")
            
            if success:
                self._candidate_details[CandidateDetails.INTERVIEW_STATUS] = "completed"
            
            # Generate the comprehensive report
            report_result = await self.generate_interview_report(context)
            
            # Create a final summary message
            final_message = f"""
🎯 INTERVIEW COMPLETED!

Thank you {candidate_name} for your time today. I've enjoyed our conversation and learning about your background and experience.

{report_result}

Your interview has been recorded and our team will review the analysis. We'll be in touch soon regarding next steps.

Have a wonderful day!
            """
            
            # Mark the interview phase as completed
            self._current_phase = InterviewPhase.COMPLETED
            
            return final_message
            
        except Exception as e:
            logger.error(f"Error ending interview and generating report: {e}")
            return f"Interview ended, but there was an issue generating the report: {str(e)}. Your interview responses have been saved."
    
    @function_tool
    async def check_for_interview_end_request(self, context: RunContext, user_message: str):
        """Check if the user wants to end the interview based on their message
        
        Args:
            user_message: The user's spoken or typed message
        """
        # Keywords that indicate user wants to end the interview
        end_keywords = [
            "end the interview", "end interview", "finish the interview", 
            "finish interview", "stop the interview", "stop interview",
            "wrap up", "that's all", "conclude the interview",
            "generate report", "create report", "finish up",
            "done with interview", "interview done", "we're done"
        ]
        
        user_message_lower = user_message.lower().strip()
        
        # Check if any end keywords are present
        for keyword in end_keywords:
            if keyword in user_message_lower:
                logger.info(f"Interview end requested by user with phrase: '{keyword}'")
                return await self.end_interview_and_generate_report(context)
        
        # If no end request detected, return None to continue normal flow
        return None
    
    def has_candidate(self):
        return self._candidate_details[CandidateDetails.CANDIDATE_ID] != ""