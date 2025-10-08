from __future__ import annotations
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm
)
from livekit.plugins import google
from dotenv import load_dotenv
from api import AssistantFnc, CandidateDetails, InterviewPhase
from prompts import WELCOME_MESSAGE, INSTRUCTIONS, LOOKUP_CANDIDATE_MESSAGE
import os
import logging
import json

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Suppress Google Realtime API warnings about unsupported features
logging.getLogger("livekit.plugins.google").setLevel(logging.ERROR)

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    
    # Create the realtime model for LiveKit integration with optimized settings
    model = google.beta.realtime.RealtimeModel(
        model="gemini-2.0-flash-exp",
        voice="Aoede",  # Changed to a more reliable voice
        temperature=0.3,  # Lower temperature for faster, more focused responses
        instructions=INSTRUCTIONS + " Keep responses concise and direct. Respond quickly without unnecessary elaboration."
    )
    
    # Create function context
    assistant_fnc = AssistantFnc()
    
    # Create agent with the realtime model and function tools
    agent = Agent(
        instructions=INSTRUCTIONS,
        llm=model,
        tools=[
            assistant_fnc.load_recent_candidate,  # First tool to load candidate info
            assistant_fnc.advance_interview_phase,  # Primary tool for interview progression
            assistant_fnc.record_interview_question, 
            assistant_fnc.generate_interview_report,  # Generate comprehensive analysis report
            assistant_fnc.end_interview_and_generate_report,  # End interview and create report
            assistant_fnc.check_for_interview_end_request,  # Check if user wants to end interview
            assistant_fnc.search_interview_reports,  # Search existing reports
            assistant_fnc.get_detailed_report,  # Get full report details
            assistant_fnc.lookup_candidate, 
            assistant_fnc.get_candidate_details, 
            assistant_fnc.process_resume_and_start_interview,  # Backup for manual resume processing
            assistant_fnc.create_candidate_profile,  # Backup for manual entry
            assistant_fnc.create_candidate,  # Keep for compatibility
            assistant_fnc.update_interview_status,
            assistant_fnc.upload_resume,  # Keep for compatibility
            assistant_fnc.get_resume_based_question,
            assistant_fnc.analyze_answer_with_resume
        ],
    )
    
    # Create agent session 
    session = AgentSession(
        llm=model,
    )
    
    # Start the session
    await session.start(agent=agent, room=ctx.room)
    
    # Automatically try to load recent candidate information first
    try:
        await assistant_fnc.load_recent_candidate(None)
        logger.info("Successfully loaded recent candidate information")
        
        # If we have candidate info, start with personalized greeting
        if assistant_fnc.has_candidate():
            candidate_name = assistant_fnc._candidate_details[CandidateDetails.NAME]
            position = assistant_fnc._candidate_details[CandidateDetails.POSITION]
            
            # Create explicit welcome message with phase instruction
            welcome_msg = f"""You are starting an interview with {candidate_name} who is applying for a {position} role. 
            You have successfully loaded their resume information. 
            
            Start the interview with this exact greeting: "Hi {candidate_name}! Nice to meet you. I've reviewed your resume and can see you're applying for a {position} role. I'm excited to learn more about you!"
            
            Then wait for their response before proceeding to the introduction phase.
            
            Follow this exact sequence:
            1. Greeting (current phase) - Just greet them personally
            2. Introduction - Ask about background and motivation  
            3. Projects - Ask about specific projects
            4. Skills/Tech questions - Deep dive into project technologies
            5. Experience - Professional experience discussion
            6. Achievements - Their proudest accomplishments
            7. Wrap-up - Final questions
            
            You are currently in the GREETING phase. Start with the personalized greeting above."""
        else:
            welcome_msg = "Hello! I'm your AI interviewer. Let me check if you've uploaded your resume so I can personalize our interview."
            
    except Exception as e:
        logger.warning(f"Could not load candidate information: {e}")
        welcome_msg = "Hello! I'm your AI interviewer for today. Please make sure you've uploaded your resume so I can personalize our interview for you."
    
    await session.generate_reply(instructions=welcome_msg)
    
    # Note: With the new Agent/AgentSession architecture, 
    # conversation handling is managed differently.
    # The agent will automatically handle user inputs through its tools and LLM integration.
    # Interview questions and responses are managed through the interview function tools.
    
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))