from fastapi import FastAPI, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai

from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import engine, Base, SessionLocal
import models

from rag import (
    create_embedding,
    search_knowledge_semantically
)

import os
import json
import re
from difflib import SequenceMatcher


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="NEXUS AI OS"
)


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(bind=engine)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# =========================================================
# GEMINI
# =========================================================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# =========================================================
# DATA MODELS
# =========================================================

class ChatMessage(BaseModel):

    role: str

    text: str


class ChatRequest(BaseModel):

    message: str

    history: list[ChatMessage] = []


class KnowledgeRequest(BaseModel):

    title: str

    content: str

    category: str = "general"

    source: str = ""


class TaskRequest(BaseModel):

    title: str

    completed: bool = False


class TaskActionRequest(BaseModel):

    task_id: int

    completed: bool


class ProjectRequest(BaseModel):

    name: str

    description: str = ""

    technology: str = ""

    status: str = "active"

    progress: int = 0


class NoteRequest(BaseModel):

    title: str

    content: str

    category: str = "General"

    tags: str = ""

    pinned: bool = False

    project_id: int | None = None


class NoteAIRequest(BaseModel):

    title: str = ""

    content: str


# =========================================================
# PROJECT MEMORY
# =========================================================

PROJECT_CONTEXT = """

The user is a CSE BTech student and developer.

Known projects:

1. NEXUS AI OS
- Personal AI operating system.
- React + Vite frontend.
- FastAPI + Python backend.
- Gemini AI integration.
- Knowledge Vault.
- Task management.
- AI Assistant.
- RAG and semantic search.
- Projects and productivity features.

2. Virtual India Explorer
- Interactive virtual/3D India exploration project.
- React-based frontend.
- Uses datasets and visual components.
- Goal is an immersive digital India experience.

3. Indian Traffic Accident Analytics
- Python data analytics project.
- Pandas, NumPy, Matplotlib, Seaborn,
  Plotly and Streamlit.
- Traffic accident dataset.
- Analytics dashboard with maps and insights.

4. 3D Portfolio World
- Bruno Simon-inspired interactive portfolio.
- React Three Fiber / Three.js.
- Blender-generated 3D world and GLB assets.

5. AirWriting / AirCanvas
- Hand gesture based virtual drawing application.
- Python, MediaPipe and OpenCV.

6. RockGuard AI / RockfallGuard
- AI-based rockfall prediction concept for mines.

7. ConsentTracker
- Consent-based location tracking application.
- React, Node.js, Express, Socket.io and maps.

"""


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "NEXUS AI OS Backend is running 🚀"
    }


# =========================================================
# TASK HELPERS
# =========================================================

def get_all_tasks(db):

    return (
        db.query(models.Task)
        .order_by(
            models.Task.created_at.desc()
        )
        .all()
    )


def task_to_dict(task):

    project_name = None

    try:
        if getattr(task, "project", None):
            project_name = task.project.name
    except Exception:
        project_name = None

    return {
        "id": task.id,
        "title": task.title,
        "completed": bool(task.completed),
        "project_id": getattr(task, "project_id", None),
        "project_name": project_name
    }


# =========================================================
# AUTO UPDATE PROJECT PROGRESS FROM LINKED TASKS
# =========================================================

def update_project_progress_from_tasks(db, project_id):

    if not project_id:
        return None

    project = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()

    if not project:
        return None

    linked_tasks = db.query(models.Task).filter(
        models.Task.project_id == project_id
    ).all()

    if not linked_tasks:
        return project

    completed_count = sum(
        1 for task in linked_tasks
        if task.completed
    )

    project.progress = round(
        (completed_count / len(linked_tasks)) * 100
    )

    if project.progress >= 100:
        project.progress = 100

    return project


# =========================================================
# SMART TASK NORMALIZATION
# =========================================================

def normalize_task_text(text):

    if not text:
        return ""

    text = str(text).strip().lower()

    prefixes = [

        r"^mark\s+",

        r"^complete\s+",

        r"^finish\s+",

        r"^done\s+with\s+",

        r"^delete\s+",

        r"^remove\s+",

        r"^task\s+"
    ]

    for prefix in prefixes:

        text = re.sub(
            prefix,
            "",
            text,
            flags=re.IGNORECASE
        )

    text = re.sub(
        r"\s+as\s+(completed|complete|done)\s*$",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"[^\w\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    words = text.split()

    cleaned_words = []

    for word in words:

        if (
            not cleaned_words
            or cleaned_words[-1] != word
        ):

            cleaned_words.append(word)

    return " ".join(cleaned_words)


# =========================================================
# SMART TASK MATCHING
# =========================================================

def find_task_by_title(
    db,
    title,
    prefer_pending=True
):

    search = normalize_task_text(title)

    if not search:
        return None

    tasks = get_all_tasks(db)

    if not tasks:
        return None

    # -----------------------------------------------------
    # EXACT MATCH
    # -----------------------------------------------------

    exact_matches = []

    for task in tasks:

        task_title = normalize_task_text(
            task.title
        )

        if task_title == search:

            exact_matches.append(task)

    if exact_matches:

        if prefer_pending:

            pending = [
                task
                for task in exact_matches
                if not task.completed
            ]

            if pending:
                return pending[0]

        return exact_matches[0]

    # -----------------------------------------------------
    # CONTAINS MATCH
    # -----------------------------------------------------

    contains_matches = []

    for task in tasks:

        task_title = normalize_task_text(
            task.title
        )

        if (
            search in task_title
            or task_title in search
        ):

            contains_matches.append(task)

    if contains_matches:

        if prefer_pending:

            pending = [
                task
                for task in contains_matches
                if not task.completed
            ]

            if pending:
                return pending[0]

        return contains_matches[0]

    # -----------------------------------------------------
    # TOKEN MATCH
    # -----------------------------------------------------

    search_words = set(
        search.split()
    )

    best_task = None

    best_score = 0

    for task in tasks:

        task_title = normalize_task_text(
            task.title
        )

        task_words = set(
            task_title.split()
        )

        if not task_words:
            continue

        common_words = (
            search_words & task_words
        )

        score = len(common_words) / max(
            len(search_words),
            len(task_words)
        )

        if score > best_score:

            best_score = score

            best_task = task

    if best_task and best_score >= 0.5:

        if prefer_pending and best_task.completed:

            pending_tasks = [

                task
                for task in tasks

                if not task.completed
                and task.id == best_task.id
            ]

            if pending_tasks:
                return pending_tasks[0]

        return best_task

    # -----------------------------------------------------
    # FUZZY MATCH
    # -----------------------------------------------------

    best_task = None

    best_ratio = 0

    for task in tasks:

        task_title = normalize_task_text(
            task.title
        )

        ratio = SequenceMatcher(
            None,
            search,
            task_title
        ).ratio()

        if ratio > best_ratio:

            best_ratio = ratio

            best_task = task

    if best_task and best_ratio >= 0.65:

        if prefer_pending and best_task.completed:

            pending_candidates = [

                task
                for task in tasks
                if not task.completed
            ]

            if pending_candidates:

                pending_candidates.sort(

                    key=lambda task:
                    SequenceMatcher(
                        None,
                        search,
                        normalize_task_text(
                            task.title
                        )
                    ).ratio(),

                    reverse=True
                )

                ratio = SequenceMatcher(

                    None,
                    search,
                    normalize_task_text(
                        pending_candidates[0].title
                    )
                ).ratio()

                if ratio >= 0.65:

                    return pending_candidates[0]

        return best_task

    return None


# =========================================================
# TASKS - GET
# =========================================================

@app.get("/tasks")
def get_tasks(
    db: Session = Depends(get_db)
):

    tasks = get_all_tasks(db)

    return [
        task_to_dict(task)
        for task in tasks
    ]


# =========================================================
# TASKS - CREATE
# =========================================================

@app.post("/tasks")
def create_task(
    request: TaskRequest,
    db: Session = Depends(get_db)
):

    title = request.title.strip()

    if not title:

        return {
            "success": False,
            "message": "Task title cannot be empty"
        }

    task = models.Task(
        title=title,
        completed=1 if request.completed else 0
    )

    db.add(task)

    db.commit()

    db.refresh(task)

    return task_to_dict(task)


# =========================================================
# TASKS - UPDATE
# =========================================================

@app.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    request: TaskRequest,
    db: Session = Depends(get_db)
):

    task = (
        db.query(models.Task)
        .filter(
            models.Task.id == task_id
        )
        .first()
    )

    if not task:

        return {
            "success": False,
            "message": "Task not found"
        }

    task.title = request.title.strip()

    task.completed = (
        1
        if request.completed
        else 0
    )

    project = None

    if getattr(task, "project_id", None):
        project = update_project_progress_from_tasks(
            db,
            task.project_id
        )

    db.commit()

    db.refresh(task)

    if project:
        db.refresh(project)

    return task_to_dict(task)


