import { useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const API_URL = 'http://127.0.0.1:8000';

function AIChat() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // =========================
  // SEND MESSAGE
  // =========================

  const sendMessage = async (customMessage = null) => {
    const userMessage = (
      customMessage ?? message
    ).trim();

    if (!userMessage || loading) {
      return;
    }

    const userChat = {
      role: 'user',
      text: userMessage,
    };

    setMessages((prev) => [
      ...prev,
      userChat,
    ]);

    setMessage('');
    setLoading(true);

    try {
      const response = await axios.post(
        `${API_URL}/chat`,
        {
          message: userMessage,
          history: messages,
        }
      );

      console.log(
        'NEXUS API RESPONSE:',
        response.data
      );

      const aiText =
        response.data?.response ||
        response.data?.text ||
        'NEXUS received your message, but no response text was returned.';

      const sources =
        response.data?.sources || [];

      setMessages((prev) => [
        ...prev,
        {
          role: 'ai',
          text: aiText,
          sources: sources,
        },
      ]);

    } catch (error) {

      console.error(
        'NEXUS API ERROR:',
        error
      );

      setMessages((prev) => [
        ...prev,
        {
          role: 'ai',
          text:
            'Sorry, I could not connect to the NEXUS backend.',
          sources: [],
        },
      ]);

    } finally {

      setLoading(false);

    }
  };


  // =========================
  // SUGGESTION
  // =========================

  const sendSuggestion = (text) => {
    sendMessage(text);
  };


  return (
    <div className="ai-workspace">

      {/* ========================= */}
      {/* HEADER */}
      {/* ========================= */}

      <div className="ai-workspace-header">

        <div className="ai-title">

          <div className="ai-avatar-large">
            ✦
          </div>

          <div>

            <span className="ai-label">
              PERSONAL INTELLIGENCE
            </span>

            <h1>
              NEXUS AI
            </h1>

            <p>
              Your personal AI operating system
            </p>

          </div>

        </div>


        <div className="ai-online">

          <span></span>

          Online

        </div>

      </div>


      {/* ========================= */}
      {/* CHAT */}
      {/* ========================= */}

      <div className="ai-chat-container">

        {/* WELCOME */}

        {messages.length === 0 && (

          <div className="ai-welcome">

            <div className="welcome-icon">
              ✦
            </div>

            <h2>
              How can I help you today?
            </h2>

            <p>
              Ask NEXUS about your projects,
              knowledge, tasks, notes or anything
              you're working on.
            </p>


            <div className="suggestions">

              <button
                onClick={() =>
                  sendSuggestion(
                    'Analyze my projects'
                  )
                }
              >
                ✦ Analyze my projects
              </button>


              <button
                onClick={() =>
                  sendSuggestion(
                    'Search my knowledge'
                  )
                }
              >
                ◈ Search my knowledge
              </button>


              <button
                onClick={() =>
                  sendSuggestion(
                    'What should I work on today?'
                  )
                }
              >
                ✓ What should I work on today?
              </button>


              <button
                onClick={() =>
                  sendSuggestion(
                    'Help me write a note'
                  )
                }
              >
                ✎ Help me write a note
              </button>

            </div>

          </div>

        )}


        {/* DEFAULT NEXUS MESSAGE */}

        <div className="ai-message-box">

          <div className="message-avatar">
            ✦
          </div>

          <div className="message-content">

            <strong>
              NEXUS
            </strong>

            <p>
              Hello Sharad 👋 I'm ready to help
              you manage your projects, knowledge,
              tasks and daily workflow.
            </p>

          </div>

        </div>


        {/* CHAT MESSAGES */}

        {messages.map((item, index) => (

          <div
            className="ai-message-box"
            key={`${item.role}-${index}`}
            style={{
              marginTop: '12px',
            }}
          >

            <div className="message-avatar">

              {item.role === 'ai'
                ? '✦'
                : 'S'}

            </div>


            <div className="message-content">

              <strong>

                {item.role === 'ai'
                  ? 'NEXUS'
                  : 'YOU'}

              </strong>


              {item.role === 'ai' ? (

                <>

                  <div className="message-text markdown-content">

                    <ReactMarkdown>
                      {item.text}
                    </ReactMarkdown>

                  </div>


                  {/* ========================= */}
                  {/* RAG SOURCES */}
                  {/* ========================= */}

                  {item.sources &&
                    item.sources.length > 0 && (

                      <div
                        style={{
                          marginTop: '14px',
                          padding: '12px 14px',
                          borderRadius: '14px',
                          background:
                            'rgba(124, 92, 255, 0.06)',
                          border:
                            '1px solid rgba(124, 92, 255, 0.12)',
                        }}
                      >

                        <div
                          style={{
                            fontSize: '12px',
                            fontWeight: '700',
                            color: '#6b5ce7',
                            marginBottom: '8px',
                          }}
                        >
                          📚 KNOWLEDGE SOURCES
                        </div>


                        {item.sources.map(
                          (source, sourceIndex) => (

                            <div
                              key={
                                source.id ||
                                sourceIndex
                              }
                              style={{
                                display: 'flex',
                                alignItems:
                                  'center',
                                gap: '8px',
                                marginTop:
                                  sourceIndex === 0
                                    ? '0'
                                    : '7px',
                                fontSize: '13px',
                                color: '#555',
                              }}
                            >

                              <span>
                                ◈
                              </span>

                              <span>
                                {source.title ||
                                  'Knowledge Item'}
                              </span>

                              {source.similarity !==
                                undefined && (

                                <span
                                  style={{
                                    marginLeft:
                                      'auto',
                                    fontSize:
                                      '11px',
                                    color:
                                      '#8a8a9a',
                                  }}
                                >
                                  {Math.round(
                                    source.similarity *
                                      100
                                  )}
                                  % match
                                </span>

                              )}

                            </div>

                          )
                        )}

                      </div>

                    )}

                </>

              ) : (

                <p>
                  {item.text}
                </p>

              )}

            </div>

          </div>

        ))}


        {/* LOADING */}

        {loading && (

          <div
            className="ai-message-box"
            style={{
              marginTop: '12px',
            }}
          >

            <div className="message-avatar">
              ✦
            </div>

            <div className="message-content">

              <strong>
                NEXUS
              </strong>

              <p>
                Thinking...
              </p>

            </div>

          </div>

        )}

      </div>


      {/* ========================= */}
      {/* INPUT */}
      {/* ========================= */}

      <div className="ai-input-wrapper">

        <div className="input-icon">
          ✦
        </div>


        <input
          type="text"
          placeholder={
            loading
              ? 'NEXUS is thinking...'
              : 'Ask NEXUS anything...'
          }
          value={message}
          disabled={loading}
          onChange={(e) =>
            setMessage(e.target.value)
          }
          onKeyDown={(e) => {

            if (
              e.key === 'Enter' &&
              !e.shiftKey
            ) {
              e.preventDefault();
              sendMessage();
            }

          }}
        />


        <button
          className="send-button"
          onClick={() => sendMessage()}
          disabled={loading}
        >
          {loading ? '...' : '➜'}
        </button>

      </div>


      {/* FOOTER */}

      <div className="ai-footer">
        NEXUS AI can search your knowledge
        and help manage your workspace.
      </div>

    </div>
  );
}

export default AIChat;