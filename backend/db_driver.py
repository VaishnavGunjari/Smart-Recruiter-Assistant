import os
import tempfile
from typing import Optional
from dataclasses import dataclass
from supabase import create_client, Client
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

@dataclass
class Candidate:
    candidate_id: str
    name: str
    position: str
    experience_level: str
    email: str = ""
    phone: str = ""
    interview_status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    created_at: str = ""
    updated_at: str = ""
    resume_path: str = ""  # Path to uploaded resume
    resume_summary: str = ""  # AI-generated summary
    skills: str = ""  # JSON string of extracted skills

@dataclass
class InterviewQuestion:
    question_id: int
    candidate_id: str
    question: str
    answer: str
    score: int = 0  # 1-10 rating
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

@dataclass
class InterviewReport:
    report_id: str
    candidate_id: str
    candidate_name: str
    position: str
    interview_date: str
    communication_score: int
    technical_score: int
    soft_skills_score: int
    overall_score: int
    full_analysis_report: str
    strengths: list  # JSONB array
    areas_for_improvement: list  # JSONB array
    technical_competencies: list  # JSONB array
    hiring_recommendation: str
    cultural_fit_analysis: str = ""
    salary_recommendation: str = ""
    next_steps: str = ""
    total_questions: int = 0
    interview_duration_minutes: int = 0
    report_generated_by: str = "AI_System"
    created_at: str = ""
    updated_at: str = ""
    performance_rating: str = ""  # For view
    avg_skill_score: float = 0.0  # For view

