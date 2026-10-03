import { useEffect, useState } from 'react';
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000';

function KnowledgeVault() {
  const [knowledge, setKnowledge] = useState([]);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [searchMode, setSearchMode] = useState('normal');
  const [semanticResults, setSemanticResults] = useState([]);
  const [searchingAI, setSearchingAI] = useState(false);

  const [showForm, setShowForm] = useState(false);

  const [form, setForm] = useState({
    title: '',
    content: '',
    category: 'general',
    source: '',
  });

  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  // ================================
  // LOAD KNOWLEDGE
  // ================================

  const loadKnowledge = async () => {
    try {
      setLoading(true);

      const response = await axios.get(
        `${API_URL}/knowledge`
      );

      setKnowledge(response.data || []);
    } catch (error) {
      console.error(
        'Knowledge fetch error:',
        error
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKnowledge();
  }, []);

  // ================================
  // FORM INPUT
  // ================================

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  // ================================
  // SAVE KNOWLEDGE
  // ================================

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (
      !form.title.trim() ||
      !form.content.trim()
    ) {
      return;
    }

    setSaving(true);

    try {
      await axios.post(
        `${API_URL}/knowledge`,
        {
          title: form.title.trim(),
          content: form.content.trim(),
          category: form.category,
          source: form.source.trim(),
        }
      );

      setForm({
        title: '',
        content: '',
        category: 'general',
        source: '',
      });

      setShowForm(false);

      await loadKnowledge();
    } catch (error) {
      console.error(
        'Knowledge save error:',
        error
      );

      alert(
        'Could not save this knowledge item.'
      );
    } finally {
      setSaving(false);
    }
  };

  // ================================
  // DELETE KNOWLEDGE
  // ================================

  const handleDelete = async (itemId) => {
    const confirmed = window.confirm(
      'Are you sure you want to delete this knowledge item?'
    );

    if (!confirmed) {
      return;
    }

    setDeletingId(itemId);

    try {
      await axios.delete(
        `${API_URL}/knowledge/${itemId}`
      );

      setKnowledge((prev) =>
        prev.filter(
          (item) => item.id !== itemId
        )
      );

      setSemanticResults((prev) =>
        prev.filter(
          (item) => item.id !== itemId
        )
      );
    } catch (error) {
      console.error(
        'Knowledge delete error:',
        error
      );

      alert(
        'Could not delete this knowledge item.'
      );
    } finally {
      setDeletingId(null);
    }
  };

  // ================================
  // AI SEMANTIC SEARCH
  // ================================

  const handleSemanticSearch = async () => {
    const query = search.trim();

    if (!query) {
      setSemanticResults([]);
      return;
    }

    setSearchingAI(true);

    try {
      const response = await axios.get(
        `${API_URL}/knowledge/search`,
        {
          params: {
            q: query,
          },
        }
      );

      setSemanticResults(
        response.data || []
      );
    } catch (error) {
      console.error(
        'Semantic search error:',
        error
      );

      setSemanticResults([]);
    } finally {
      setSearchingAI(false);
    }
  };

  // ================================
  // SEARCH MODE
  // ================================

  const handleSearchModeChange = (mode) => {
    setSearchMode(mode);

    if (mode === 'normal') {
      setSemanticResults([]);
    }
  };

  // ================================
  // NORMAL SEARCH
  // ================================

  const filteredKnowledge =
    knowledge.filter((item) => {
      const query =
        search.toLowerCase().trim();

      if (!query) {
        return true;
      }

      return (
        item.title
          ?.toLowerCase()
          .includes(query) ||
        item.content
          ?.toLowerCase()
          .includes(query) ||
        item.category
          ?.toLowerCase()
          .includes(query) ||
        item.source
          ?.toLowerCase()
          .includes(query)
      );
    });

  const displayedKnowledge =
    searchMode === 'ai'
      ? semanticResults
      : filteredKnowledge;

  // ================================
  // CATEGORY ICON
  // ================================

  const getCategoryIcon = (category) => {
    const value =
      category?.toLowerCase();

    if (value === 'project') {
      return '◈';
    }

    if (value === 'learning') {
      return '⌘';
    }

    if (value === 'idea') {
      return '✦';
    }

    if (value === 'note') {
      return '✎';
    }

    if (value === 'reference') {
      return '◎';
    }

    return '◇';
  };

  // ================================
  // UI
  // ================================

  return (
    <div className="knowledge-page">

      {/* ================================
          HEADER
      ================================= */}

      <div className="knowledge-header">

        <div>
          <span className="knowledge-eyebrow">
            PERSONAL KNOWLEDGE
          </span>

          <h1>
            Knowledge Vault
          </h1>

          <p>
            Your personal collection of
            knowledge, notes and project
            information.
          </p>
        </div>

        <div className="knowledge-header-actions">

          <div className="knowledge-count">
            <strong>
              {knowledge.length}
            </strong>

            <span>
              Items
            </span>
          </div>

          <button
            className="add-knowledge-button"
            onClick={() =>
              setShowForm(!showForm)
            }
          >
            <span>＋</span>
            Add Knowledge
          </button>

        </div>
      </div>

      {/* ================================
          AI SEARCH INTRO
      ================================= */}

      <div
        style={{
          marginBottom: '18px',
          padding: '18px 20px',
          borderRadius: '20px',
          background:
            'linear-gradient(135deg, rgba(124,92,255,0.10), rgba(91,141,239,0.08))',
          border:
            '1px solid rgba(124,92,255,0.14)',
        }}
      >

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >

          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '14px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background:
                'rgba(124,92,255,0.12)',
              fontSize: '20px',
            }}
          >
            ✦
          </div>

          <div>

            <strong
              style={{
                display: 'block',
                fontSize: '14px',
                color: '#34334a',
              }}
            >
              NEXUS Semantic Knowledge
            </strong>

            <span
              style={{
                display: 'block',
                marginTop: '3px',
                fontSize: '12px',
                color: '#77758a',
              }}
            >
              Search by meaning, not just
              exact words.
            </span>

          </div>

        </div>

      </div>

      {/* ================================
          ADD KNOWLEDGE FORM
      ================================= */}

      {showForm && (

        <form
          className="knowledge-form"
          onSubmit={handleSubmit}
        >

          <div className="form-header">

            <div>
              <span className="knowledge-eyebrow">
                NEW ENTRY
              </span>

              <h2>
                Add Knowledge
              </h2>
            </div>

            <button
              type="button"
              className="form-close"
              onClick={() =>
                setShowForm(false)
              }
            >
              ×
            </button>

          </div>

          <div className="form-grid">

            <div className="form-field">

              <label>
                Title
              </label>

              <input
                type="text"
                name="title"
                placeholder="e.g. NEXUS AI OS"
                value={form.title}
                onChange={handleChange}
              />

            </div>

            <div className="form-field">

              <label>
                Category
              </label>

              <select
                name="category"
                value={form.category}
                onChange={handleChange}
              >

                <option value="general">
                  General
                </option>

                <option value="project">
                  Project
                </option>

                <option value="learning">
                  Learning
                </option>

                <option value="idea">
                  Idea
                </option>

                <option value="note">
                  Note
                </option>

                <option value="reference">
                  Reference
                </option>

              </select>

            </div>

            <div className="form-field full">

              <label>
                Content
              </label>

              <textarea
                name="content"
                placeholder="Write your knowledge here..."
                rows="5"
                value={form.content}
                onChange={handleChange}
              />

            </div>

            <div className="form-field full">

              <label>
                Source
              </label>

              <input
                type="text"
                name="source"
                placeholder="e.g. Personal Project, Course, Website..."
                value={form.source}
                onChange={handleChange}
              />

            </div>

          </div>

          <div className="form-actions">

            <button
              type="button"
              className="cancel-button"
              onClick={() =>
                setShowForm(false)
              }
            >
              Cancel
            </button>

            <button
              type="submit"
              className="save-knowledge-button"
              disabled={saving}
            >
              {saving
                ? 'Saving...'
                : 'Save Knowledge'}
            </button>

          </div>

        </form>
      )}

      {/* ================================
          SEARCH
      ================================= */}

      <div className="knowledge-search">

        <span>
          {searchMode === 'ai'
            ? '✦'
            : '⌕'}
        </span>

        <input
          type="text"
          placeholder={
            searchMode === 'ai'
              ? 'Ask your knowledge something...'
              : 'Search your knowledge...'
          }
          value={search}
          onChange={(e) =>
            setSearch(e.target.value)
          }
          onKeyDown={(e) => {
            if (
              e.key === 'Enter' &&
              searchMode === 'ai'
            ) {
              handleSemanticSearch();
            }
          }}
        />

        {searchMode === 'ai' &&
          search.trim() && (
            <button
              type="button"
              onClick={handleSemanticSearch}
              disabled={searchingAI}
              style={{
                border: 'none',
                borderRadius: '10px',
                padding: '8px 12px',
                background:
                  '#7c5cff',
                color: '#fff',
                cursor:
                  searchingAI
                    ? 'default'
                    : 'pointer',
                fontWeight: '600',
              }}
            >
              {searchingAI
                ? 'Thinking...'
                : 'Search AI'}
            </button>
          )}

        <span className="search-count">
          {displayedKnowledge.length} results
        </span>

      </div>

      {/* ================================
          SEARCH MODES
      ================================= */}

      <div
        style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '20px',
        }}
      >

        <button
          type="button"
          onClick={() =>
            handleSearchModeChange('normal')
          }
          style={{
            border: '1px solid rgba(124,92,255,0.15)',
            background:
              searchMode === 'normal'
                ? 'rgba(124,92,255,0.10)'
                : '#fff',
            color:
              searchMode === 'normal'
                ? '#6b5ce7'
                : '#777',
            padding: '8px 14px',
            borderRadius: '10px',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '12px',
          }}
        >
          ⌕ Normal Search
        </button>

        <button
          type="button"
          onClick={() =>
            handleSearchModeChange('ai')
          }
          style={{
            border: '1px solid rgba(124,92,255,0.15)',
            background:
              searchMode === 'ai'
                ? 'rgba(124,92,255,0.10)'
                : '#fff',
            color:
              searchMode === 'ai'
                ? '#6b5ce7'
                : '#777',
            padding: '8px 14px',
            borderRadius: '10px',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '12px',
          }}
        >
          ✦ AI Semantic Search
        </button>

      </div>

      {/* ================================
          CONTENT
      ================================= */}

      {loading ? (

        <div className="knowledge-loading">

          <div className="loading-icon">
            ✦
          </div>

          <p>
            Loading your knowledge...
          </p>

        </div>

      ) : displayedKnowledge.length === 0 ? (

        <div className="knowledge-empty">

          <div className="empty-icon">
            ✦
          </div>

          <h2>
            {searchMode === 'ai'
              ? 'No relevant knowledge found'
              : 'No knowledge found'}
          </h2>

          <p>
            {searchMode === 'ai'
              ? 'Try asking your knowledge vault about another topic.'
              : 'Try searching for another project, note or topic.'}
          </p>

        </div>

      ) : (

        <div className="knowledge-grid">

          {displayedKnowledge.map(
            (item) => (

              <div
                className="knowledge-card"
                key={item.id}
              >

                <div className="knowledge-card-top">

                  <div className="knowledge-icon">
                    {getCategoryIcon(
                      item.category
                    )}
                  </div>

                  <span className="knowledge-category">
                    {item.category ||
                      'knowledge'}
                  </span>

                </div>

                <h2>
                  {item.title}
                </h2>

                <p className="knowledge-content">
                  {item.content}
                </p>

                {/* AI MATCH SCORE */}

                {searchMode === 'ai' &&
                  item.similarity !==
                    undefined && (

                    <div
                      style={{
                        marginTop: '12px',
                        padding: '9px 11px',
                        borderRadius: '10px',
                        background:
                          'rgba(124,92,255,0.06)',
                        fontSize: '11px',
                        color: '#6b5ce7',
                        fontWeight: '600',
                      }}
                    >
                      ✦{' '}
                      {Math.round(
                        item.similarity * 100
                      )}
                      % semantic match
                    </div>
                  )}

                <div className="knowledge-card-footer">

                  <span>
                    {item.source ||
                      'Personal'}
                  </span>

                  <div className="knowledge-footer-right">

                    <span>
                      #{item.id}
                    </span>

                    <button
                      className="delete-knowledge-button"
                      onClick={() =>
                        handleDelete(item.id)
                      }
                      disabled={
                        deletingId === item.id
                      }
                      title="Delete knowledge"
                    >
                      {deletingId === item.id
                        ? '...'
                        : '🗑'}
                    </button>

                  </div>

                </div>

              </div>

            )
          )}

        </div>

      )}

    </div>
  );
}

export default KnowledgeVault;