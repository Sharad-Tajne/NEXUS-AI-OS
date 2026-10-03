import { useEffect, useState } from 'react';

import axios from 'axios';



import AIChat from './components/AIChat';

import KnowledgeVault from './components/KnowledgeVault';

import Tasks from './components/Tasks';

import Projects from './components/Projects';
import Notes from './components/Notes';



const API_URL = 'http://127.0.0.1:8000';



function App() {

  const [activePage, setActivePage] = useState('home');



  const [projects, setProjects] = useState([]);

  const [tasks, setTasks] = useState([]);

  const [knowledge, setKnowledge] = useState([]);



  const [dashboardLoading, setDashboardLoading] = useState(true);



  /* =========================================

     LOAD DASHBOARD DATA

  ========================================= */



  const loadDashboardData = async () => {

    try {

      const [projectsResponse, tasksResponse, knowledgeResponse] =

        await Promise.all([

          axios.get(`${API_URL}/projects`),

          axios.get(`${API_URL}/tasks`),

          axios.get(`${API_URL}/knowledge`),

        ]);



      setProjects(projectsResponse.data);

      setTasks(tasksResponse.data);

      setKnowledge(knowledgeResponse.data);



    } catch (error) {

      console.error(

        'Dashboard data fetch error:',

        error

      );

    } finally {

      setDashboardLoading(false);

    }

  };



  useEffect(() => {

    loadDashboardData();

  }, []);





  /* =========================================

     DASHBOARD COUNTS

  ========================================= */



  const totalProjects = projects.length;



  const totalTasks = tasks.length;



  const completedTasks = tasks.filter(

    (task) => task.completed

  ).length;



  const totalDocuments = knowledge.length;



  const activeProjects = projects.filter(

    (project) => project.status === 'active'

  );





  return (

    <div className="app">



      {/* =====================================

          SIDEBAR

      ===================================== */}



      <aside className="sidebar">



        {/* LOGO */}



        <div className="logo">



          <div className="logo-icon">

            N

          </div>



          <div>

            <h2>NEXUS</h2>

            <span>AI OS</span>

          </div>



        </div>





        {/* NAVIGATION */}



        <nav>



          {/* HOME */}



          <button

            className={`nav-item ${

              activePage === 'home'

                ? 'active'

                : ''

            }`}

            onClick={() => setActivePage('home')}

          >

            ⌂ <span>Home</span>

          </button>





          {/* AI */}



          <button

            className={`nav-item ${

              activePage === 'ai'

                ? 'active'

                : ''

            }`}

            onClick={() => setActivePage('ai')}

          >

            ✦ <span>AI Assistant</span>

          </button>





          {/* KNOWLEDGE */}



          <button

            className={`nav-item ${

              activePage === 'knowledge'

                ? 'active'

                : ''

            }`}

            onClick={() =>

              setActivePage('knowledge')

            }

          >

            ▣ <span>Knowledge Vault</span>

          </button>





          {/* TASKS */}



          <button

            className={`nav-item ${

              activePage === 'tasks'

                ? 'active'

                : ''

            }`}

            onClick={() => setActivePage('tasks')}

          >

            ✓ <span>Tasks</span>

          </button>





          {/* PROJECTS */}



          <button

            className={`nav-item ${

              activePage === 'projects'

                ? 'active'

                : ''

            }`}

            onClick={() =>

              setActivePage('projects')

            }

          >

            ◈ <span>Projects</span>

          </button>





          {/* NOTES */}



          <button

            className={`nav-item ${

              activePage === 'notes'

                ? 'active'

                : ''

            }`}

            onClick={() => setActivePage('notes')}

          >

            ✎ <span>Notes</span>

          </button>



        </nav>





        {/* SIDEBAR BOTTOM */}



        <div className="sidebar-bottom">



          <button

            className={`nav-item ${

              activePage === 'settings'

                ? 'active'

                : ''

            }`}

            onClick={() =>

              setActivePage('settings')

            }

          >

            ⚙ <span>Settings</span>

          </button>



        </div>



      </aside>





      {/* =====================================

          MAIN CONTENT

      ===================================== */}



      <main className="main-content">





        {/* =====================================

            AI

        ===================================== */}



        {activePage === 'ai' ? (



          <AIChat />





        ) : activePage === 'knowledge' ? (



          <KnowledgeVault />





        ) : activePage === 'tasks' ? (



          <Tasks />





        ) : activePage === 'projects' ? (



          <Projects />





        ) : activePage === 'notes' ? (



          <Notes />





        ) : (



          /* ===================================

             HOME

          =================================== */



          <>



            {/* TOPBAR */}



            <header className="topbar">



              <div>



                <p className="eyebrow">

                  PERSONAL AI WORKSPACE

                </p>



                <h1>

                  Good afternoon 👋

                </h1>



              </div>





              <div className="profile">



                <div className="avatar">

                  S

                </div>



                <div>



                  <strong>

                    Sharad

                  </strong>



                  <small>

                    Personal Workspace

                  </small>



                </div>



              </div>



            </header>





            {/* HERO */}



            <section className="hero">



              <div>



                <span className="status">



                  <span className="status-dot"></span>



                  NEXUS is online



                </span>





                <h2>

                  What are you working on?

                </h2>





                <p>

                  Ask questions, search your

                  knowledge, manage projects,

                  or let NEXUS help you get things done.

                </p>



              </div>





              <div className="ai-symbol">

                ✦

              </div>



            </section>





            {/* SEARCH */}



            <section className="search-box">



              <span>

                ✦

              </span>



              <input

                type="text"

                placeholder="Ask NEXUS anything..."

              />



              <button

                onClick={() =>

                  setActivePage('ai')

                }

              >

                ➜

              </button>



            </section>





            {/* =================================

                LIVE STATS

            ================================= */}



            <section className="stats">



              {/* PROJECTS */}



              <div className="stat-card">



                <span>

                  PROJECTS

                </span>



                <strong>

                  {dashboardLoading

                    ? '—'

                    : String(totalProjects).padStart(2, '0')}

                </strong>



              </div>





              {/* TASKS */}



              <div className="stat-card">



                <span>

                  TASKS

                </span>



                <strong>

                  {dashboardLoading

                    ? '—'

                    : String(totalTasks).padStart(2, '0')}

                </strong>



              </div>





              {/* DOCUMENTS */}



              <div className="stat-card">



                <span>

                  DOCUMENTS

                </span>



                <strong>

                  {dashboardLoading

                    ? '—'

                    : String(totalDocuments).padStart(2, '0')}

                </strong>



              </div>





              {/* COMPLETED TASKS */}



              <div className="stat-card">



                <span>

                  COMPLETED TASKS

                </span>



                <strong>

                  {dashboardLoading

                    ? '—'

                    : String(completedTasks).padStart(2, '0')}

                </strong>



              </div>



            </section>





            {/* =================================

                CONTENT GRID

            ================================= */}



            <section className="content-grid">





              {/* =================================

                  LIVE PROJECTS

              ================================= */}



              <div className="panel">



                <div className="panel-header">



                  <div>



                    <span className="panel-label">

                      ACTIVE WORK

                    </span>



                    <h3>

                      Projects

                    </h3>



                  </div>





                  <button

                    className="view-button"

                    onClick={() =>

                      setActivePage('projects')

                    }

                  >

                    View all →

                  </button>



                </div>





                {activeProjects.length === 0 ? (



                  <div className="task">



                    <div>

                      <strong>

                        No active projects

                      </strong>



                      <p>

                        Create your first project.

                      </p>

                    </div>



                  </div>



                ) : (



                  activeProjects

                    .slice(0, 4)

                    .map((project) => (



                      <div

                        className="project-item"

                        key={project.id}

                      >



                        <div className="project-icon">



                          {project.name

                            ?.substring(0, 2)

                            .toUpperCase()}



                        </div>





                        <div>



                          <strong>

                            {project.name}

                          </strong>



                          <p>

                            {project.description ||

                              'Active project'}

                          </p>



                        </div>





                        <span className="progress">

                          {project.progress || 0}%

                        </span>



                      </div>



                    ))



                )}



              </div>





              {/* =================================

                  LIVE TASKS

              ================================= */}



              <div className="panel">



                <div className="panel-header">



                  <div>



                    <span className="panel-label">

                      WORKFLOW

                    </span>



                    <h3>

                      Tasks

                    </h3>



                  </div>





                  <button

                    className="view-button"

                    onClick={() =>

                      setActivePage('tasks')

                    }

                  >

                    View all →

                  </button>



                </div>





                {tasks.length === 0 ? (



                  <div className="task">



                    <div>



                      <strong>

                        No tasks yet

                      </strong>



                      <p>

                        Create your first task.

                      </p>



                    </div>



                  </div>



                ) : (



                  tasks

                    .slice(0, 4)

                    .map((task) => (



                      <div

                        className={`task ${

                          task.completed

                            ? 'completed'

                            : ''

                        }`}

                        key={task.id}

                      >



                        <span

                          className={`checkbox ${

                            task.completed

                              ? 'checked'

                              : ''

                          }`}

                        >

                          {task.completed

                            ? '✓'

                            : ''}

                        </span>





                        <div>



                          <strong>

                            {task.title}

                          </strong>



                          <p>

                            {task.completed

                              ? 'Completed'

                              : 'Pending'}

                          </p>



                        </div>



                      </div>



                    ))



                )}



              </div>



            </section>



          </>



        )}



      </main>



    </div>

  );

}



export default App;