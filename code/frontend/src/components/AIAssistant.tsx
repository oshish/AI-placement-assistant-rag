import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Filter,
  Check,
  Copy,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Trash2,
  AlertCircle,
} from 'lucide-react';
import { api } from '../api/client';
import type { ChatFilter, ChatMessage, FilterOptions, QuestionItem } from '../types';

interface AIAssistantProps {
  filterOptions: FilterOptions | null;
  onJumpToLibraryWithQuestion?: (question: QuestionItem) => void;
  initialPrompt?: string;
}

export const AIAssistant: React.FC<AIAssistantProps> = ({
  filterOptions,
  onJumpToLibraryWithQuestion,
  initialPrompt,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        '👋 Welcome to **Your AI Placement Assistant**!\n\nI am grounded exclusively on **9,302 real interview questions** from campus placement drives across **212 companies**. You can ask about:\n\n- Specific company question trends (e.g. *American Express, Deloitte, IBM*)\n- Data structures & algorithm questions (e.g. *HashMaps, Binary Trees, Dynamic Programming*)\n- Core CS fundamentals (*SQL, DBMS, OOP, Operating Systems*)\n- HR and behavioral round strategies\n\nPick a starter prompt below or enter your own query!',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [activeFilters, setActiveFilters] = useState<ChatFilter>({});
  const [topK, setTopK] = useState(5);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const starterPrompts = [
    'What are the most common SQL and Python questions asked at American Express?',
    'Explain how to solve the HashMap and Array questions reported for SDE roles.',
    'What behavioral and HR questions are commonly asked in final interview rounds?',
    'Give me a breakdown of technical questions asked by Deloitte.',
  ];

  useEffect(() => {
    if (initialPrompt && initialPrompt.trim()) {
      handleSend(initialPrompt);
    }
  }, [initialPrompt]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleSourceExpand = (id: string) => {
    setExpandedSources((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleSend = async (queryToSend?: string) => {
    const text = (queryToSend !== undefined ? queryToSend : inputQuery).trim();
    if (!text || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (queryToSend === undefined) {
      setInputQuery('');
    }
    setIsLoading(true);

    try {
      const historyPayload = messages
        .filter((m) => m.id !== 'welcome')
        .slice(-6)
        .map((m) => ({ role: m.role, content: m.content }));

      const response = await api.sendChatMessage({
        query: text,
        filters: activeFilters,
        history: historyPayload,
        top_k: topK,
      });

      const assistantMessage: ChatMessage = {
        id: `assistant_${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        mode: response.mode,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **Unable to complete request:** ${err.message || 'Unknown network error'}\n\nPlease ensure the backend FastAPI service is running on port 8000.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: 'welcome_cleared',
        role: 'assistant',
        content: 'Chat cleared. What placement topic would you like to explore next?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  const hasActiveFilters = Boolean(
    activeFilters.company_name || activeFilters.role_name || activeFilters.category || activeFilters.batch
  );

  return (
    <div style={{
      maxWidth: '1200px',
      margin: '0 auto',
      padding: '1.5rem',
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(100vh - 80px)',
    }}>
      {/* Top Controls Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '1rem',
        flexWrap: 'wrap',
        gap: '0.75rem',
      }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={22} color="#38bdf8" />
            AI Placement Assistant
          </h1>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Semantic search + LLM generation grounded on real campus drive questions
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Filter Toggle Button */}
          <button
            onClick={() => setFiltersOpen(!filtersOpen)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '8px',
              fontSize: '0.82rem',
              fontWeight: 600,
              background: hasActiveFilters ? 'rgba(56, 189, 248, 0.15)' : '#131b26',
              border: `1px solid ${hasActiveFilters ? '#38bdf8' : '#1e293b'}`,
              color: hasActiveFilters ? '#38bdf8' : '#cbd5e1',
            }}
          >
            <Filter size={14} />
            <span>Target Filters {hasActiveFilters ? '(Active)' : ''}</span>
            {filtersOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>

          {/* Clear Chat Button */}
          <button
            onClick={handleClearChat}
            title="Reset conversation"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '8px',
              fontSize: '0.82rem',
              fontWeight: 600,
              background: '#131b26',
              border: '1px solid #1e293b',
              color: '#94a3b8',
            }}
          >
            <Trash2 size={14} />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Filter Drawer / Accordion */}
      {filtersOpen && (
        <div style={{
          background: '#131b26',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          padding: '1rem',
          marginBottom: '1rem',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '0.85rem',
        }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: '4px' }}>
              Company
            </label>
            <select
              value={activeFilters.company_name || ''}
              onChange={(e) => setActiveFilters({ ...activeFilters, company_name: e.target.value || undefined })}
              style={{ width: '100%', padding: '6px 10px', fontSize: '0.85rem' }}
            >
              <option value="">All Companies (212)</option>
              {filterOptions?.companies.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: '4px' }}>
              Role
            </label>
            <select
              value={activeFilters.role_name || ''}
              onChange={(e) => setActiveFilters({ ...activeFilters, role_name: e.target.value || undefined })}
              style={{ width: '100%', padding: '6px 10px', fontSize: '0.85rem' }}
            >
              <option value="">All Roles</option>
              {filterOptions?.roles.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: '4px' }}>
              Category
            </label>
            <select
              value={activeFilters.category || ''}
              onChange={(e) => setActiveFilters({ ...activeFilters, category: e.target.value || undefined })}
              style={{ width: '100%', padding: '6px 10px', fontSize: '0.85rem' }}
            >
              <option value="">All Categories</option>
              {filterOptions?.categories.map((cat) => (
                <option key={cat} value={cat}>{cat.replace('_', ' ').toUpperCase()}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: '4px' }}>
              Evidence Sources Count (Top K: {topK})
            </label>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              style={{ width: '100%', padding: '6px 10px', fontSize: '0.85rem' }}
            >
              <option value={3}>3 Questions</option>
              <option value={5}>5 Questions (Default)</option>
              <option value={8}>8 Questions</option>
              <option value={10}>10 Questions</option>
            </select>
          </div>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        paddingRight: '0.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
      }}>
        {messages.map((message) => {
          const isUser = message.role === 'user';
          return (
            <div
              key={message.id}
              style={{
                display: 'flex',
                gap: '0.85rem',
                alignItems: 'flex-start',
                flexDirection: isUser ? 'row-reverse' : 'row',
              }}
            >
              {/* Avatar */}
              <div style={{
                width: '34px',
                height: '34px',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                background: isUser ? 'linear-gradient(135deg, #0284c7, #38bdf8)' : 'linear-gradient(135deg, #4f46e5, #6366f1)',
              }}>
                {isUser ? <User size={18} color="#ffffff" /> : <Bot size={18} color="#ffffff" />}
              </div>

              {/* Message Content Container */}
              <div style={{
                maxWidth: '82%',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem',
              }}>
                {/* Bubble */}
                <div style={{
                  padding: '1rem 1.25rem',
                  borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                  background: isUser ? '#1e293b' : '#131b26',
                  border: `1px solid ${isUser ? '#334155' : '#1e293b'}`,
                  color: '#f8fafc',
                }}>
                  {/* Mode Banner if fallback */}
                  {message.mode === 'fallback' && (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      background: 'rgba(245, 158, 11, 0.1)',
                      border: '1px solid rgba(245, 158, 11, 0.25)',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      marginBottom: '0.85rem',
                      fontSize: '0.82rem',
                      color: '#fbbf24',
                    }}>
                      <AlertCircle size={16} />
                      <div>
                        <strong>Local RAG Mode:</strong> Gemini API Key not yet set in <code>.env</code>. The system retrieved verbatim questions below from your ChromaDB index.
                      </div>
                    </div>
                  )}

                  <div className="markdown-body" style={{ whiteSpace: 'pre-wrap' }}>
                    {message.content}
                  </div>

                  <div style={{
                    fontSize: '0.7rem',
                    color: '#64748b',
                    marginTop: '0.5rem',
                    textAlign: isUser ? 'right' : 'left',
                  }}>
                    {message.timestamp}
                  </div>
                </div>

                {/* Grounded Source Attributions */}
                {message.sources && message.sources.length > 0 && (
                  <div style={{
                    background: '#0e1622',
                    border: '1px solid #1e293b',
                    borderRadius: '10px',
                    padding: '0.75rem 1rem',
                  }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '0.5rem',
                    }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Retrieved Context ({message.sources.length} Questions)
                      </span>
                      <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
                        Click pill to inspect exact verbatim question
                      </span>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {message.sources.map((src, idx) => {
                        const isExpanded = Boolean(expandedSources[src.id]);
                        const comp = src.metadata.company_name || 'General';
                        const role = src.metadata.role_name || '';
                        const cat = src.metadata.category || 'Technical';
                        const score = src.similarity_score !== undefined ? Math.round(src.similarity_score * 100) : null;

                        return (
                          <div
                            key={src.id || idx}
                            style={{
                              background: '#131b26',
                              border: '1px solid #1e293b',
                              borderRadius: '8px',
                              overflow: 'hidden',
                            }}
                          >
                            <div
                              onClick={() => toggleSourceExpand(src.id)}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                padding: '8px 12px',
                                cursor: 'pointer',
                                fontSize: '0.8rem',
                              }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                <span style={{ fontWeight: 700, color: '#ffffff' }}>
                                  #{idx + 1} {comp}
                                </span>
                                {role && (
                                  <span style={{ color: '#94a3b8' }}>• {role}</span>
                                )}
                                <span className={`badge ${cat.toLowerCase().includes('hr') ? 'badge-hr' : cat.toLowerCase().includes('practice') ? 'badge-practice' : 'badge-tech'}`}>
                                  {cat}
                                </span>
                                {score !== null && (
                                  <span style={{ fontSize: '0.7rem', color: '#38bdf8', fontWeight: 600 }}>
                                    {score}% Match
                                  </span>
                                )}
                              </div>

                              <div style={{ color: '#94a3b8' }}>
                                {isExpanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                              </div>
                            </div>

                            {/* Expanded Source Details */}
                            {isExpanded && (
                              <div style={{
                                padding: '10px 12px',
                                background: '#0a0e16',
                                borderTop: '1px solid #1e293b',
                                fontSize: '0.85rem',
                              }}>
                                <p style={{ color: '#f1f5f9', fontStyle: 'italic', marginBottom: '8px' }}>
                                  "{src.text}"
                                </p>

                                <div style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'space-between',
                                  flexWrap: 'wrap',
                                  gap: '8px',
                                  fontSize: '0.72rem',
                                  color: '#64748b',
                                }}>
                                  <span>ID: <code>{src.id}</code></span>

                                  <div style={{ display: 'flex', gap: '8px' }}>
                                    <button
                                      onClick={() => handleCopy(src.text, src.id)}
                                      style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '4px',
                                        background: 'transparent',
                                        border: '1px solid #1e293b',
                                        borderRadius: '4px',
                                        padding: '2px 8px',
                                        color: '#cbd5e1',
                                        fontSize: '0.72rem',
                                      }}
                                    >
                                      {copiedId === src.id ? <Check size={12} color="#10b981" /> : <Copy size={12} />}
                                      <span>{copiedId === src.id ? 'Copied' : 'Copy Question'}</span>
                                    </button>

                                    {onJumpToLibraryWithQuestion && (
                                      <button
                                        onClick={() => onJumpToLibraryWithQuestion(src)}
                                        style={{
                                          display: 'flex',
                                          alignItems: 'center',
                                          gap: '4px',
                                          background: 'rgba(56, 189, 248, 0.1)',
                                          border: '1px solid rgba(56, 189, 248, 0.25)',
                                          borderRadius: '4px',
                                          padding: '2px 8px',
                                          color: '#38bdf8',
                                          fontSize: '0.72rem',
                                        }}
                                      >
                                        <ExternalLink size={12} />
                                        <span>View in Library</span>
                                      </button>
                                    )}
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading Bubble */}
        {isLoading && (
          <div style={{ display: 'flex', gap: '0.85rem', alignItems: 'center' }}>
            <div style={{
              width: '34px',
              height: '34px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'linear-gradient(135deg, #4f46e5, #6366f1)',
            }}>
              <Bot size={18} color="#ffffff" />
            </div>
            <div style={{
              padding: '0.75rem 1.25rem',
              borderRadius: '4px 16px 16px 16px',
              background: '#131b26',
              border: '1px solid #1e293b',
              color: '#94a3b8',
              fontSize: '0.88rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              <Sparkles size={16} color="#38bdf8" className="animate-spin" />
              <span>Retrieving relevant questions from 9,302 records and synthesizing answer...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Starter Prompts (if chat is fresh) */}
      {messages.length <= 2 && (
        <div style={{ marginTop: '0.75rem', marginBottom: '0.5rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', marginBottom: '6px' }}>
            SUGGESTED EXPLORATIONS:
          </div>
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '6px',
          }}>
            {starterPrompts.map((prompt, i) => (
              <button
                key={i}
                onClick={() => handleSend(prompt)}
                disabled={isLoading}
                style={{
                  background: '#131b26',
                  border: '1px solid #1e293b',
                  borderRadius: '20px',
                  padding: '6px 12px',
                  fontSize: '0.78rem',
                  color: '#cbd5e1',
                  textAlign: 'left',
                }}
              >
                💡 {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Bar */}
      <div style={{
        marginTop: '0.75rem',
        background: '#131b26',
        border: '1px solid #1e293b',
        borderRadius: '12px',
        padding: '8px 12px',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
      }}>
        <textarea
          rows={1}
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Ask anything about placement interview questions, patterns, or company rounds..."
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            color: '#ffffff',
            fontSize: '0.92rem',
            resize: 'none',
            padding: '6px 0',
          }}
        />

        <button
          onClick={() => handleSend()}
          disabled={!inputQuery.trim() || isLoading}
          style={{
            background: inputQuery.trim() && !isLoading ? 'linear-gradient(135deg, #4f46e5, #6366f1)' : '#1e293b',
            border: 'none',
            borderRadius: '8px',
            width: '36px',
            height: '36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ffffff',
            flexShrink: 0,
          }}
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
};
