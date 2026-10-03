import { useEffect, useMemo, useState } from "react";
import {
  Plus,
  Search,
  Pin,
  PinOff,
  Trash2,
  Edit3,
  Save,
  X,
  Sparkles,
  FileText,
  Clock3,
  Tag,
  Brain,
  Check
} from "lucide-react";
import axios from "axios";

const API = "http://127.0.0.1:8000";

function Notes() {
  const [notes, setNotes] = useState([]);
  const [selectedNote, setSelectedNote] = useState(null);
  const [search, setSearch] = useState("");
  const [showEditor, setShowEditor] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const [form, setForm] = useState({
    title: "",
    content: "",
    category: "General",
    tags: ""
  });

  const loadNotes = async () => {
    try {
      setLoading(true);

      const response = await axios.get(`${API}/notes`);

      setNotes(response.data || []);
    } catch (error) {
      console.error("Failed to load notes:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotes();
  }, []);

  const filteredNotes = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) {
      return [...notes].sort(
        (a, b) => Number(b.pinned) - Number(a.pinned)
      );
    }

    return notes
      .filter((note) => {
        const text = `
          ${note.title || ""}
          ${note.content || ""}
          ${note.category || ""}
          ${note.tags || ""}
        `.toLowerCase();

        return text.includes(query);
      })
      .sort((a, b) => Number(b.pinned) - Number(a.pinned));
  }, [notes, search]);

  const resetForm = () => {
    setForm({
      title: "",
      content: "",
      category: "General",
      tags: ""
    });

    setEditingId(null);
  };

  const openCreate = () => {
    resetForm();
    setShowEditor(true);
    setSelectedNote(null);
  };

  const openEdit = (note) => {
    setEditingId(note.id);

    setForm({
      title: note.title || "",
      content: note.content || "",
      category: note.category || "General",
      tags: note.tags || ""
    });

    setShowEditor(true);
    setSelectedNote(note);
  };

  const saveNote = async () => {
    if (!form.title.trim() || !form.content.trim()) {
      setMessage("Title and content are required.");
      return;
    }

    try {
      setSaving(true);
      setMessage("");

      if (editingId) {
        await axios.put(`${API}/notes/${editingId}`, form);
      } else {
        await axios.post(`${API}/notes`, form);
      }

      await loadNotes();

      setShowEditor(false);
      resetForm();

      setMessage(
        editingId
          ? "Note updated successfully."
          : "Note created successfully."
      );
    } catch (error) {
      console.error("Failed to save note:", error);

      setMessage(
        error?.response?.data?.detail ||
          "Unable to save note."
      );
    } finally {
      setSaving(false);
    }
  };

  const deleteNote = async (id) => {
    const confirmed = window.confirm(
      "Delete this note permanently?"
    );

    if (!confirmed) return;

    try {
      await axios.delete(`${API}/notes/${id}`);

      if (selectedNote?.id === id) {
        setSelectedNote(null);
      }

      await loadNotes();

      setMessage("Note deleted.");
    } catch (error) {
      console.error("Failed to delete note:", error);
      setMessage("Unable to delete note.");
    }
  };

  const togglePin = async (note) => {
    try {
      await axios.patch(`${API}/notes/${note.id}/pin`, {
        pinned: !note.pinned
      });

      await loadNotes();

      if (selectedNote?.id === note.id) {
        setSelectedNote({
          ...note,
          pinned: !note.pinned
        });
      }
    } catch (error) {
      console.error("Failed to pin note:", error);
      setMessage("Unable to update pin status.");
    }
  };

  const summarizeNote = async () => {
    if (!selectedNote) return;

    try {
      setMessage("NEXUS is summarizing your note...");

      const response = await axios.post(`${API}/notes/ai/summarize`, {
        title: selectedNote.title,
        content: selectedNote.content
      });

      const summary =
        response.data?.summary ||
        response.data?.message ||
        "";

      if (!summary) {
        setMessage("No summary was generated.");
        return;
      }

      setSelectedNote({
        ...selectedNote,
        aiSummary: summary
      });

      setMessage("AI summary generated.");
    } catch (error) {
      console.error("AI summary error:", error);

      setMessage(
        error?.response?.data?.detail ||
          "AI summary is not available yet."
      );
    }
  };

  const improveNote = async () => {
    if (!selectedNote) return;

    try {
      setMessage("NEXUS is improving your note...");

      const response = await axios.post(`${API}/notes/ai/improve`, {
        title: selectedNote.title,
        content: selectedNote.content
      });

      const improved =
        response.data?.content ||
        response.data?.improved_content ||
        "";

      if (!improved) {
        setMessage("No improved content was generated.");
        return;
      }

      setSelectedNote({
        ...selectedNote,
        content: improved
      });

      setMessage("AI improved version generated.");
    } catch (error) {
      console.error("AI improve error:", error);

      setMessage(
        error?.response?.data?.detail ||
          "AI improve is not available yet."
      );
    }
  };

  const saveToKnowledge = async () => {
    if (!selectedNote) return;

    try {
      await axios.post(`${API}/knowledge`, {
        title: selectedNote.title,
        content: selectedNote.content,
        category: selectedNote.category || "Notes",
        source: "NEXUS Notes"
      });

      setMessage("Saved to Knowledge Vault successfully.");
    } catch (error) {
      console.error(
        "Failed to save to knowledge:",
        error
      );

      setMessage(
        error?.response?.data?.detail ||
          "Unable to save to Knowledge Vault."
      );
    }
  };

  const formatDate = (date) => {
    if (!date) return "Just now";

    const parsed = new Date(date);

    if (Number.isNaN(parsed.getTime())) {
      return "Just now";
    }

    return parsed.toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  };

  return (
    <div className="notes-page">
      <div className="notes-header">
        <div>
          <div className="section-kicker">
            PERSONAL KNOWLEDGE
          </div>

          <h1>Notes</h1>

          <p>
            Capture ideas, organize thoughts and let NEXUS
            turn your notes into knowledge.
          </p>
        </div>

        <button
          className="notes-primary-btn"
          onClick={openCreate}
        >
          <Plus size={18} />
          New Note
        </button>
      </div>

      <div className="notes-toolbar">
        <div className="notes-search">
          <Search size={18} />

          <input
            type="text"
            placeholder="Search your notes..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="notes-count">
          <FileText size={16} />
          {filteredNotes.length} notes
        </div>
      </div>

      {message && (
        <div className="notes-message">
          <Check size={16} />
          {message}
        </div>
      )}

      {loading ? (
        <div className="notes-empty">
          <Brain size={32} />
          <h3>Loading your notes...</h3>
        </div>
      ) : filteredNotes.length === 0 ? (
        <div className="notes-empty">
          <div className="notes-empty-icon">
            <FileText size={30} />
          </div>

          <h2>No notes yet</h2>

          <p>
            Start capturing your ideas and let NEXUS
            organize your thinking.
          </p>

          <button
            className="notes-primary-btn"
            onClick={openCreate}
          >
            <Plus size={18} />
            Create your first note
          </button>
        </div>
      ) : (
        <div className="notes-layout">
          <div className="notes-grid">
            {filteredNotes.map((note) => (
              <article
                key={note.id}
                className={`note-card ${
                  selectedNote?.id === note.id
                    ? "selected"
                    : ""
                }`}
                onClick={() => {
                  setSelectedNote(note);
                  setShowEditor(false);
                }}
              >
                <div className="note-card-top">
                  <span className="note-category">
                    <Tag size={13} />
                    {note.category || "General"}
                  </span>

                  <button
                    className="note-icon-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      togglePin(note);
                    }}
                    title={
                      note.pinned
                        ? "Unpin note"
                        : "Pin note"
                    }
                  >
                    {note.pinned ? (
                      <PinOff size={16} />
                    ) : (
                      <Pin size={16} />
                    )}
                  </button>
                </div>

                <h3>{note.title}</h3>

                <p>
                  {note.content?.length > 160
                    ? `${note.content.slice(
                        0,
                        160
                      )}...`
                    : note.content}
                </p>

                <div className="note-card-bottom">
                  <span>
                    <Clock3 size={13} />
                    {formatDate(
                      note.updated_at ||
                        note.created_at
                    )}
                  </span>

                  {note.tags && (
                    <span className="note-tags">
                      {note.tags}
                    </span>
                  )}
                </div>
              </article>
            ))}
          </div>

          {selectedNote && !showEditor && (
            <aside className="note-detail">
              <div className="note-detail-header">
                <div>
                  <span className="note-category">
                    <Tag size={13} />
                    {selectedNote.category ||
                      "General"}
                  </span>

                  <h2>{selectedNote.title}</h2>
                </div>

                <div className="note-detail-actions">
                  <button
                    className="note-icon-btn"
                    onClick={() =>
                      togglePin(selectedNote)
                    }
                  >
                    {selectedNote.pinned ? (
                      <PinOff size={17} />
                    ) : (
                      <Pin size={17} />
                    )}
                  </button>

                  <button
                    className="note-icon-btn"
                    onClick={() =>
                      openEdit(selectedNote)
                    }
                  >
                    <Edit3 size={17} />
                  </button>

                  <button
                    className="note-icon-btn danger"
                    onClick={() =>
                      deleteNote(selectedNote.id)
                    }
                  >
                    <Trash2 size={17} />
                  </button>

                  <button
                    className="note-icon-btn"
                    onClick={() =>
                      setSelectedNote(null)
                    }
                  >
                    <X size={17} />
                  </button>
                </div>
              </div>

              <div className="note-detail-content">
                {selectedNote.content}
              </div>

              {selectedNote.tags && (
                <div className="note-detail-tags">
                  <Tag size={15} />
                  {selectedNote.tags}
                </div>
              )}

              {selectedNote.aiSummary && (
                <div className="ai-summary-box">
                  <div className="ai-summary-title">
                    <Sparkles size={16} />
                    NEXUS AI Summary
                  </div>

                  <p>{selectedNote.aiSummary}</p>
                </div>
              )}

              <div className="note-ai-actions">
                <button onClick={summarizeNote}>
                  <Sparkles size={16} />
                  Summarize
                </button>

                <button onClick={improveNote}>
                  <Brain size={16} />
                  Improve with AI
                </button>

                <button onClick={saveToKnowledge}>
                  <Save size={16} />
                  Save to Knowledge
                </button>
              </div>
            </aside>
          )}
        </div>
      )}

      {showEditor && (
        <div className="note-editor-overlay">
          <div className="note-editor">
            <div className="note-editor-header">
              <div>
                <span className="section-kicker">
                  {editingId
                    ? "EDIT NOTE"
                    : "NEW NOTE"}
                </span>

                <h2>
                  {editingId
                    ? "Edit your note"
                    : "Create a new note"}
                </h2>
              </div>

              <button
                className="note-icon-btn"
                onClick={() => {
                  setShowEditor(false);
                  resetForm();
                }}
              >
                <X size={18} />
              </button>
            </div>

            <div className="note-form">
              <input
                className="note-title-input"
                placeholder="Note title..."
                value={form.title}
                onChange={(e) =>
                  setForm({
                    ...form,
                    title: e.target.value
                  })
                }
              />

              <div className="note-form-row">
                <select
                  value={form.category}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      category: e.target.value
                    })
                  }
                >
                  <option>General</option>
                  <option>Learning</option>
                  <option>Ideas</option>
                  <option>Projects</option>
                  <option>Work</option>
                  <option>Personal</option>
                  <option>Research</option>
                </select>

                <input
                  placeholder="Tags: react, AI, project"
                  value={form.tags}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      tags: e.target.value
                    })
                  }
                />
              </div>

              <textarea
                className="note-content-input"
                placeholder="Start writing your thoughts..."
                value={form.content}
                onChange={(e) =>
                  setForm({
                    ...form,
                    content: e.target.value
                  })
                }
              />

              <div className="note-editor-footer">
                <button
                  className="notes-secondary-btn"
                  onClick={() => {
                    setShowEditor(false);
                    resetForm();
                  }}
                >
                  Cancel
                </button>

                <button
                  className="notes-primary-btn"
                  onClick={saveNote}
                  disabled={saving}
                >
                  <Save size={17} />
                  {saving
                    ? "Saving..."
                    : editingId
                    ? "Update Note"
                    : "Save Note"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Notes;