class DatabaseDriver:
    def __init__(self, use_service_role: bool = False):
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        
        # Use Service Role Key for storage operations, Anon Key for regular operations
        if use_service_role:
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if not supabase_key:
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable must be set for storage operations")
        else:
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            if not supabase_key:
                raise ValueError("SUPABASE_ANON_KEY environment variable must be set")
        
        if not supabase_url:
            raise ValueError("SUPABASE_URL environment variable must be set")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Storage bucket name for resumes
        self.resume_bucket = "resumes"
        
        # Database connection string for direct PostgreSQL operations (optional)
        self.db_url = os.getenv("SUPABASE_DB_URL")

    @contextmanager
    def _get_connection(self):
        """Get a direct PostgreSQL connection for complex operations (optional)"""
        if not self.db_url:
            raise ValueError("SUPABASE_DB_URL is required for direct database connections")
        
        conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
        try:
            yield conn
        finally:
            conn.close()

    def create_candidate(self, candidate_id: str, name: str, position: str, experience_level: str, email: str = "", phone: str = "", resume_path: str = "", resume_summary: str = "", skills: str = "") -> Candidate:
        try:
            data = {
                "candidate_id": candidate_id,
                "name": name,
                "position": position,
                "experience_level": experience_level,
                "email": email,
                "phone": phone,
                "resume_path": resume_path,
                "resume_summary": resume_summary,
                "skills": skills
            }
            
            result = self.supabase.table("candidates").insert(data).execute()
            
            if result.data:
                row = result.data[0]
                return Candidate(
                    candidate_id=row["candidate_id"],
                    name=row["name"],
                    position=row["position"],
                    experience_level=row["experience_level"],
                    email=row.get("email", ""),
                    phone=row.get("phone", ""),
                    interview_status=row.get("interview_status", "scheduled"),
                    created_at=row.get("created_at", ""),
                    updated_at=row.get("updated_at", ""),
                    resume_path=row.get("resume_path", ""),
                    resume_summary=row.get("resume_summary", ""),
                    skills=row.get("skills", "")
                )
            else:
                raise Exception("Failed to create candidate")
        except Exception as e:
            print(f"Error creating candidate: {e}")
            raise

    def get_candidate_by_id(self, candidate_id: str) -> Optional[Candidate]:
        try:
            result = self.supabase.table("candidates").select("*").eq("candidate_id", candidate_id).execute()
            
            if result.data:
                row = result.data[0]
                return Candidate(
                    candidate_id=row["candidate_id"],
                    name=row["name"],
                    position=row["position"],
                    experience_level=row["experience_level"],
                    email=row.get("email", ""),
                    phone=row.get("phone", ""),
                    interview_status=row.get("interview_status", "scheduled"),
                    created_at=row.get("created_at", ""),
                    updated_at=row.get("updated_at", ""),
                    resume_path=row.get("resume_path", ""),
                    resume_summary=row.get("resume_summary", ""),
                    skills=row.get("skills", "")
                )
            return None
        except Exception as e:
            print(f"Error getting candidate: {e}")
            return None
    
    def get_most_recent_candidate(self) -> Optional[Candidate]:
        """Get the most recently created candidate"""
        try:
            result = self.supabase.table("candidates").select("*").order("created_at", desc=True).limit(1).execute()
            
            if result.data:
                row = result.data[0]
                return Candidate(
                    candidate_id=row["candidate_id"],
                    name=row["name"],
                    position=row["position"],
                    experience_level=row["experience_level"],
                    email=row.get("email", ""),
                    phone=row.get("phone", ""),
                    interview_status=row.get("interview_status", "scheduled"),
                    created_at=row.get("created_at", ""),
                    updated_at=row.get("updated_at", ""),
                    resume_path=row.get("resume_path", ""),
                    resume_summary=row.get("resume_summary", ""),
                    skills=row.get("skills", "")
                )
            return None
        except Exception as e:
            print(f"Error getting most recent candidate: {e}")
            return None
    
    def get_all_candidates(self) -> list[Candidate]:
        """Get all candidates from the database"""
        try:
            result = self.supabase.table("candidates").select("*").order("created_at", desc=False).execute()
            
            return [
                Candidate(
                    candidate_id=row["candidate_id"],
                    name=row["name"],
                    position=row["position"],
                    experience_level=row["experience_level"],
                    email=row.get("email", ""),
                    phone=row.get("phone", ""),
                    interview_status=row.get("interview_status", "scheduled"),
                    created_at=row.get("created_at", ""),
                    updated_at=row.get("updated_at", ""),
                    resume_path=row.get("resume_path", ""),
                    resume_summary=row.get("resume_summary", ""),
                    skills=row.get("skills", "")
                )
                for row in result.data
            ]
        except Exception as e:
            print(f"Error getting all candidates: {e}")
            return []
    
    def update_candidate_resume(self, candidate_id: str, resume_path: str, resume_summary: str, skills: str) -> bool:
        """Update candidate with resume information"""
        try:
            result = self.supabase.table("candidates").update({
                "resume_path": resume_path,
                "resume_summary": resume_summary,
                "skills": skills
            }).eq("candidate_id", candidate_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error updating candidate resume: {e}")
            return False
    
    def update_candidate_status(self, candidate_id: str, status: str) -> bool:
        try:
            result = self.supabase.table("candidates").update({"interview_status": status}).eq("candidate_id", candidate_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error updating candidate status: {e}")
            return False
    
    def save_interview_question(self, candidate_id: str, question: str, answer: str = "", score: int = 0, notes: str = "") -> InterviewQuestion:
        try:
            data = {
                "candidate_id": candidate_id,
                "question": question,
                "answer": answer,
                "score": score,
                "notes": notes
            }
            
            result = self.supabase.table("interview_questions").insert(data).execute()
            
            if result.data:
                row = result.data[0]
                return InterviewQuestion(
                    question_id=row["question_id"],
                    candidate_id=row["candidate_id"],
                    question=row["question"],
                    answer=row.get("answer", ""),
                    score=row.get("score", 0),
                    notes=row.get("notes", ""),
                    created_at=row.get("created_at", ""),
                    updated_at=row.get("updated_at", "")
                )
            else:
                raise Exception("Failed to save interview question")
        except Exception as e:
            print(f"Error saving interview question: {e}")
            raise
    
    def get_interview_questions(self, candidate_id: str) -> list[InterviewQuestion]:
        try:
            result = self.supabase.table("interview_questions").select("*").eq("candidate_id", candidate_id).execute()
            
            return [
                InterviewQuestion(
                    question_id=row["question_id"],
                    candidate_id=row["candidate_id"],
                    question=row["question"],
                    answer=row.get("answer", ""),
                    score=row.get("score", 0),
                    notes=row.get("notes", ""),
                    created_at=row.get("created_at", ""),
                    updated_at=row.get("updated_at", "")
                )
                for row in result.data
            ]
        except Exception as e:
            print(f"Error getting interview questions: {e}")
            return []
    
    # Supabase Storage Methods for Resume Files
    
    def upload_resume(self, candidate_id: str, file_data: bytes, filename: str) -> str:
        """Upload resume to Supabase storage and return the storage path"""
        # Create file path with candidate_id as folder
        file_path = f"{candidate_id}/{filename}"
        
        try:
            # First, check if file already exists and remove it
            try:
                file_list = self.supabase.storage.from_(self.resume_bucket).list(candidate_id)
                file_exists = any(f.get('name') == filename for f in file_list)
                
                if file_exists:
                    logger.info(f"File already exists, removing old version: {file_path}")
                    # Remove existing file first
                    self.supabase.storage.from_(self.resume_bucket).remove([file_path])
            except Exception as list_error:
                logger.info(f"Could not check existing files, proceeding with upload: {list_error}")
            
            # Now upload the file
            result = self.supabase.storage.from_(self.resume_bucket).upload(
                path=file_path,
                file=file_data
            )
            
            logger.info(f"Resume uploaded successfully: {file_path}")
            return file_path
            
        except Exception as e:
            # If it's still a duplicate error, try to return the existing file path
            if "409" in str(e) or "Duplicate" in str(e) or "already exists" in str(e):
                logger.info(f"File still exists after removal attempt, using existing: {file_path}")
                return file_path
            else:
                logger.error(f"Error uploading resume to Supabase: {e}")
                raise ValueError(f"Failed to upload resume: {str(e)}")
    
    def download_resume(self, file_path: str) -> bytes:
        """Download resume from Supabase storage"""
        try:
            result = self.supabase.storage.from_(self.resume_bucket).download(file_path)
            logger.info(f"Resume downloaded successfully: {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error downloading resume from Supabase: {e}")
            raise ValueError(f"Failed to download resume: {str(e)}")
    
    def download_resume_to_temp(self, file_path: str) -> str:
        """Download resume from Supabase storage to a temporary file and return temp file path"""
        try:
            # Download file data
            file_data = self.download_resume(file_path)
            
            # Create temporary file
            file_extension = file_path.split('.')[-1] if '.' in file_path else 'tmp'
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}')
            
            # Write data to temp file
            temp_file.write(file_data)
            temp_file.close()
            
            logger.info(f"Resume downloaded to temp file: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error downloading resume to temp file: {e}")
            raise ValueError(f"Failed to download resume to temp file: {str(e)}")
    
    def delete_resume(self, file_path: str) -> bool:
        """Delete resume from Supabase storage"""
        try:
            result = self.supabase.storage.from_(self.resume_bucket).remove([file_path])
            logger.info(f"Resume deleted successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting resume from Supabase: {e}")
            return False
    
    def get_resume_signed_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Get signed URL for secure file access"""
        try:
            result = self.supabase.storage.from_(self.resume_bucket).create_signed_url(
                path=file_path,
                expires_in=expires_in
            )
            return result.get('signedURL', '')
            
        except Exception as e:
            logger.error(f"Error getting signed URL for resume: {e}")
            return ""
    
    def get_resume_public_url(self, file_path: str) -> str:
        """Get public URL for resume (if bucket is public)"""
        try:
            result = self.supabase.storage.from_(self.resume_bucket).get_public_url(file_path)
            return str(result) if result else ""
            
        except Exception as e:
            logger.error(f"Error getting public URL for resume: {e}")
            return ""
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        content_types = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain'
        }
        
        return content_types.get(extension, 'application/octet-stream')
    
    # Interview Reports Methods
    
    def save_interview_report(self, 
                            candidate_id: str,
                            candidate_name: str,
                            position: str,
                            communication_score: int,
                            technical_score: int,
                            soft_skills_score: int,
                            overall_score: int,
                            full_analysis_report: str,
                            strengths: list,
                            areas_for_improvement: list,
                            technical_competencies: list,
                            hiring_recommendation: str,
                            cultural_fit_analysis: str = "",
                            salary_recommendation: str = "",
                            next_steps: str = "",
                            total_questions: int = 0,
                            interview_duration_minutes: int = 0) -> Optional[InterviewReport]:
        """Save comprehensive interview report to database"""
        try:
            data = {
                "candidate_id": candidate_id,
                "candidate_name": candidate_name,
                "position": position,
                "communication_score": communication_score,
                "technical_score": technical_score,
                "soft_skills_score": soft_skills_score,
                "overall_score": overall_score,
                "full_analysis_report": full_analysis_report,
                "strengths": strengths,  # JSONB
                "areas_for_improvement": areas_for_improvement,  # JSONB
                "technical_competencies": technical_competencies,  # JSONB
                "hiring_recommendation": hiring_recommendation,
                "cultural_fit_analysis": cultural_fit_analysis,
                "salary_recommendation": salary_recommendation,
                "next_steps": next_steps,
                "total_questions": total_questions,
                "interview_duration_minutes": interview_duration_minutes
            }
            
            result = self.supabase.table("interview_reports").insert(data).execute()
            
            if result.data:
                row = result.data[0]
                return InterviewReport(
                    report_id=row["report_id"],
                    candidate_id=row["candidate_id"],
                    candidate_name=row["candidate_name"],
                    position=row["position"],
                    interview_date=row.get("interview_date", ""),
                    communication_score=row["communication_score"],
                    technical_score=row["technical_score"],
                    soft_skills_score=row["soft_skills_score"],
                    overall_score=row["overall_score"],
                    full_analysis_report=row["full_analysis_report"],
                    strengths=row.get("strengths", []),
                    areas_for_improvement=row.get("areas_for_improvement", []),
                    technical_competencies=row.get("technical_competencies", []),
                    hiring_recommendation=row["hiring_recommendation"],
                    cultural_fit_analysis=row.get("cultural_fit_analysis", ""),
                    salary_recommendation=row.get("salary_recommendation", ""),
                    next_steps=row.get("next_steps", ""),
                    total_questions=row.get("total_questions", 0),
                    interview_duration_minutes=row.get("interview_duration_minutes", 0),
                    report_generated_by=row.get("report_generated_by", "AI_System"),
                    created_at=row.get("created_at", ""),
                    updated_at=row.get("updated_at", "")
                )
            else:
                raise Exception("Failed to save interview report")
        except Exception as e:
            print(f"Error saving interview report: {e}")
            return None
    
    def get_interview_report_by_candidate(self, candidate_id: str) -> Optional[InterviewReport]:
        """Get interview report for a specific candidate"""
        try:
            result = self.supabase.table("interview_reports").select("*").eq("candidate_id", candidate_id).execute()
            
            if result.data:
                row = result.data[0]  # Get the most recent report
                return InterviewReport(
                    report_id=row["report_id"],
                    candidate_id=row["candidate_id"],
                    candidate_name=row["candidate_name"],
                    position=row["position"],
                    interview_date=row.get("interview_date", ""),
                    communication_score=row["communication_score"],
                    technical_score=row["technical_score"],
                    soft_skills_score=row["soft_skills_score"],
                    overall_score=row["overall_score"],
                    full_analysis_report=row["full_analysis_report"],
                    strengths=row.get("strengths", []),
                    areas_for_improvement=row.get("areas_for_improvement", []),
                    technical_competencies=row.get("technical_competencies", []),
                    hiring_recommendation=row["hiring_recommendation"],
                    cultural_fit_analysis=row.get("cultural_fit_analysis", ""),
                    salary_recommendation=row.get("salary_recommendation", ""),
                    next_steps=row.get("next_steps", ""),
                    total_questions=row.get("total_questions", 0),
                    interview_duration_minutes=row.get("interview_duration_minutes", 0),
                    report_generated_by=row.get("report_generated_by", "AI_System"),
                    created_at=row.get("created_at", ""),
                    updated_at=row.get("updated_at", "")
                )
            return None
        except Exception as e:
            print(f"Error getting interview report: {e}")
            return None
    
    def search_interview_reports(self, 
                               search_query: str = "",
                               position_filter: str = "",
                               min_score: int = 0,
                               hiring_recommendation: str = "",
                               limit: int = 50) -> list[InterviewReport]:
        """Search interview reports with filters"""
        try:
            # Use the summary view for better performance
            query = self.supabase.table("interview_reports_summary").select("*")
            
            # Apply filters
            if search_query:
                # Search in candidate name (case-insensitive)
                query = query.ilike("candidate_name", f"%{search_query}%")
            
            if position_filter:
                query = query.eq("position", position_filter)
            
            if min_score > 0:
                query = query.gte("overall_score", min_score)
            
            if hiring_recommendation:
                query = query.eq("hiring_recommendation", hiring_recommendation)
            
            # Order by interview date (newest first) and limit results
            result = query.order("interview_date", desc=True).limit(limit).execute()
            
            reports = []
            for row in result.data:
                reports.append(InterviewReport(
                    report_id=row["report_id"],
                    candidate_id="",  # Not in summary view
                    candidate_name=row["candidate_name"],
                    position=row["position"],
                    interview_date=row.get("interview_date", ""),
                    communication_score=row["communication_score"],
                    technical_score=row["technical_score"],
                    soft_skills_score=row["soft_skills_score"],
                    overall_score=row["overall_score"],
                    full_analysis_report="",  # Not loaded in summary
                    strengths=[],
                    areas_for_improvement=[],
                    technical_competencies=[],
                    hiring_recommendation=row["hiring_recommendation"],
                    total_questions=row.get("total_questions", 0),
                    created_at=row.get("created_at", ""),
                    performance_rating=row.get("performance_rating", ""),
                    avg_skill_score=row.get("avg_skill_score", 0.0)
                ))
            
            return reports
            
        except Exception as e:
            print(f"Error searching interview reports: {e}")
            return []
    
    def get_full_interview_report(self, report_id: str) -> Optional[InterviewReport]:
        """Get complete interview report with full details"""
        try:
            result = self.supabase.table("interview_reports").select("*").eq("report_id", report_id).execute()
            
            if result.data:
                row = result.data[0]
                return InterviewReport(
                    report_id=row["report_id"],
                    candidate_id=row["candidate_id"],
                    candidate_name=row["candidate_name"],
                    position=row["position"],
                    interview_date=row.get("interview_date", ""),
                    communication_score=row["communication_score"],
                    technical_score=row["technical_score"],
                    soft_skills_score=row["soft_skills_score"],
                    overall_score=row["overall_score"],
                    full_analysis_report=row["full_analysis_report"],
                    strengths=row.get("strengths", []),
                    areas_for_improvement=row.get("areas_for_improvement", []),
                    technical_competencies=row.get("technical_competencies", []),
                    hiring_recommendation=row["hiring_recommendation"],
                    cultural_fit_analysis=row.get("cultural_fit_analysis", ""),
                    salary_recommendation=row.get("salary_recommendation", ""),
                    next_steps=row.get("next_steps", ""),
                    total_questions=row.get("total_questions", 0),
                    interview_duration_minutes=row.get("interview_duration_minutes", 0),
                    report_generated_by=row.get("report_generated_by", "AI_System"),
                    created_at=row.get("created_at", ""),
                    updated_at=row.get("updated_at", "")
                )
            return None
        except Exception as e:
            print(f"Error getting full interview report: {e}")
            return None