# =========================================================
# TASKS - DELETE
# =========================================================

@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):

    task = (
        db.query(models.Task)
        .filter(
            models.Task.id == task_id
        )
        .first()
    )

    if not task:

        return {
            "success": False,
            "message": "Task not found"
        }

    project_id = getattr(task, "project_id", None)

    db.delete(task)
    db.flush()

    project = None

    if project_id:
        project = update_project_progress_from_tasks(
            db,
            project_id
        )

    db.commit()

    if project:
        db.refresh(project)

    return {
        "success": True,
        "message": "Task deleted successfully",
        "project": project_to_dict(project) if project else None
    }


# =========================================================
# TASKS - ACTION
# =========================================================

@app.post("/tasks/{task_id}/action")
def task_action(
    task_id: int,
    request: TaskActionRequest,
    db: Session = Depends(get_db)
):

    task = (
        db.query(models.Task)
        .filter(
            models.Task.id == task_id
        )
        .first()
    )

    if not task:

        return {
            "success": False,
            "message": "Task not found"
        }

    task.completed = (
        1
        if request.completed
        else 0
    )

    project = None

    if getattr(task, "project_id", None):
        project = update_project_progress_from_tasks(
            db,
            task.project_id
        )

    db.commit()

    db.refresh(task)

    if project:
        db.refresh(project)

    message = (
        "Task marked as completed"
        if request.completed
        else "Task marked as pending"
    )

    return {
        "success": True,
        "message": message,
        "task": task_to_dict(task),
        "project": project_to_dict(project) if project else None
    }


# =========================================================
# KNOWLEDGE - CREATE
# =========================================================

@app.post("/knowledge")
def create_knowledge(
    request: KnowledgeRequest,
    db: Session = Depends(get_db)
):

    title = request.title.strip()

    content = request.content.strip()

    if not title or not content:

        return {
            "success": False,
            "message": "Title and content are required"
        }

    item = models.KnowledgeItem(

        title=title,

        content=content,

        category=request.category,

        source=request.source
    )

    db.add(item)

    db.commit()

    db.refresh(item)

    # -----------------------------------------------------
    # CREATE SEMANTIC EMBEDDING
    # -----------------------------------------------------

    try:

        embedding_text = f"""
Title: {item.title}

Category: {item.category}

Source: {item.source or ""}

Content:
{item.content}
""".strip()

        item.embedding = create_embedding(
            embedding_text
        )

        db.commit()

    except Exception as error:

        print(
            "Embedding creation failed:",
            error
        )

        item.embedding = None

        db.commit()

    return {

        "message":
        "Knowledge saved successfully",

        "id":
        item.id,

        "title":
        item.title
    }


# =========================================================
# KNOWLEDGE - GET
# =========================================================

@app.get("/knowledge")
def get_knowledge(
    db: Session = Depends(get_db)
):

    items = (

        db.query(
            models.KnowledgeItem
        )

        .order_by(
            models.KnowledgeItem.created_at.desc()
        )

        .all()
    )

    return items


# =========================================================
# KNOWLEDGE - SEMANTIC SEARCH
# =========================================================

@app.get("/knowledge/search")
def search_knowledge(
    q: str,
    db: Session = Depends(get_db)
):
    query = q.strip()

    if not query:
        return []

    knowledge_items = (
        db.query(
            models.KnowledgeItem
        )
        .order_by(
            models.KnowledgeItem.created_at.desc()
        )
        .all()
    )

    knowledge_documents = [
        {
            "id": item.id,
            "title": item.title,
            "content": item.content,
            "category": item.category or "general",
            "source": item.source or "",
            "embedding": item.embedding or [],
        }
        for item in knowledge_items
    ]

    try:
        results = search_knowledge_semantically(
            query=query,
            documents=knowledge_documents,
            top_k=5,
            minimum_score=0.65,
        )

    except Exception as error:
        print("Semantic search error:", error)
        return []

    return [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "content": item.get("content", ""),
            "category": item.get(
                "category",
                "general"
            ),
            "source": item.get(
                "source",
                ""
            ),
            "similarity": item.get(
                "similarity",
                0
            ),
        }
        for item in results
    ]

# =========================================================
# KNOWLEDGE - DELETE
# =========================================================

@app.delete("/knowledge/{item_id}")
def delete_knowledge(
    item_id: int,
    db: Session = Depends(get_db)
):

    item = (

        db.query(
            models.KnowledgeItem
        )

        .filter(
            models.KnowledgeItem.id == item_id
        )

        .first()
    )

    if not item:

        return {
            "message":
            "Knowledge item not found"
        }

    db.delete(item)

    db.commit()

    return {
        "message":
        "Knowledge deleted successfully"
    }


# =========================================================
# PROJECTS - CREATE
# =========================================================

@app.post("/projects")
def create_project(
    request: ProjectRequest,
    db: Session = Depends(get_db)
):

    project = models.Project(

        name=request.name,

        description=request.description,

        technology=request.technology,

        status=request.status,

        progress=request.progress
    )

    db.add(project)

    db.commit()

    db.refresh(project)

    return project


