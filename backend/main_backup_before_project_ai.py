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

    return {
        "id": task.id,
        "title": task.title,
        "completed": bool(task.completed)
    }


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

    db.commit()

    db.refresh(task)

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

    db.delete(task)

    db.commit()

    return {
        "success": True,
        "message": "Task deleted successfully"
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

    db.commit()

    db.refresh(task)

    message = (
        "Task marked as completed"
        if request.completed
        else "Task marked as pending"
    )

    return {
        "success": True,
        "message": message,
        "task": task_to_dict(task)
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

            return {
                "action": "create",
                "title": title
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

        task = models.Task(

            title=title,

            completed=0
        )

        db.add(task)

        db.commit()

        db.refresh(task)

        return {

            "response": (
                "✅ Task created successfully:\n\n"
                f"**{task.title}**"
            ),

            "action":
            "task_created",

            "task":
            task_to_dict(task)
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

        db.commit()

        db.refresh(task)

        return {

            "response": (
                "✅ Task completed:\n\n"
                f"**{task.title}**"
            ),

            "action":
            "task_completed",

            "task":
            task_to_dict(task)
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