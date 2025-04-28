
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI

class CommandRequest(BaseModel):
    command: str
    context: Optional[dict] = None

class CommandResponse(BaseModel):
    message: str
    status: str
    codeBlock: Optional[str] = None
    codeAnalysis: Optional[List[dict]] = None

def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY", "")
    return ChatGoogleGenerativeAI(model="gemini-", google_api_key=api_key)

def create_github_crew():
    llm = get_llm()
    
    # Code Expert Agent
    code_expert = Agent(
        role="Code Expert",
        goal="Analyze and improve code quality, security, and formatting",
        backstory="You are an experienced software engineer with expertise in code quality and security best practices.",
        verbose=True,
        llm=llm,
    )
    
    # GitHub Operations Agent
    github_ops = Agent(
        role="GitHub Operations Specialist",
        goal="Handle GitHub operations like commits, pushes, and merge conflicts",
        backstory="You manage version control operations and ensure smooth GitHub workflow.",
        verbose=True,
        llm=llm,
    )
    
    # Test Expert Agent
    test_expert = Agent(
        role="Test Engineer",
        goal="Ensure code is properly tested before being pushed",
        backstory="You specialize in testing methodologies and quality assurance.",
        verbose=True,
        llm=llm,
    )
    
    return code_expert, github_ops, test_expert