# =========================================================
# PROJECTS - GET ALL
# =========================================================

@app.get("/projects")
def get_projects(
    db: Session = Depends(get_db)
):

    projects = (

        db.query(models.Project)

        .order_by(
            models.Project.created_at.desc()
        )

        .all()
    )

    changed = False

    for project in projects:
        previous_progress = project.progress
        update_project_progress_from_tasks(
            db,
            project.id
        )
        if project.progress != previous_progress:
            changed = True

    if changed:
        db.commit()
        for project in projects:
            db.refresh(project)

    return projects


# =========================================================
# PROJECTS - GET SINGLE
# =========================================================

@app.get("/projects/{project_id}")
def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = (

        db.query(models.Project)

        .filter(
            models.Project.id == project_id
        )

        .first()
    )

    if not project:

        return {
            "message": "Project not found"
        }

    return project


# =========================================================
# PROJECTS - UPDATE
# =========================================================

@app.put("/projects/{project_id}")
def update_project(
    project_id: int,
    request: ProjectRequest,
    db: Session = Depends(get_db)
):

    project = (

        db.query(models.Project)

        .filter(
            models.Project.id == project_id
        )

        .first()
    )

    if not project:

        return {
            "message": "Project not found"
        }

    project.name = request.name

    project.description = request.description

    project.technology = request.technology

    project.status = request.status

    project.progress = request.progress

    db.commit()

    db.refresh(project)

    return project


# =========================================================
# PROJECTS - DELETE
# =========================================================

@app.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = (

        db.query(models.Project)

        .filter(
            models.Project.id == project_id
        )

        .first()
    )

    if not project:

        return {
            "message": "Project not found"
        }

    db.delete(project)

    db.commit()

    return {
        "message":
        "Project deleted successfully"
    }


# =========================================================
# NOTES HELPERS
# =========================================================

def note_to_dict(note):

    project_name = None

    try:
        if getattr(note, "project", None):
            project_name = note.project.name
    except Exception:
        project_name = None

    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "category": note.category or "General",
        "tags": note.tags or "",
        "pinned": bool(note.pinned),
        "project_id": getattr(note, "project_id", None),
        "project_name": project_name,
        "created_at": (
            note.created_at.isoformat()
            if note.created_at
            else None
        ),
        "updated_at": (
            note.updated_at.isoformat()
            if note.updated_at
            else None
        ),
    }


# =========================================================
# NOTES - GET ALL
# =========================================================

@app.get("/notes")
def get_notes(
    db: Session = Depends(get_db)
):

    notes = (
        db.query(models.Note)
        .order_by(
            models.Note.pinned.desc(),
            models.Note.updated_at.desc()
        )
        .all()
    )

    return [
        note_to_dict(note)
        for note in notes
    ]


# =========================================================
# NOTES - CREATE
# =========================================================

