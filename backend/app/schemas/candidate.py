from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class Bullet(BaseModel):
    text: str
    metrics: Optional[int] = 0
    source: str


class Education(BaseModel):
    institution: str
    degree: str
    field: str
    start: Optional[str] = ""
    end: Optional[str] = ""
    gpa: Optional[str] = ""
    location: Optional[str] = ""
    source: Optional[str] = ""


class Experience(BaseModel):
    id: Optional[str] = ""
    company: str
    title: str
    location: Optional[str] = ""
    start: Optional[str] = ""
    end: Optional[str] = ""
    bullets: List[Bullet] = []
    source: Optional[str] = ""


class Project(BaseModel):
    id: Optional[str] = ""
    name: str
    tech: List[str] = []
    award: Optional[str] = ""
    links: Dict[str, str] = {}
    bullets: List[Bullet] = []
    source: Optional[str] = ""


class Personal(BaseModel):
    name: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    linkedin: Optional[str] = ""
    github: Optional[str] = ""
    location: Optional[str] = ""


class Achievement(BaseModel):
    title: str
    category: Optional[str] = ""
    description: Optional[str] = ""
    metrics: Optional[List[str]] = []
    links: Optional[List[str]] = []
    source: Optional[str] = ""


class Certification(BaseModel):
    name: str
    issuer: Optional[str] = ""
    year: Optional[str] = ""
    source: Optional[str] = ""


class Candidate(BaseModel):
    personal: Personal
    summary: Optional[Dict[str, Any]] = None
    education: List[Education] = []
    experience: List[Experience] = []
    projects: List[Project] = []
    skills: Dict[str, Any] = {}
    achievements: List[Achievement] = []
    certifications: List[Certification] = []
