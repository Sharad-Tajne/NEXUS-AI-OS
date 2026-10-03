import { useEffect, useState } from 'react';

import axios from 'axios';



const API_URL = 'http://127.0.0.1:8000';



function Projects() {

  const [projects, setProjects] = useState([]);

  const [loading, setLoading] = useState(true);



  const [showForm, setShowForm] = useState(false);

  const [saving, setSaving] = useState(false);

  const [editingProject, setEditingProject] = useState(null);
  const [insightsProject, setInsightsProject] = useState(null);
  const [insights, setInsights] = useState(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsError, setInsightsError] = useState('');



  const [form, setForm] = useState({

    name: '',

    description: '',

    technology: '',

    status: 'active',

    progress: 0,

  });



  const loadProjects = async () => {

    try {

      const response = await axios.get(`${API_URL}/projects`);

      setProjects(response.data);

    } catch (error) {

      console.error('Projects fetch error:', error);

    } finally {

      setLoading(false);

    }

  };



  useEffect(() => {

    loadProjects();

  }, []);



  const resetForm = () => {

    setForm({

      name: '',

      description: '',

      technology: '',

      status: 'active',

      progress: 0,

    });



    setEditingProject(null);

    setShowForm(false);

  };



  const handleChange = (e) => {

    const { name, value } = e.target;



    setForm((prev) => ({

      ...prev,

      [name]: value,

    }));

  };



  const openCreateForm = () => {

    setForm({

      name: '',

      description: '',

      technology: '',

      status: 'active',

      progress: 0,

    });



    setEditingProject(null);

    setShowForm(true);

  };



  const openEditForm = (project) => {

    setForm({

      name: project.name || '',

      description: project.description || '',

      technology: project.technology || '',

      status: project.status || 'active',

      progress: project.progress || 0,

    });



    setEditingProject(project);

    setShowForm(true);

  };



  const saveProject = async (e) => {

    e.preventDefault();



    if (!form.name.trim() || saving) return;



    setSaving(true);



    const projectData = {

      name: form.name.trim(),

      description: form.description.trim(),

      technology: form.technology.trim(),

      status: form.status,

      progress: Number(form.progress),

    };



    try {

      if (editingProject) {

        const response = await axios.put(

          `${API_URL}/projects/${editingProject.id}`,

          projectData

        );



        setProjects((prev) =>

          prev.map((project) =>

            project.id === editingProject.id

              ? response.data

              : project

          )

        );

      } else {

        const response = await axios.post(

          `${API_URL}/projects`,

          projectData

        );



        setProjects((prev) => [

          response.data,

          ...prev,

        ]);

      }



      resetForm();



    } catch (error) {

      console.error('Project save error:', error);

      alert('Could not save project.');

    } finally {

      setSaving(false);

    }

  };



  const deleteProject = async (id) => {

    const confirmed = window.confirm(

      'Are you sure you want to delete this project?'

    );



    if (!confirmed) return;



    try {

      await axios.delete(`${API_URL}/projects/${id}`);



      setProjects((prev) =>

        prev.filter((project) => project.id !== id)

      );



    } catch (error) {

      console.error('Project delete error:', error);

      alert('Could not delete project.');

    }

  };



  const openInsights = async (project) => {
    setInsightsProject(project);
    setInsights(null);
    setInsightsError('');
    setInsightsLoading(true);

    try {
      const response = await axios.get(
        `${API_URL}/projects/${project.id}/insights`
      );

      if (!response.data?.success) {
        throw new Error(
          response.data?.message || 'Could not generate project insights.'
        );
      }

      setInsights(response.data);
    } catch (error) {
      console.error('Project insights error:', error);
      setInsightsError(
        error.response?.data?.message ||
          error.message ||
          'Could not generate project insights.'
      );
    } finally {
      setInsightsLoading(false);
    }
  };

  const closeInsights = () => {
    if (insightsLoading) return;
    setInsightsProject(null);
    setInsights(null);
    setInsightsError('');
  };

  return (

    <div className="projects-page">



      {/* HEADER */}



      <div className="projects-header">



        <div>

          <span className="projects-eyebrow">

            WORKSPACE MANAGEMENT

          </span>



          <h1>Projects</h1>



          <p>

            Manage your projects, technologies and development progress.

          </p>

        </div>



        <button

          className="add-project-button"

          onClick={openCreateForm}

        >

          ＋ New Project

        </button>



      </div>





      {/* STATS */}



      <div className="projects-stats">



        <div className="project-stat">

          <span>TOTAL PROJECTS</span>

          <strong>{projects.length}</strong>

        </div>



        <div className="project-stat">

          <span>ACTIVE</span>



          <strong>

            {

              projects.filter(

                (project) =>

                  project.status === 'active'

              ).length

            }

          </strong>

        </div>



        <div className="project-stat">

          <span>COMPLETED</span>



          <strong>

            {

              projects.filter(

                (project) =>

                  project.status === 'completed'

              ).length

            }

          </strong>

        </div>



      </div>





      {/* CREATE / EDIT FORM */}



      {showForm && (



        <div className="project-form-overlay">



          <div className="project-form-card">



            <div className="project-form-header">



              <div>



                <span className="projects-eyebrow">

                  {editingProject

                    ? 'PROJECT MANAGEMENT'

                    : 'NEW WORKSPACE PROJECT'}

                </span>



                <h2>

                  {editingProject

                    ? 'Edit Project'

                    : 'Create Project'}

                </h2>



              </div>



              <button

                className="project-close-button"

                onClick={resetForm}

              >

                ×

              </button>



            </div>





            <form onSubmit={saveProject}>



              {/* NAME */}



              <div className="project-form-group">



                <label>

                  Project Name

                </label>



                <input

                  type="text"

                  name="name"

                  placeholder="e.g. NEXUS AI OS"

                  value={form.name}

                  onChange={handleChange}

                  required

                />



              </div>





              {/* DESCRIPTION */}



              <div className="project-form-group">



                <label>

                  Description

                </label>



                <textarea

                  name="description"

                  placeholder="Describe your project..."

                  value={form.description}

                  onChange={handleChange}

                  rows="4"

                />



              </div>





              {/* TECHNOLOGY */}



              <div className="project-form-group">



                <label>

                  Technologies

                </label>



                <input

                  type="text"

                  name="technology"

                  placeholder="React, FastAPI, PostgreSQL, Gemini"

                  value={form.technology}

                  onChange={handleChange}

                />



                <small>

                  Separate technologies using commas.

                </small>



              </div>





              {/* STATUS + PROGRESS */}



              <div className="project-form-row">



                <div className="project-form-group">



                  <label>

                    Status

                  </label>



                  <select

                    name="status"

                    value={form.status}

                    onChange={handleChange}

                  >

                    <option value="active">

                      Active

                    </option>



                    <option value="completed">

                      Completed

                    </option>



                    <option value="paused">

                      Paused

                    </option>



                  </select>



                </div>





                <div className="project-form-group">



                  <label>

                    Progress %

                  </label>



                  <input

                    type="number"

                    name="progress"

                    min="0"

                    max="100"

                    value={form.progress}

                    onChange={handleChange}

                  />



                </div>



              </div>





              {/* BUTTONS */}



              <div className="project-form-actions">



                <button

                  type="button"

                  className="project-cancel-button"

                  onClick={resetForm}

                >

                  Cancel

                </button>



                <button

                  type="submit"

                  className="project-save-button"

                  disabled={saving}

                >

                  {saving

                    ? 'Saving...'

                    : editingProject

                      ? 'Save Changes'

                      : 'Create Project'}

                </button>



              </div>



            </form>



          </div>



        </div>



      )}





      {insightsProject && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 2000,
            background: 'rgba(31, 41, 74, 0.28)',
            backdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
          }}
          onClick={closeInsights}
        >
          <div
            style={{
              width: 'min(900px, 100%)',
              maxHeight: '88vh',
              overflowY: 'auto',
              background: '#ffffff',
              border: '1px solid rgba(130, 110, 255, 0.18)',
              borderRadius: '24px',
              boxShadow: '0 30px 90px rgba(45, 40, 100, 0.22)',
              padding: '28px',
            }}
            onClick={(event) => event.stopPropagation()}
          >
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',gap:'20px',marginBottom:'24px'}}>
              <div>
                <span style={{fontSize:'11px',fontWeight:800,letterSpacing:'0.14em',color:'#7567f8'}}>
                  NEXUS PROJECT INTELLIGENCE
                </span>
                <h2 style={{margin:'8px 0 6px',fontSize:'28px',color:'#1f2440'}}>
                  {insightsProject.name}
                </h2>
                <p style={{margin:0,color:'#747a91',fontSize:'14px'}}>
                  AI-generated project analysis from your tasks, notes and Knowledge Vault.
                </p>
              </div>
              <button type="button" onClick={closeInsights} disabled={insightsLoading}
                style={{border:'none',background:'#f4f3ff',color:'#5f55d9',width:'40px',height:'40px',borderRadius:'12px',fontSize:'22px',cursor:insightsLoading?'not-allowed':'pointer'}}>
                ×
              </button>
            </div>

            {insightsLoading && (
              <div style={{padding:'50px 20px',textAlign:'center',borderRadius:'18px',background:'#f8f8ff'}}>
                <div style={{fontSize:'34px',marginBottom:'12px'}}>✦</div>
                <h3 style={{margin:'0 0 8px',color:'#252943'}}>NEXUS is analyzing your project...</h3>
                <p style={{margin:0,color:'#777d93'}}>Reading progress, tasks, notes and relevant knowledge.</p>
              </div>
            )}

            {!insightsLoading && insightsError && (
              <div style={{padding:'18px',borderRadius:'16px',background:'#fff5f5',border:'1px solid #ffd5d5',color:'#b42318'}}>
                {insightsError}
              </div>
            )}

            {!insightsLoading && !insightsError && insights?.insights && (
              <div>
                <div style={{display:'grid',gridTemplateColumns:'repeat(4,minmax(0,1fr))',gap:'12px',marginBottom:'20px'}}>
                  {[
                    ['Progress', String(insights.insights.current_state?.progress ?? 0).endsWith('%') ? String(insights.insights.current_state?.progress ?? 0) : `${insights.insights.current_state?.progress ?? 0}%`],
                    ['Total Tasks', insights.insights.current_state?.total_tasks ?? 0],
                    ['Completed', insights.insights.current_state?.completed_tasks ?? 0],
                    ['Pending', insights.insights.current_state?.pending_tasks ?? 0],
                  ].map(([label,value]) => (
                    <div key={label} style={{padding:'16px',borderRadius:'16px',background:'#f8f8ff',border:'1px solid #ecebfa'}}>
                      <div style={{fontSize:'11px',fontWeight:700,color:'#858ba0',marginBottom:'7px'}}>{label}</div>
                      <strong style={{fontSize:'24px',color:'#272b47'}}>{value}</strong>
                    </div>
                  ))}
                </div>

                <div style={{padding:'20px',borderRadius:'18px',background:'linear-gradient(135deg,#f5f3ff,#f2f7ff)',border:'1px solid #e7e4ff',marginBottom:'16px'}}>
                  <h3 style={{margin:'0 0 9px',color:'#272b47'}}>AI Summary</h3>
                  <p style={{margin:0,lineHeight:1.7,color:'#626980'}}>
                    {insights.insights.summary || 'No summary generated.'}
                  </p>
                </div>

                <div style={{display:'grid',gridTemplateColumns:'repeat(2,minmax(0,1fr))',gap:'16px'}}>
                  {[
                    ['Completed Work', insights.insights.completed_work, '✓'],
                    ['Pending Work', insights.insights.pending_work, '◌'],
                    ['Important Knowledge', insights.insights.important_knowledge, '✦'],
                    ['Next Actions', insights.insights.next_actions, '→'],
                  ].map(([title,items,icon]) => (
                    <div key={title} style={{padding:'20px',borderRadius:'18px',background:'#fff',border:'1px solid #ececf5'}}>
                      <h3 style={{margin:'0 0 14px',color:'#2a2e49',fontSize:'16px'}}>{icon} {title}</h3>
                      {Array.isArray(items) && items.length > 0 ? (
                        <ul style={{margin:0,paddingLeft:'20px',color:'#656b82',lineHeight:1.7}}>
                          {items.map((item,index) => <li key={`${title}-${index}`}>{item}</li>)}
                        </ul>
                      ) : (
                        <p style={{margin:0,color:'#9297aa'}}>Nothing to show.</p>
                      )}
                    </div>
                  ))}
                </div>

                <div style={{marginTop:'16px',display:'flex',gap:'10px',flexWrap:'wrap',color:'#7b8095',fontSize:'13px'}}>
                  <span>Notes analyzed: {insights.notes_count ?? 0}</span>
                  <span>•</span>
                  <span>Knowledge items matched: {insights.knowledge_count ?? 0}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* PROJECTS */}



      {loading ? (



        <div className="projects-empty">



          <div className="projects-empty-icon">

            ✦

          </div>



          <h2>

            Loading projects...

          </h2>



          <p>

            NEXUS is loading your projects.

          </p>



        </div>



      ) : projects.length === 0 ? (



        <div className="projects-empty">



          <div className="projects-empty-icon">

            ◈

          </div>



          <h2>

            No projects yet

          </h2>



          <p>

            Create your first project to get started.

          </p>



        </div>



      ) : (



        <div className="projects-grid">



          {projects.map((project) => (



            <div

              className="project-card"

              key={project.id}

            >



              {/* CARD TOP */}



              <div className="project-card-top">



                <div className="project-card-icon">

                  {project.name

                    ?.substring(0, 2)

                    .toUpperCase()}

                </div>



                <span

                  className={`project-status ${

                    project.status === 'completed'

                      ? 'completed'

                      : project.status === 'paused'

                        ? 'paused'

                        : 'active'

                  }`}

                >

                  {project.status}

                </span>



              </div>





              {/* CONTENT */}



              <div className="project-card-content">



                <h2>

                  {project.name}

                </h2>



                <p>

                  {project.description ||

                    'No project description available.'}

                </p>



              </div>





              {/* TECHNOLOGIES */}



              <div className="project-technologies">



                {project.technology

                  ? project.technology

                      .split(',')

                      .map((tech, index) => (

                        <span key={index}>

                          {tech.trim()}

                        </span>

                      ))

                  : (

                    <span>

                      No technologies added

                    </span>

                  )}



              </div>





              {/* PROGRESS */}



              <div className="project-progress-section">



                <div className="project-progress-header">



                  <span>

                    Progress

                  </span>



                  <strong>

                    {project.progress || 0}%

                  </strong>



                </div>



                <div className="project-progress-bar">



                  <div

                    className="project-progress-fill"

                    style={{

                      width: `${project.progress || 0}%`,

                    }}

                  />



                </div>



              </div>





              {/* FOOTER */}



              <div className="project-card-footer">



                <span>

                  Project #{project.id}

                </span>



                <div className="project-card-actions">



                  <button
                    type="button"
                    className="project-edit-button"
                    onClick={() => openInsights(project)}
                    style={{
                      background: 'linear-gradient(135deg, #7567f8, #5b8def)',
                      color: '#fff',
                      border: 'none',
                    }}
                  >
                    ✦ AI Insights
                  </button>

                  <button

                    className="project-edit-button"

                    onClick={() =>

                      openEditForm(project)

                    }

                  >

                    ✎ Edit

                  </button>



                  <button

                    className="project-delete-button"

                    onClick={() =>

                      deleteProject(project.id)

                    }

                  >

                    🗑 Delete

                  </button>



                </div>



              </div>



            </div>



          ))}



        </div>



      )}



    </div>

  );

}



export default Projects;