@app.post("/notes")
def create_note(
    request: NoteRequest,
    db: Session = Depends(get_db)
):

    title = request.title.strip()
    content = request.content.strip()

    if not title or not content:
        return {
            "success": False,
            "message": "Title and content are required"
        }

    project = None

    if request.project_id is not None:
        project = (
            db.query(models.Project)
            .filter(models.Project.id == request.project_id)
            .first()
        )

        if not project:
            return {
                "success": False,
                "message": "Project not found"
            }

    note = models.Note(
        title=title,
        content=content,
        category=request.category.strip() or "General",
        tags=request.tags.strip(),
        pinned=1 if request.pinned else 0,
        project_id=project.id if project else None
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return note_to_dict(note)


# =========================================================
# NOTES - UPDATE
# =========================================================

@app.put("/notes/{note_id}")
def update_note(
    note_id: int,
    request: NoteRequest,
    db: Session = Depends(get_db)
):

    note = (
        db.query(models.Note)
        .filter(models.Note.id == note_id)
        .first()
    )

    if not note:
        return {
            "success": False,
            "message": "Note not found"
        }

    title = request.title.strip()
    content = request.content.strip()

    if not title or not content:
        return {
            "success": False,
            "message": "Title and content are required"
        }

    project = None

    if request.project_id is not None:
        project = (
            db.query(models.Project)
            .filter(models.Project.id == request.project_id)
            .first()
        )

        if not project:
            return {
                "success": False,
                "message": "Project not found"
            }

    note.title = title
    note.content = content
    note.category = request.category.strip() or "General"
    note.tags = request.tags.strip()
    note.pinned = 1 if request.pinned else 0
    note.project_id = project.id if project else None

    db.commit()
    db.refresh(note)

    return note_to_dict(note)


# =========================================================
# NOTES - DELETE
# =========================================================

@app.delete("/notes/{note_id}")
def delete_note(
    note_id: int,
    db: Session = Depends(get_db)
):

    note = (
        db.query(models.Note)
        .filter(models.Note.id == note_id)
        .first()
    )

    if not note:
        return {
            "success": False,
            "message": "Note not found"
        }

    db.delete(note)
    db.commit()

    return {
        "success": True,
        "message": "Note deleted successfully"
    }


# =========================================================
# NOTES - PIN / UNPIN
# =========================================================

@app.patch("/notes/{note_id}/pin")
def toggle_note_pin(
    note_id: int,
    db: Session = Depends(get_db)
):

    note = (
        db.query(models.Note)
        .filter(models.Note.id == note_id)
        .first()
    )

    if not note:
        return {
            "success": False,
            "message": "Note not found"
        }

    note.pinned = 0 if note.pinned else 1

    db.commit()
    db.refresh(note)

    return {
        "success": True,
        "pinned": bool(note.pinned),
        "note": note_to_dict(note)
    }


# =========================================================
# NOTES - AI SUMMARY
# =========================================================

@app.post("/notes/ai/summarize")
def summarize_note(
    request: NoteAIRequest
):

    title = request.title.strip()
    content = request.content.strip()

    if not content:
        return {
            "success": False,
            "message": "Note content is required"
        }

    prompt = f"""
You are NEXUS AI OS.

Summarize the following personal note.

Rules:
- Keep the important information.
- Make it concise and useful.
- Use clear bullet points when appropriate.
- Do not invent information.
- Return only the summary.

Title:
{title or "Untitled"}

Note:
{content}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        return {
            "success": True,
            "summary": (
                getattr(response, "text", "") or ""
            ).strip()
        }

    except Exception as error:
        print("Note summary error:", error)

        return {
            "success": False,
            "message": "AI summary failed"
        }


# =========================================================
# NOTES - AI IMPROVE
# =========================================================

@app.post("/notes/ai/improve")
def improve_note(
    request: NoteAIRequest
):

    title = request.title.strip()
    content = request.content.strip()

    if not content:
        return {
            "success": False,
            "message": "Note content is required"
        }

    prompt = f"""
You are NEXUS AI OS.

Improve the writing of the following personal note.

Rules:
- Preserve the original meaning.
- Improve clarity, structure and readability.
- Fix grammar where needed.
- Do not add facts that were not present.
- Keep it natural and practical.
- Return only the improved note content.

Title:
{title or "Untitled"}

Original note:
{content}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        return {
            "success": True,
            "content": (
                getattr(response, "text", "") or ""
            ).strip()
        }

    except Exception as error:
        print("Note improve error:", error)

        return {
            "success": False,
            "message": "AI improvement failed"
        }




# =========================================================
# AI PROJECT INSIGHTS
# =========================================================

@app.get("/projects/{project_id}/insights")
def get_project_insights(
    project_id: int,
    db: Session = Depends(get_db)
):
    project = (
        db.query(models.Project)
        .filter(models.Project.id == project_id)
        .first()
    )

    if not project:
        return {
            "success": False,
            "message": "Project not found"
        }

    tasks = (
        db.query(models.Task)
        .filter(models.Task.project_id == project_id)
        .order_by(models.Task.created_at.desc())
        .all()
    )

    notes = (
        db.query(models.Note)
        .filter(models.Note.project_id == project_id)
        .order_by(models.Note.updated_at.desc())
        .all()
    )

    completed_tasks = [
        task.title for task in tasks if task.completed
    ]

    pending_tasks = [
        task.title for task in tasks if not task.completed
    ]

    knowledge_items = (
        db.query(models.KnowledgeItem)
        .order_by(models.KnowledgeItem.created_at.desc())
        .all()
    )

    # Find knowledge related to the project using the project name
    # and important project keywords. This keeps the feature useful
    # even when knowledge items are not explicitly linked to a project.
    project_terms = {
        word.lower()
        for word in re.findall(r"[A-Za-z0-9]+", project.name)
        if len(word) >= 3
    }

    relevant_knowledge = []

    for item in knowledge_items:
        searchable = (
            f"{item.title} {item.content} {item.category or ''}"
        ).lower()

        if any(term in searchable for term in project_terms):
            relevant_knowledge.append(item)

    knowledge_preview = [
        {
            "title": item.title,
            "category": item.category or "general",
            "content": item.content[:1000]
        }
        for item in relevant_knowledge[:8]
    ]

    notes_preview = [
        {
            "title": note.title,
            "category": note.category or "General",
            "tags": note.tags or "",
            "content": note.content[:1000]
        }
        for note in notes[:8]
    ]

    task_summary = (
        f"Total tasks: {len(tasks)}\n"
        f"Completed tasks: {len(completed_tasks)}\n"
        f"Pending tasks: {len(pending_tasks)}"
    )

    prompt = f"""
You are NEXUS AI OS, a personal AI project intelligence assistant.

Analyze the following project data and generate a useful project intelligence
report.

PROJECT
Name: {project.name}
Description: {project.description or "Not provided"}
Technology: {project.technology or "Not provided"}
Status: {project.status or "active"}
Progress: {project.progress or 0}%

TASK SUMMARY
{task_summary}

COMPLETED TASKS
{chr(10).join("- " + item for item in completed_tasks) if completed_tasks else "None"}

PENDING TASKS
{chr(10).join("- " + item for item in pending_tasks) if pending_tasks else "None"}

PROJECT NOTES
{json.dumps(notes_preview, ensure_ascii=False)}

RELEVANT KNOWLEDGE VAULT ITEMS
{json.dumps(knowledge_preview, ensure_ascii=False)}

Rules:
- Use only the information provided above.
- Do not invent completed work, tasks, technologies, or project facts.
- Clearly distinguish current facts from suggested next actions.
- Keep the report concise but useful.
- Return valid JSON only.
- JSON keys must be exactly:
  summary, current_state, completed_work, pending_work,
  important_knowledge, next_actions
- summary must be a short paragraph.
- current_state must be an object containing progress, status, total_tasks,
  completed_tasks, pending_tasks.
- completed_work must be an array of strings.
- pending_work must be an array of strings.
- important_knowledge must be an array of strings.
- next_actions must be an array of strings.
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        raw_text = (
            getattr(response, "text", "") or ""
        ).strip()

        cleaned = raw_text

        if cleaned.startswith("```"):
            cleaned = re.sub(
                r"^```(?:json)?\s*",
                "",
                cleaned,
                flags=re.IGNORECASE
            )
            cleaned = re.sub(
                r"\s*```$",
                "",
                cleaned
            ).strip()

        try:
            insights = json.loads(cleaned)
        except json.JSONDecodeError:
            insights = {
                "summary": raw_text,
                "current_state": {
                    "progress": project.progress or 0,
                    "status": project.status or "active",
                    "total_tasks": len(tasks),
                    "completed_tasks": len(completed_tasks),
                    "pending_tasks": len(pending_tasks)
                },
                "completed_work": completed_tasks,
                "pending_work": pending_tasks,
                "important_knowledge": [
                    item["title"] for item in knowledge_preview
                ],
                "next_actions": pending_tasks[:5]
            }

        return {
            "success": True,
            "project": project_to_dict(project),
            "insights": insights,
            "tasks": {
                "total": len(tasks),
                "completed": completed_tasks,
                "pending": pending_tasks
            },
            "notes_count": len(notes),
            "knowledge_count": len(relevant_knowledge)
        }

    except Exception as error:
        print("Project insights error:", error)

        return {
            "success": False,
            "message": "AI project insights generation failed",
            "project": project_to_dict(project),
            "tasks": {
                "total": len(tasks),
                "completed": completed_tasks,
                "pending": pending_tasks
            }
        }

# =========================================================
# PROJECT HELPERS
# =========================================================

def normalize_project_text(text):
    if not text:
        return ""

    text = str(text).strip().lower()

    prefixes = [
        r"^project\s+",
        r"^the\s+project\s+",
        r"^delete\s+project\s+",
        r"^remove\s+project\s+",
        r"^complete\s+project\s+",
        r"^finish\s+project\s+",
        r"^mark\s+project\s+",
        r"^update\s+project\s+",
        r"^set\s+project\s+",
    ]

    for prefix in prefixes:
        text = re.sub(prefix, "", text, flags=re.IGNORECASE)

    text = re.sub(
        r"\s+(as\s+)?(completed|complete|done)$",
        "",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"\s+(status|progress)\s+(to|at)\s+.+$",
        "",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(r"[^\w\s\-\.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def find_project_by_name(db, name):
    search = normalize_project_text(name)
    if not search:
        return None

    projects = (
        db.query(models.Project)
        .order_by(models.Project.created_at.desc())
        .all()
    )
    if not projects:
        return None

    for project in projects:
        if normalize_project_text(project.name) == search:
            return project

    contains_matches = []
    for project in projects:
        project_name = normalize_project_text(project.name)
        if search in project_name or project_name in search:
            contains_matches.append(project)

    if contains_matches:
        return contains_matches[0]

    search_words = set(search.split())
    best_project = None
    best_score = 0

    for project in projects:
        project_name = normalize_project_text(project.name)
        project_words = set(project_name.split())
        if not project_words:
            continue

        common_words = search_words & project_words
        score = len(common_words) / max(
            len(search_words),
            len(project_words)
        )

        if score > best_score:
            best_score = score
            best_project = project

    if best_project and best_score >= 0.5:
        return best_project

    best_project = None
    best_ratio = 0

    for project in projects:
        project_name = normalize_project_text(project.name)
        ratio = SequenceMatcher(
            None,
            search,
            project_name
        ).ratio()

        if ratio > best_ratio:
            best_ratio = ratio
            best_project = project

    if best_project and best_ratio >= 0.65:
        return best_project

    return None


def project_to_dict(project):
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description or "",
        "technology": project.technology or "",
        "status": project.status or "active",
        "progress": project.progress or 0
    }


# =========================================================
# AI PROJECT COMMAND DETECTION
# =========================================================

def detect_project_action(message):
    text = message.strip()

    create_patterns = [
        r"(?:create|add|make|new)\s+(?:a\s+)?project[: ]+(.+)",
        r"start\s+(?:a\s+)?project[: ]+(.+)"
    ]

    for pattern in create_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {
                "action": "create",
                "name": match.group(1).strip()
            }

    delete_patterns = [
        r"delete\s+(?:the\s+)?project[: ]+(.+)",
        r"remove\s+(?:the\s+)?project[: ]+(.+)"
    ]

    for pattern in delete_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {
                "action": "delete",
                "name": match.group(1).strip()
            }

    complete_patterns = [
        r"complete\s+(?:the\s+)?project[: ]+(.+)",
        r"finish\s+(?:the\s+)?project[: ]+(.+)",
        r"mark\s+(?:the\s+)?project[: ]+(.+?)\s+as\s+(?:completed|complete|done)"
    ]

    for pattern in complete_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return {
                "action": "complete",
                "name": match.group(1).strip()
            }

    progress_patterns = [
        r"(?:set|update|change)\s+(?:project\s+)?(.+?)\s+progress\s+(?:to|at)\s+(\d{1,3})\s*%?",
        r"(?:set|update|change)\s+project[: ]+(.+?)\s+to\s+(\d{1,3})\s*%?\s+progress"
    ]

    for pattern in progress_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            progress = int(match.group(2))
            return {
                "action": "progress",
                "name": match.group(1).strip(),
                "progress": max(0, min(progress, 100))
            }

    status_patterns = [
        r"(?:set|update|change)\s+(?:project\s+)?(.+?)\s+status\s+(?:to|as)\s+(.+)",
        r"(?:set|update|change)\s+status\s+of\s+project[: ]+(.+?)\s+to\s+(.+)"
    ]

    for pattern in status_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            status = match.group(2).strip().lower()
            allowed_statuses = {
                "active",
                "completed",
                "complete",
                "done",
                "paused",
                "on hold",
                "planning",
                "archived"
            }

            if status not in allowed_statuses:
                return {"action": "chat"}

            if status in {"complete", "done"}:
                status = "completed"

            return {
                "action": "status",
                "name": match.group(1).strip(),
                "status": status
            }

    return {"action": "chat"}



# =========================================================
# AI MULTI-TASK COMMAND DETECTION
# =========================================================

def extract_tasks_from_project_plan(history):
    """Extract actionable tasks from the latest NEXUS project plan."""
    if not history:
        return []

    assistant_text = ""
    for item in reversed(history):
        role = getattr(item, "role", "")
        text = getattr(item, "text", "") or ""
        if role != "user" and text.strip():
            assistant_text = text.strip()
            break

    if not assistant_text:
        return []

    lines = assistant_text.splitlines()
    tasks = []
    in_execution_plan = False
    waiting_for_task = False

    ignored_headings = {
        "current status",
        "execution plan",
        "tech stack",
        "progress",
        "status",
        "description",
        "project plan",
        "next steps",
        "summary",
    }

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        clean = re.sub(r"^#+\s*", "", line)
        clean = clean.replace("**", "").replace("__", "").strip()

        if re.search(r"execution plan", clean, re.IGNORECASE):
            in_execution_plan = True
            continue

        if re.match(r"^(current status|tech stack|summary|next steps)\s*:?$", clean, re.IGNORECASE):
            continue

        if re.search(r"\btask\s*:", clean, re.IGNORECASE):
            after = re.split(r"\btask\s*:\s*", clean, maxsplit=1, flags=re.IGNORECASE)[-1].strip()
            if after and len(after) >= 4:
                tasks.append(after)
            else:
                waiting_for_task = True
            continue

        if waiting_for_task:
            candidate = re.sub(r"^[-*•◦]+\s*", "", clean)
            candidate = re.sub(r"^\d+[.)]\s*", "", candidate).strip()
            if candidate and candidate.lower() not in ignored_headings:
                tasks.append(candidate)
                waiting_for_task = False
                continue

        if in_execution_plan:
            # Prefer nested bullet tasks when the plan uses numbered phases.
            if re.match(r"^[-*•◦]\s+", clean):
                candidate = re.sub(r"^[-*•◦]\s+", "", clean).strip()
                if candidate and candidate.lower().rstrip(":") not in ignored_headings:
                    tasks.append(candidate)
                    continue

            # If the plan has numbered task/phase lines, capture them.
            numbered_match = re.match(r"^\d+[.)]\s+(.+)$", clean)
            if numbered_match:
                candidate = numbered_match.group(1).strip()
                candidate_lower = candidate.lower().rstrip(":")
                if candidate_lower not in ignored_headings:
                    # Skip obvious phase headings when a nested Task: will follow.
                    if not re.search(r"(?:development|phase|overview|status)$", candidate, re.IGNORECASE):
                        tasks.append(candidate)
                    else:
                        waiting_for_task = True

    # Fallback: if no execution-plan marker was found, collect meaningful
    # bullet/numbered lines from the latest assistant response.
    if not tasks:
        for raw_line in lines:
            clean = raw_line.strip().replace("**", "").strip()
            candidate = re.sub(r"^(?:[-*•◦]|\d+[.)])\s*", "", clean).strip()
            if len(candidate) < 5:
                continue
            if candidate.lower().rstrip(":") in ignored_headings:
                continue
            if re.match(r"^(here is|based on|current|progress|tech stack|status)", candidate, re.IGNORECASE):
                continue
            tasks.append(candidate)

    unique_tasks = []
    seen = set()
    for task in tasks:
        task = re.sub(r"\s+", " ", task).strip(" -:;")
        key = normalize_task_text(task)
        if key and key not in seen and len(task) >= 4:
            seen.add(key)
            unique_tasks.append(task)

    return unique_tasks[:10]


def detect_plan_task_creation(message):
    text = message.strip()
    patterns = [
        r"create\s+(?:the\s+)?tasks?\s+from\s+(?:this|the)\s+project\s+plan",
        r"add\s+(?:the\s+)?tasks?\s+from\s+(?:this|the)\s+project\s+plan",
        r"turn\s+(?:this|the)\s+project\s+plan\s+into\s+tasks?",
        r"create\s+tasks?\s+from\s+(?:this|the)\s+plan",
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return {"action": "create_from_plan"}
    return {"action": "chat"}


def detect_multiple_task_action(message):
    text = message.strip()

    # Supports commands such as:
    # create 3 tasks for NEXUS AI OS:
    # 1. Build project dashboard
    # 2. Add project analytics
    # 3. Add AI project insights
    numbered = re.findall(
        r"(?:^|\s)(?:\d+)[.)]\s*(.+?)(?=(?:\s+\d+[.)]\s*)|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    if numbered and re.search(
        r"\bcreate\s+\d+\s+tasks?\b|\badd\s+\d+\s+tasks?\b|\bmake\s+\d+\s+tasks?\b",
        text,
        re.IGNORECASE
    ):
        tasks = []
        for title in numbered:
            clean_title = re.sub(r"\s+", " ", title).strip()
            if clean_title:
                tasks.append(clean_title)

        if tasks:
            return {
                "action": "create_multiple",
                "titles": tasks
            }

    return {
        "action": "chat"
    }


# =========================================================
# AI TASK COMMAND DETECTION
# =========================================================

def detect_task_action(message):

    text = message.strip()

    # -----------------------------------------------------
    # CREATE
    # -----------------------------------------------------

    create_patterns = [

        r"add (?:a )?task[: ]+(.+)",

        r"create (?:a )?task[: ]+(.+)",

        r"make (?:a )?task[: ]+(.+)",

        r"new task[: ]+(.+)",

        r"remind me to (.+)"
    ]

    for pattern in create_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            title = match.group(1).strip()
            project_name = None

            # Supports: create task for NEXUS AI OS: build dashboard
            project_match = re.match(
                r"for\s+(.+?)\s*:\s*(.+)$",
                title,
                re.IGNORECASE
            )

            if project_match:
                project_name = project_match.group(1).strip()
                title = project_match.group(2).strip()

            return {
                "action": "create",
                "title": title,
                "project_name": project_name
            }

    # -----------------------------------------------------
    # COMPLETE
    # -----------------------------------------------------

    complete_patterns = [

        r"mark (.+) as completed",

        r"mark (.+) as complete",

        r"complete (.+)",

        r"finish (.+)",

        r"mark (.+) as done",

        r"done with (.+)"
    ]

    for pattern in complete_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            title = match.group(1).strip()

            return {
                "action": "complete",
                "title": title
            }

    # -----------------------------------------------------
    # DELETE
    # -----------------------------------------------------

    delete_patterns = [

        r"delete task (.+)",

        r"delete (.+)",

        r"remove task (.+)",

        r"remove (.+)"
    ]

    for pattern in delete_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            title = match.group(1).strip()

            return {
                "action": "delete",
                "title": title
            }

    return {
        "action": "chat"
    }


# =========================================================
# AI CHAT
# =========================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):

    user_message = request.message.strip()

    if not user_message:

        return {
            "response":
            "Please enter a message."
        }

    # =====================================================
    # CHECK MULTI-TASK COMMAND
    # =====================================================

    multiple_task_action = detect_multiple_task_action(
        user_message
    )

    if multiple_task_action["action"] == "create_multiple":
        created_tasks = []

        for title in multiple_task_action["titles"]:
            task = models.Task(
                title=title,
                completed=0
            )
            db.add(task)
            db.flush()
            created_tasks.append(task)

        db.commit()

        for task in created_tasks:
            db.refresh(task)

        task_lines = "\n".join(
            f"- **{task.title}**"
            for task in created_tasks
        )

        return {
            "response": (
                "✅ Tasks created successfully:\n\n"
                + task_lines
            ),
            "action": "tasks_created",
            "tasks": [
                task_to_dict(task)
                for task in created_tasks
            ]
        }

    # =====================================================
    # CREATE TASKS FROM THE LATEST PROJECT PLAN
    # =====================================================

    plan_action = detect_plan_task_creation(user_message)

    if plan_action["action"] == "create_from_plan":
        planned_tasks = extract_tasks_from_project_plan(request.history)

        # Some frontend chat states may send only the latest user messages in
        # history. In that case, the previous planner response is not
        # available to the backend. Recover gracefully by rebuilding the
        # latest project plan from the live project database and asking
        # Gemini for a small structured list of actionable tasks.
        if not planned_tasks:
            project_name = None
            history_items = request.history or []

            for item in reversed(history_items):
                role = getattr(item, "role", "")
                text = getattr(item, "text", "") or ""
                if role != "user":
                    continue
                match = re.search(
                    r"(?:plan|planning)\s+(.+?)\s+project$",
                    text.strip(),
                    re.IGNORECASE
                )
                if match:
                    project_name = match.group(1).strip()
                    break

            if not project_name:
                match = re.search(
                    r"(?:for|of)\s+(.+?)\s+project",
                    user_message,
                    re.IGNORECASE
                )
                if match:
                    project_name = match.group(1).strip()

            # If the user says "this project plan" without naming the
            # project, use the most recently created project. This matches
            # the natural follow-up flow: plan a project -> create tasks
            # from this project plan.
            if project_name:
                project = (
                    db.query(models.Project)
                    .filter(models.Project.name.ilike(project_name))
                    .first()
                )
            else:
                project = (
                    db.query(models.Project)
                    .order_by(models.Project.created_at.desc())
                    .first()
                )

                if project:
                    current_tasks = get_all_tasks(db)
                    pending_tasks = [
                        task.title
                        for task in current_tasks
                        if not task.completed
                    ]

                    planner_prompt = f"""
You are NEXUS AI OS project planner.
Create 5 concise, actionable development tasks for this project.
Return ONLY a numbered list, one task per line. Do not add headings,
explanations, progress values, or markdown bullets.

Project: {project.name}
Description: {project.description or 'Not provided'}
Technology: {project.technology or 'Not provided'}
Current progress: {project.progress or 0}%
Current status: {project.status or 'active'}
Existing pending tasks: {', '.join(pending_tasks[:20]) if pending_tasks else 'None'}

Avoid duplicating existing pending tasks.
"""

                    try:
                        planner_response = client.models.generate_content(
                            model="gemini-3.5-flash-lite",
                            contents=planner_prompt
                        )
                        generated_plan = (
                            getattr(planner_response, "text", "") or ""
                        ).strip()
                        planned_tasks = []
                        for raw_line in generated_plan.splitlines():
                            candidate = re.sub(
                                r"^\s*(?:\d+[.)]|[-*•◦])\s*",
                                "",
                                raw_line
                            ).strip()
                            candidate = re.sub(r"\s+", " ", candidate)
                            if len(candidate) >= 4:
                                planned_tasks.append(candidate)
                        planned_tasks = planned_tasks[:10]
                    except Exception as error:
                        print("Project plan recovery error:", error)

        if not planned_tasks:
            return {
                "response": (
                    "❌ I couldn't find actionable tasks in the latest project plan. "
                    "Please ask me to plan the project first, then create the tasks."
                ),
                "action": "plan_tasks_not_found",
            }

        created_tasks = []
        existing_titles = {normalize_task_text(task.title) for task in get_all_tasks(db)}

        for title in planned_tasks:
            normalized = normalize_task_text(title)
            if not normalized or normalized in existing_titles:
                continue
            task = models.Task(title=title.strip(), completed=0)
            db.add(task)
            db.flush()
            created_tasks.append(task)
            existing_titles.add(normalized)

        if created_tasks:
            db.commit()
            for task in created_tasks:
                db.refresh(task)
            task_lines = "\n".join(f"- **{task.title}**" for task in created_tasks)
            return {
                "response": "🧠 Project plan converted into tasks:\n\n" + task_lines,
                "action": "plan_tasks_created",
                "tasks": [task_to_dict(task) for task in created_tasks],
            }

        return {
            "response": "ℹ️ All tasks from the project plan already exist in your task list.",
            "action": "plan_tasks_already_exist",
            "tasks": [],
        }

    # =====================================================
    # CHECK PROJECT COMMAND
    # =====================================================

    project_action = detect_project_action(
        user_message
    )

    # =====================================================
    # CREATE PROJECT THROUGH AI
    # =====================================================

    if project_action["action"] == "create":
        project_name = project_action["name"].strip()

        existing_project = find_project_by_name(
            db,
            project_name
        )

        if existing_project:
            return {
                "response": (
                    "⚠️ A project with this name already exists:\n\n"
                    f"**{existing_project.name}**"
                ),
                "action": "project_exists",
                "project": project_to_dict(existing_project)
            }

        project = models.Project(
            name=project_name,
            description="",
            technology="",
            status="active",
            progress=0
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        return {
            "response": (
                "🚀 Project created successfully:\n\n"
                f"**{project.name}**"
            ),
            "action": "project_created",
            "project": project_to_dict(project)
        }

    # =====================================================
    # DELETE PROJECT THROUGH AI
    # =====================================================

    if project_action["action"] == "delete":
        requested_name = project_action["name"]

        project = find_project_by_name(
            db,
            requested_name
        )

        if not project:
            return {
                "response": (
                    "❌ I couldn't find a project matching "
                    f"**{requested_name}**."
                ),
                "action": "project_not_found"
            }

        deleted_name = project.name
        db.delete(project)
        db.commit()

        return {
            "response": (
                "🗑️ Project deleted:\n\n"
                f"**{deleted_name}**"
            ),
            "action": "project_deleted",
            "project": {"name": deleted_name}
        }

    # =====================================================
    # COMPLETE PROJECT THROUGH AI
    # =====================================================

    if project_action["action"] == "complete":
        requested_name = project_action["name"]

        project = find_project_by_name(
            db,
            requested_name
        )

        if not project:
            return {
                "response": (
                    "❌ I couldn't find a project matching "
                    f"**{requested_name}**."
                ),
                "action": "project_not_found"
            }

        project.progress = 100
        project.status = "completed"

        db.commit()
        db.refresh(project)

        return {
            "response": (
                "✅ Project completed:\n\n"
                f"**{project.name}**\n\n"
                "Progress: **100%**"
            ),
            "action": "project_completed",
            "project": project_to_dict(project)
        }

    # =====================================================
    # UPDATE PROJECT PROGRESS THROUGH AI
    # =====================================================

    if project_action["action"] == "progress":
        requested_name = project_action["name"]
        progress = project_action["progress"]

        project = find_project_by_name(
            db,
            requested_name
        )

        if not project:
            return {
                "response": (
                    "❌ I couldn't find a project matching "
                    f"**{requested_name}**."
                ),
                "action": "project_not_found"
            }

        project.progress = progress

        if progress >= 100:
            project.progress = 100
            project.status = "completed"
        elif project.status == "completed":
            project.status = "active"

        db.commit()
        db.refresh(project)

        return {
            "response": (
                "📊 Project progress updated:\n\n"
                f"**{project.name}**\n\n"
                f"Progress: **{project.progress}%**"
            ),
            "action": "project_progress_updated",
            "project": project_to_dict(project)
        }

    # =====================================================
    # UPDATE PROJECT STATUS THROUGH AI
    # =====================================================

    if project_action["action"] == "status":
        requested_name = project_action["name"]
        status = project_action["status"]

        project = find_project_by_name(
            db,
            requested_name
        )

        if not project:
            return {
                "response": (
                    "❌ I couldn't find a project matching "
                    f"**{requested_name}**."
                ),
                "action": "project_not_found"
            }

        project.status = status

        if status == "completed":
            project.progress = 100

        db.commit()
        db.refresh(project)

        return {
            "response": (
                "🔄 Project status updated:\n\n"
                f"**{project.name}**\n\n"
                f"Status: **{project.status}**"
            ),
            "action": "project_status_updated",
            "project": project_to_dict(project)
        }

    # =====================================================
    # CHECK TASK COMMAND
    # =====================================================

    task_action = detect_task_action(
        user_message
    )

    # =====================================================
    # CREATE TASK THROUGH AI
    # =====================================================

    if task_action["action"] == "create":

        title = task_action["title"].strip()

        title = re.sub(
            r"\s+",
            " ",
            title
        )

        project = None
        project_name = task_action.get("project_name")

        if project_name:
            project = find_project_by_name(
                db,
                project_name
            )

            if not project:
                return {
                    "response": (
                        "❌ I couldn't find a project matching "
                        f"**{project_name}**."
                    ),
                    "action": "project_not_found"
                }

        task = models.Task(
            title=title,
            completed=0,
            project_id=project.id if project else None
        )

        db.add(task)

        db.commit()

        db.refresh(task)

        project_text = (
            f"\n\nProject: **{project.name}**"
            if project
            else ""
        )

        return {
            "response": (
                "✅ Task created successfully:\n\n"
                f"**{task.title}**"
                + project_text
            ),
            "action": "task_created",
            "task": task_to_dict(task)
        }

    # =====================================================
    # COMPLETE TASK THROUGH AI
    # =====================================================

    if task_action["action"] == "complete":

        requested_title = (
            task_action["title"]
        )

        task = find_task_by_title(

            db,

            requested_title,

            prefer_pending=True
        )

        if not task:

            return {

                "response": (
                    "❌ I couldn't find a task matching "
                    f"**{requested_title}**."
                ),

                "action":
                "task_not_found"
            }

        task.completed = 1

        project = None

        if getattr(task, "project_id", None):
            project = update_project_progress_from_tasks(
                db,
                task.project_id
            )

        db.commit()

        db.refresh(task)

        if project:
            db.refresh(project)

        project_text = (
            f"\n\nProject: **{project.name}**"
            f"\nProgress: **{project.progress}%**"
            if project
            else ""
        )

        return {

            "response": (
                "✅ Task completed:\n\n"
                f"**{task.title}**"
                + project_text
            ),

            "action":
            "task_completed",

            "task":
            task_to_dict(task),

            "project":
            project_to_dict(project) if project else None
        }

    # =====================================================
    # DELETE TASK THROUGH AI
    # =====================================================

    if task_action["action"] == "delete":

        requested_title = (
            task_action["title"]
        )

        task = find_task_by_title(

            db,

            requested_title,

            prefer_pending=True
        )

        if not task:

            return {

                "response": (
                    "❌ I couldn't find a task matching "
                    f"**{requested_title}**."
                ),

                "action":
                "task_not_found"
            }

        deleted_title = task.title

        db.delete(task)

        db.commit()

        return {

            "response": (
                "🗑️ Task deleted:\n\n"
                f"**{deleted_title}**"
            ),

            "action":
            "task_deleted"
        }

    # =====================================================
    # LOAD CURRENT TASKS
    # =====================================================

    tasks = get_all_tasks(db)

    pending_tasks = [

        task_to_dict(task)

        for task in tasks

        if not task.completed
    ]

    completed_tasks = [

        task_to_dict(task)

        for task in tasks

        if task.completed
    ]

    # =====================================================
    # LOAD CURRENT PROJECTS
    # =====================================================

    projects = (

        db.query(models.Project)

        .order_by(
            models.Project.created_at.desc()
        )

        .all()
    )

    project_data = [

        {

            "id":
            project.id,

            "name":
            project.name,

            "description":
            project.description or "",

            "technology":
            project.technology or "",

            "status":
            project.status or "active",

            "progress":
            project.progress or 0
        }

        for project in projects
    ]

    # =====================================================
    # LOAD KNOWLEDGE WITH EMBEDDINGS
    # =====================================================

    knowledge_items = (

        db.query(
            models.KnowledgeItem
        )

        .order_by(
            models.KnowledgeItem.created_at.desc()
        )

        .all()
    )

    # =====================================================
    # PREPARE KNOWLEDGE DOCUMENTS FOR RAG
    # =====================================================

    knowledge_documents = [

        {

            "id":
            item.id,

            "title":
            item.title,

            "content":
            item.content,

            "category":
            item.category or "general",

            "source":
            item.source or "",

            "embedding":
            item.embedding or []
        }

        for item in knowledge_items
    ]

    # =====================================================
    # SEMANTIC RAG SEARCH
    # =====================================================

    relevant_knowledge = []

    try:

        relevant_knowledge = (
            search_knowledge_semantically(

                query=user_message,

                documents=knowledge_documents,

                top_k=5,

                minimum_score=0.30
            )
        )

    except Exception as error:

        print(
            "Semantic search error:",
            error
        )

        relevant_knowledge = []

    # =====================================================
    # REMOVE EMBEDDING FROM AI CONTEXT
    # =====================================================

    rag_knowledge_data = []

    for item in relevant_knowledge:

        rag_knowledge_data.append({

            "id":
            item.get("id"),

            "title":
            item.get("title"),

            "category":
            item.get("category", "general"),

            "source":
            item.get("source", ""),

            "content":
            item.get("content", ""),

            "similarity":
            item.get("similarity", 0)
        })

    # =====================================================
    # CONVERSATION HISTORY
    # =====================================================

    conversation = ""

    for item in request.history:

        speaker = (

            "User"

            if item.role == "user"

            else "NEXUS"
        )

        conversation += (

            f"{speaker}: "
            f"{item.text}\n"
        )

    conversation += (

        f"User: {user_message}"
    )

    # =====================================================
    # LIVE TASK CONTEXT
    # =====================================================

    task_context = f"""

CURRENT TASKS:

Pending Tasks:

{json.dumps(
    pending_tasks,
    indent=2
)}

Completed Tasks:

{json.dumps(
    completed_tasks,
    indent=2
)}

"""

    # =====================================================
    # LIVE PROJECT CONTEXT
    # =====================================================

    project_database_context = f"""

CURRENT PROJECTS FROM DATABASE:

{json.dumps(
    project_data,
    indent=2
)}

"""

    # =====================================================
    # RAG KNOWLEDGE CONTEXT
    # =====================================================

    rag_context = f"""

SEMANTICALLY RELEVANT KNOWLEDGE
FROM THE USER'S KNOWLEDGE VAULT:

{json.dumps(
    rag_knowledge_data,
    indent=2
)}

"""

    # =====================================================
    # AI SYSTEM PROMPT
    # =====================================================

    system_prompt = """

You are NEXUS, the user's personal AI operating system.

You help the user manage:

- Projects
- Tasks
- Knowledge
- Learning
- Coding
- Productivity

IMPORTANT RULES:

1. Use live database context when relevant.

2. When the user asks about projects,
   use CURRENT PROJECTS FROM DATABASE.

3. When the user asks about tasks,
   use CURRENT TASKS.

4. When the user asks about personal knowledge,
   memories, stored information, or something
   related to their Knowledge Vault,
   use SEMANTICALLY RELEVANT KNOWLEDGE.

5. The semantic knowledge section contains
   documents retrieved using embedding similarity.

6. Prefer highly relevant semantic knowledge
   over unrelated knowledge documents.

7. Do not claim that a document is stored
   unless it appears in the provided context.

8. Never invent tasks.

9. Never invent projects.

10. Never invent project progress.

11. Never invent project status.

12. Never invent stored knowledge.

13. If the relevant knowledge context does not
    contain the requested information,
    clearly say that the information is not
    currently available in the Knowledge Vault.

14. If the user asks:
    "what are my current tasks",
    list actual tasks from CURRENT TASKS.

15. Clearly separate pending and completed tasks.

16. If there are no tasks, say so.

17. If there are no projects, say so.

18. If a task has already been completed,
    do not describe it as pending.

19. If the user asks to perform a task action,
    the backend action should handle it.
    Do not pretend the action happened.

20. For coding questions,
    give practical and usable guidance.

21. Be friendly and natural.

22. Keep answers concise unless the user asks
    for a detailed explanation.

23. Do not claim access to information
    that is not included in the provided context.

24. When discussing the user's projects,
    combine known project memory with
    live database information.

25. If live database information conflicts
    with older project memory,
    prefer the live database information.

26. Do not use generic motivational responses.

27. Use the user's semantic knowledge only when
    it is relevant to the current question.

28. Do not expose embedding vectors,
    similarity calculations, or internal
    retrieval implementation unless the user
    explicitly asks about the technical system.

KNOWN PROJECT MEMORY:

""" + PROJECT_CONTEXT

    # =====================================================
    # GEMINI RESPONSE
    # =====================================================

    response = client.models.generate_content(

        model="gemini-3.5-flash-lite",

        contents=(

            system_prompt

            + "\n\n"

            + project_database_context

            + "\n\n"

            + task_context

            + "\n\n"

            + rag_context

            + "\n\n"

            + "CONVERSATION HISTORY:\n"

            + conversation
        )
    )

    return {

        "response":
        response.text,

        "rag_used":
        len(rag_knowledge_data) > 0,

        "sources":
        [
            {
                "id":
                item["id"],

                "title":
                item["title"],

                "similarity":
                item["similarity"]
            }

            for item in rag_knowledge_data
        ]
    }