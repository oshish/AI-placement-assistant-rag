import React, { useState, useEffect } from 'react';
import {
  Search,
  X,
  Copy,
  Check,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Building2,
  Briefcase,
  Calendar,
  Layers,
  RotateCcw,
} from 'lucide-react';
import { api } from '../api/client';
import type { FilterOptions, PaginatedQuestions } from '../types';

interface QuestionLibraryProps {
  filterOptions: FilterOptions | null;
  onAskAI: (prompt: string) => void;
  presetCompany?: string | null;
  presetCategory?: string | null;
}

export const QuestionLibrary: React.FC<QuestionLibraryProps> = ({
  filterOptions,
  onAskAI,
  presetCompany,
  presetCategory,
}) => {
  const [questionsData, setQuestionsData] = useState<PaginatedQuestions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [search, setSearch] = useState('');
  const [selectedCompany, setSelectedCompany] = useState<string>(presetCompany || '');
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [selectedBatch, setSelectedBatch] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>(presetCategory || '');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Sync external presets if they change (e.g. clicking on Analytics chart)
  useEffect(() => {
    if (presetCompany !== undefined && presetCompany !== null) {
      setSelectedCompany(presetCompany);
      setPage(1);
    }
  }, [presetCompany]);

  useEffect(() => {
    if (presetCategory !== undefined && presetCategory !== null) {
      setSelectedCategory(presetCategory);
      setPage(1);
    }
  }, [presetCategory]);

  const fetchQuestions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getQuestions({
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
        company: selectedCompany || undefined,
        role: selectedRole || undefined,
        batch: selectedBatch || undefined,
        category: selectedCategory || undefined,
      });
      setQuestionsData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load questions from database.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestions();
  }, [page, pageSize, selectedCompany, selectedRole, selectedBatch, selectedCategory]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchQuestions();
  };

  const handleClearFilters = () => {
    setSearch('');
    setSelectedCompany('');
    setSelectedRole('');
    setSelectedBatch('');
    setSelectedCategory('');
    setPage(1);
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const hasAnyFilter = Boolean(
    search.trim() || selectedCompany || selectedRole || selectedBatch || selectedCategory
  );

  const startRecord = questionsData ? (questionsData.page - 1) * questionsData.page_size + 1 : 0;
  const endRecord = questionsData
    ? Math.min(questionsData.page * questionsData.page_size, questionsData.total)
    : 0;

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '1.5rem' }}>
      {/* Page Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={24} color="#6366f1" />
          Question Library
        </h1>
        <p style={{ fontSize: '0.88rem', color: '#94a3b8' }}>
          Complete index of 9,302 placement questions across 212 companies with exact keyword and faceted search
        </p>
      </div>

      {/* Search and Filters Bar */}
      <div style={{
        background: '#131b26',
        border: '1px solid #1e293b',
        borderRadius: '12px',
        padding: '1.25rem',
        marginBottom: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}>
        {/* Search Input Form */}
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{
            flex: 1,
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            minWidth: '280px',
          }}>
            <Search size={18} color="#64748b" style={{ position: 'absolute', left: '12px' }} />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by keywords (e.g. HashMap, Two Sum, SQL, Binary Tree, Threading, OOP)..."
              style={{
                width: '100%',
                padding: '10px 38px 10px 38px',
                fontSize: '0.92rem',
                borderRadius: '8px',
              }}
            />
            {search && (
              <button
                type="button"
                onClick={() => { setSearch(''); setPage(1); }}
                style={{
                  position: 'absolute',
                  right: '10px',
                  background: 'transparent',
                  border: 'none',
                  color: '#94a3b8',
                }}
              >
                <X size={16} />
              </button>
            )}
          </div>

          <button
            type="submit"
            style={{
              padding: '10px 20px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
              color: '#ffffff',
              border: 'none',
              fontWeight: 600,
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Search size={16} />
            <span>Search</span>
          </button>

          {hasAnyFilter && (
            <button
              type="button"
              onClick={handleClearFilters}
              style={{
                padding: '10px 16px',
                borderRadius: '8px',
                background: '#1e293b',
                color: '#cbd5e1',
                border: '1px solid #334155',
                fontSize: '0.88rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <RotateCcw size={15} />
              <span>Reset</span>
            </button>
          )}
        </form>

        {/* Dropdowns Row */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '0.75rem',
        }}>
          {/* Company Filter */}
          <div>
            <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>
              Company
            </label>
            <select
              value={selectedCompany}
              onChange={(e) => { setSelectedCompany(e.target.value); setPage(1); }}
              style={{ width: '100%', padding: '7px 10px', fontSize: '0.85rem' }}
            >
              <option value="">All Companies (212)</option>
              {filterOptions?.companies.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Role Filter */}
          <div>
            <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>
              Role
            </label>
            <select
              value={selectedRole}
              onChange={(e) => { setSelectedRole(e.target.value); setPage(1); }}
              style={{ width: '100%', padding: '7px 10px', fontSize: '0.85rem' }}
            >
              <option value="">All Roles</option>
              {filterOptions?.roles.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          {/* Batch Filter */}
          <div>
            <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>
              Batch
            </label>
            <select
              value={selectedBatch}
              onChange={(e) => { setSelectedBatch(e.target.value); setPage(1); }}
              style={{ width: '100%', padding: '7px 10px', fontSize: '0.85rem' }}
            >
              <option value="">All Batches</option>
              {filterOptions?.batches.map((b) => (
                <option key={b} value={b}>Batch {b}</option>
              ))}
            </select>
          </div>

          {/* Category Filter */}
          <div>
            <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => { setSelectedCategory(e.target.value); setPage(1); }}
              style={{ width: '100%', padding: '7px 10px', fontSize: '0.85rem' }}
            >
              <option value="">All Categories</option>
              {filterOptions?.categories.map((cat) => (
                <option key={cat} value={cat}>{cat.replace('_', ' ').toUpperCase()}</option>
              ))}
            </select>
          </div>

          {/* Page Size */}
          <div>
            <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>
              Page Size
            </label>
            <select
              value={pageSize}
              onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
              style={{ width: '100%', padding: '7px 10px', fontSize: '0.85rem' }}
            >
              <option value={20}>20 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
            </select>
          </div>
        </div>
      </div>

      {/* Result Status Banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '1rem',
        flexWrap: 'wrap',
        gap: '0.5rem',
      }}>
        <div style={{ fontSize: '0.9rem', color: '#cbd5e1' }}>
          {loading ? (
            <span style={{ color: '#94a3b8' }}>Loading questions...</span>
          ) : questionsData ? (
            <span>
              Showing <strong style={{ color: '#ffffff' }}>{questionsData.total > 0 ? `${startRecord}–${endRecord}` : 0}</strong> of{' '}
              <strong style={{ color: '#38bdf8' }}>{questionsData.total.toLocaleString()}</strong> questions
              {selectedCompany && ` for ${selectedCompany}`}
              {search && ` matching "${search}"`}
            </span>
          ) : null}
        </div>

        {/* Quick Filter Pills */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {selectedCompany && (
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 8px',
              borderRadius: '12px',
              background: '#1e293b',
              fontSize: '0.75rem',
              color: '#38bdf8',
            }}>
              {selectedCompany}
              <X size={12} style={{ cursor: 'pointer' }} onClick={() => setSelectedCompany('')} />
            </span>
          )}
          {selectedCategory && (
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 8px',
              borderRadius: '12px',
              background: '#1e293b',
              fontSize: '0.75rem',
              color: '#fbbf24',
            }}>
              {selectedCategory}
              <X size={12} style={{ cursor: 'pointer' }} onClick={() => setSelectedCategory('')} />
            </span>
          )}
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div style={{
          padding: '1rem',
          background: 'rgba(244, 63, 94, 0.15)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          borderRadius: '8px',
          color: '#fb7185',
          marginBottom: '1.5rem',
        }}>
          {error}
        </div>
      )}

      {/* Questions List */}
      {loading ? (
        <div style={{
          padding: '3rem',
          textAlign: 'center',
          color: '#94a3b8',
          background: '#131b26',
          borderRadius: '12px',
          border: '1px solid #1e293b',
        }}>
          Fetching questions from database...
        </div>
      ) : questionsData && questionsData.items.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {questionsData.items.map((q) => {
            const cat = q.metadata.category || 'technical';
            const comp = q.metadata.company_name || 'General';
            const role = q.metadata.role_name || '';
            const batch = q.metadata.batch || '';

            return (
              <div
                key={q.id}
                style={{
                  background: '#131b26',
                  border: '1px solid #1e293b',
                  borderRadius: '12px',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.85rem',
                  transition: 'border-color 0.2s ease',
                }}
              >
                {/* Header: Category Badge & Metadata */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '0.5rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <span className={`badge ${cat.toLowerCase().includes('hr') ? 'badge-hr' : cat.toLowerCase().includes('practice') ? 'badge-practice' : 'badge-tech'}`}>
                      {cat.replace('_', ' ')}
                    </span>

                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontSize: '0.82rem',
                      fontWeight: 700,
                      color: '#ffffff',
                    }}>
                      <Building2 size={14} color="#38bdf8" />
                      {comp}
                    </span>

                    {role && (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '0.8rem',
                        color: '#94a3b8',
                      }}>
                        <Briefcase size={13} />
                        {role}
                      </span>
                    )}

                    {batch && (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '0.78rem',
                        color: '#64748b',
                      }}>
                        <Calendar size={13} />
                        Batch {batch}
                      </span>
                    )}
                  </div>

                  <span style={{ fontSize: '0.72rem', color: '#64748b', fontFamily: 'monospace' }}>
                    {q.id}
                  </span>
                </div>

                {/* Verbatim Question Text */}
                <div style={{
                  fontSize: '0.98rem',
                  color: '#f8fafc',
                  lineHeight: 1.55,
                  padding: '8px 12px',
                  background: '#0e1622',
                  borderRadius: '8px',
                  borderLeft: '3px solid #6366f1',
                }}>
                  {q.text}
                </div>

                {/* Card Actions Footer */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  gap: '0.75rem',
                }}>
                  <button
                    onClick={() => handleCopy(q.text, q.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      padding: '5px 10px',
                      borderRadius: '6px',
                      background: '#1e293b',
                      border: '1px solid #334155',
                      color: '#cbd5e1',
                      fontSize: '0.78rem',
                    }}
                  >
                    {copiedId === q.id ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
                    <span>{copiedId === q.id ? 'Copied' : 'Copy'}</span>
                  </button>

                  <button
                    onClick={() => onAskAI(`Explain how to solve and answer this interview question from ${comp} (${role}): "${q.text}"`)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      padding: '5px 12px',
                      borderRadius: '6px',
                      background: 'rgba(99, 102, 241, 0.15)',
                      border: '1px solid rgba(99, 102, 241, 0.35)',
                      color: '#818cf8',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                    }}
                  >
                    <Sparkles size={13} />
                    <span>Ask AI About This</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div style={{
          padding: '3rem',
          textAlign: 'center',
          background: '#131b26',
          borderRadius: '12px',
          border: '1px solid #1e293b',
        }}>
          <p style={{ color: '#cbd5e1', fontSize: '1.05rem', marginBottom: '0.75rem' }}>
            No questions matched your search or filters.
          </p>
          <button
            onClick={handleClearFilters}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              background: '#4f46e5',
              color: '#ffffff',
              border: 'none',
              fontWeight: 600,
            }}
          >
            Clear All Filters
          </button>
        </div>
      )}

      {/* Pagination Bar */}
      {questionsData && questionsData.total_pages > 1 && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1rem',
          marginTop: '2rem',
          flexWrap: 'wrap',
        }}>
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={!questionsData.has_prev}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '8px 14px',
              borderRadius: '8px',
              background: '#131b26',
              border: '1px solid #1e293b',
              color: '#cbd5e1',
              fontSize: '0.85rem',
            }}
          >
            <ChevronLeft size={16} />
            <span>Previous</span>
          </button>

          <span style={{ fontSize: '0.88rem', color: '#94a3b8' }}>
            Page <strong style={{ color: '#ffffff' }}>{questionsData.page}</strong> of{' '}
            <strong style={{ color: '#ffffff' }}>{questionsData.total_pages}</strong>
          </span>

          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={!questionsData.has_next}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '8px 14px',
              borderRadius: '8px',
              background: '#131b26',
              border: '1px solid #1e293b',
              color: '#cbd5e1',
              fontSize: '0.85rem',
            }}
          >
            <span>Next</span>
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
};
