import { useEffect, useState } from 'react';
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000';

function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [taskText, setTaskText] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // =========================
  // LOAD TASKS
  // =========================

  const loadTasks = async () => {
    try {
      setError('');

      const response = await axios.get(
        `${API_URL}/tasks`
      );

      setTasks(response.data);

    } catch (error) {
      console.error(
        'Task fetch error:',
        error
      );

      setError(
        'Could not load tasks. Make sure the backend is running.'
      );

    } finally {
      setLoading(false);
    }
  };


  // =========================
  // INITIAL LOAD
  // =========================

  useEffect(() => {
    loadTasks();
  }, []);


  // =========================
  // ADD TASK
  // =========================

  const addTask = async () => {
    const title = taskText.trim();

    if (!title || saving) {
      return;
    }

    setSaving(true);
    setError('');

    try {
      const response = await axios.post(
        `${API_URL}/tasks`,
        {
          title,
          completed: false,
        }
      );

      setTasks((prev) => [
        response.data,
        ...prev,
      ]);

      setTaskText('');

    } catch (error) {
      console.error(
        'Task create error:',
        error
      );

      setError(
        'Could not create the task.'
      );

    } finally {
      setSaving(false);
    }
  };


  // =========================
  // TOGGLE TASK
  // =========================

  const toggleTask = async (task) => {
    setError('');

    try {
      const response = await axios.put(
        `${API_URL}/tasks/${task.id}`,
        {
          title: task.title,
          completed: !task.completed,
        }
      );

      setTasks((prev) =>
        prev.map((item) =>
          item.id === task.id
            ? response.data
            : item
        )
      );

    } catch (error) {
      console.error(
        'Task update error:',
        error
      );

      setError(
        'Could not update the task.'
      );
    }
  };


  // =========================
  // DELETE TASK
  // =========================

  const deleteTask = async (id) => {

    const confirmed = window.confirm(
      'Are you sure you want to delete this task?'
    );

    if (!confirmed) {
      return;
    }

    setError('');

    try {
      await axios.delete(
        `${API_URL}/tasks/${id}`
      );

      setTasks((prev) =>
        prev.filter(
          (task) => task.id !== id
        )
      );

    } catch (error) {
      console.error(
        'Task delete error:',
        error
      );

      setError(
        'Could not delete the task.'
      );
    }
  };


  // =========================
  // STATS
  // =========================

  const completedCount =
    tasks.filter(
      (task) => task.completed
    ).length;

  const pendingCount =
    tasks.length - completedCount;


  // =========================
  // RENDER
  // =========================

  return (
    <div className="tasks-page">

      {/* ========================= */}
      {/* HEADER */}
      {/* ========================= */}

      <div className="tasks-header">

        <div>

          <span className="tasks-eyebrow">
            PERSONAL PRODUCTIVITY
          </span>

          <h1>
            Tasks
          </h1>

          <p>
            Manage your work, priorities and daily goals.
          </p>

        </div>


        {/* STATS */}

        <div className="tasks-stats">

          <div className="task-stat">

            <strong>
              {tasks.length}
            </strong>

            <span>
              Total
            </span>

          </div>


          <div className="task-stat">

            <strong>
              {pendingCount}
            </strong>

            <span>
              Pending
            </span>

          </div>


          <div className="task-stat">

            <strong>
              {completedCount}
            </strong>

            <span>
              Done
            </span>

          </div>

        </div>

      </div>


      {/* ========================= */}
      {/* ERROR */}
      {/* ========================= */}

      {error && (

        <div className="task-error">
          ⚠ {error}
        </div>

      )}


      {/* ========================= */}
      {/* ADD TASK */}
      {/* ========================= */}

      <div className="task-add-box">

        <div className="task-input-icon">
          ✦
        </div>


        <input
          type="text"
          placeholder="What do you need to do?"
          value={taskText}
          onChange={(e) =>
            setTaskText(e.target.value)
          }
          onKeyDown={(e) => {

            if (e.key === 'Enter') {
              addTask();
            }

          }}
          disabled={saving}
        />


        <button
          className="add-task-button"
          onClick={addTask}
          disabled={
            saving ||
            !taskText.trim()
          }
        >

          {saving
            ? 'Saving...'
            : '＋ Add Task'}

        </button>

      </div>


      {/* ========================= */}
      {/* TASK LIST */}
      {/* ========================= */}

      {loading ? (

        <div className="tasks-empty">

          <div className="tasks-empty-icon">
            ✦
          </div>

          <h2>
            Loading tasks...
          </h2>

          <p>
            NEXUS is loading your tasks.
          </p>

        </div>

      ) : tasks.length === 0 ? (

        <div className="tasks-empty">

          <div className="tasks-empty-icon">
            ✓
          </div>

          <h2>
            No tasks yet
          </h2>

          <p>
            Create your first task above.
          </p>

        </div>

      ) : (

        <div className="tasks-list">

          {tasks.map((task) => (

            <div
              className={`task-card ${
                task.completed
                  ? 'completed'
                  : ''
              }`}
              key={task.id}
            >

              {/* CHECKBOX */}

              <button
                className={`task-checkbox ${
                  task.completed
                    ? 'checked'
                    : ''
                }`}
                onClick={() =>
                  toggleTask(task)
                }
                title={
                  task.completed
                    ? 'Mark as pending'
                    : 'Mark as completed'
                }
              >

                {task.completed
                  ? '✓'
                  : ''}

              </button>


              {/* TASK INFO */}

              <div className="task-info">

                <strong>
                  {task.title}
                </strong>

                <p>
                  {task.completed
                    ? 'Completed'
                    : 'Pending task'}
                </p>

              </div>


              {/* STATUS */}

              <span
                className={`task-status ${
                  task.completed
                    ? 'done'
                    : 'pending'
                }`}
              >

                {task.completed
                  ? 'DONE'
                  : 'PENDING'}

              </span>


              {/* DELETE */}

              <button
                className="task-delete"
                onClick={() =>
                  deleteTask(task.id)
                }
                title="Delete task"
              >
                🗑
              </button>

            </div>

          ))}

        </div>

      )}

    </div>
  );
}

export default Tasks;