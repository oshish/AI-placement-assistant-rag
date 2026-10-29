import React, { useState, useEffect } from 'react';
import {
  Building2,
  Layers,
  Award,
  ArrowRight,
  TrendingUp,
  Tag,
  Briefcase,
  Calendar,
} from 'lucide-react';
import { api } from '../api/client';
import type { AnalyticsDashboardData } from '../types';

interface AnalyticsDashboardProps {
  onSelectCompany: (company: string) => void;
  onSelectCategory: (category: string) => void;
  onAskAIWithTopic: (topic: string) => void;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  onSelectCompany,
  onSelectCategory,
  onAskAIWithTopic,
}) => {
  const [data, setData] = useState<AnalyticsDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getAnalyticsDashboard();
        setData(res);
      } catch (err: any) {
        setError(err.message || 'Failed to load analytics dashboard data.');
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
        Synthesizing placement insights across 9,302 dataset records...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '2rem' }}>
        <div style={{
          padding: '1.5rem',
          background: 'rgba(244, 63, 94, 0.15)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          borderRadius: '12px',
          color: '#fb7185',
        }}>
          {error || 'No analytics data available.'}
        </div>
      </div>
    );
  }

  const { overview, topics, companies, categories, batches, experiences } = data;
  const maxTopicCount = topics.length > 0 ? topics[0].count : 1;

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <TrendingUp size={24} color="#38bdf8" />
          Interview Insights & Placement Trends
        </h1>
        <p style={{ fontSize: '0.88rem', color: '#94a3b8' }}>
          Aggregated analytics synthesized from 9,302 questions across 212 visiting campus companies
        </p>
      </div>

      {/* Overview Stat Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '1rem',
      }}>
        {/* Card 1 */}
        <div style={{
          background: '#131b26',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#94a3b8' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase' }}>Total Questions</span>
            <Layers size={18} color="#6366f1" />
          </div>
          <span style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff' }}>
            {overview.total_questions.toLocaleString()}
          </span>
          <span style={{ fontSize: '0.75rem', color: '#38bdf8' }}>
            Across 317 company-role drives
          </span>
        </div>

        {/* Card 2 */}
        <div style={{
          background: '#131b26',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#94a3b8' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase' }}>Hiring Companies</span>
            <Building2 size={18} color="#38bdf8" />
          </div>
          <span style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff' }}>
            {overview.total_companies}
          </span>
          <span style={{ fontSize: '0.75rem', color: '#10b981' }}>
            Top tier MNCs & Startups
          </span>
        </div>

        {/* Card 3 */}
        <div style={{
          background: '#131b26',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#94a3b8' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase' }}>Job Roles</span>
            <Briefcase size={18} color="#fbbf24" />
          </div>
          <span style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff' }}>
            {overview.total_roles}
          </span>
          <span style={{ fontSize: '0.75rem', color: '#fbbf24' }}>
            SDE, Data Analyst, ML & Backend
          </span>
        </div>

        {/* Card 4 */}
        <div style={{
          background: '#131b26',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#94a3b8' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase' }}>Candidate Insights</span>
            <Award size={18} color="#10b981" />
          </div>
          <span style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff' }}>
            {experiences.total}
          </span>
          <span style={{ fontSize: '0.75rem', color: '#10b981' }}>
            100% Verified Campus Offers
          </span>
        </div>
      </div>

      {/* Grid: Topics Frequency & Category Breakdown */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))',
        gap: '1.5rem',
      }}>
        {/* High Frequency Topics */}
        <div style={{
          background: '#131b26',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          padding: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Tag size={18} color="#6366f1" />
              High-Frequency Interview Topics
            </h2>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              Click to ask AI
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {topics.slice(0, 10).map((t) => {
              const pct = Math.round((t.count / maxTopicCount) * 100);
              return (
                <div
                  key={t.topic}
                  onClick={() => onAskAIWithTopic(`Provide a comprehensive placement preparation guide for '${t.topic}', including common interview questions and key concepts.`)}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                    cursor: 'pointer',
                    padding: '6px 8px',
                    borderRadius: '8px',
                    transition: 'background 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#172231')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                    <span style={{ fontWeight: 600, color: '#f8fafc' }}>{t.topic}</span>
                    <span style={{ color: '#38bdf8', fontWeight: 700 }}>{t.count} drives</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: '#0e1622', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{
                      width: `${pct}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #4f46e5 0%, #38bdf8 100%)',
                      borderRadius: '4px',
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Category Split and Batch Breakdown */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '1.5rem',
        }}>
          {/* Category Distribution */}
          <div style={{
            background: '#131b26',
            border: '1px solid #1e293b',
            borderRadius: '12px',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} color="#10b981" />
              Question Category Breakdown
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {categories.map((c) => (
                <div
                  key={c.category}
                  onClick={() => onSelectCategory(c.category)}
                  style={{
                    cursor: 'pointer',
                    padding: '8px 12px',
                    background: '#0e1622',
                    borderRadius: '8px',
                    border: '1px solid #1e293b',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className={`badge ${c.category.includes('hr') ? 'badge-hr' : c.category.includes('practice') ? 'badge-practice' : 'badge-tech'}`}>
                      {c.category.replace('_', ' ')}
                    </span>
                    <span style={{ fontSize: '0.88rem', color: '#f8fafc', fontWeight: 600 }}>
                      {c.count.toLocaleString()} Questions
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#38bdf8' }}>
                      {c.percentage}%
                    </span>
                    <ArrowRight size={14} color="#64748b" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Batch Distribution */}
          <div style={{
            background: '#131b26',
            border: '1px solid #1e293b',
            borderRadius: '12px',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Calendar size={18} color="#fbbf24" />
              Target Batch Volume
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: '0.75rem' }}>
              {batches.map((b) => (
                <div
                  key={b.batch}
                  style={{
                    padding: '12px',
                    background: '#0e1622',
                    borderRadius: '8px',
                    border: '1px solid #1e293b',
                    textAlign: 'center',
                  }}
                >
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Batch {b.batch}</span>
                  <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff' }}>
                    {b.question_count.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Top Recruiting Companies Leaderboard */}
      <div style={{
        background: '#131b26',
        border: '1px solid #1e293b',
        borderRadius: '12px',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Building2 size={18} color="#38bdf8" />
              Top Hiring Companies by Question Volume
            </h2>
            <p style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
              Click any company to inspect its complete question set in the Question Library
            </p>
          </div>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '0.85rem',
        }}>
          {companies.slice(0, 12).map((comp, idx) => (
            <div
              key={comp.company_name}
              onClick={() => onSelectCompany(comp.company_name)}
              style={{
                background: '#0e1622',
                border: '1px solid #1e293b',
                borderRadius: '10px',
                padding: '12px 14px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                transition: 'border-color 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = '#38bdf8')}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = '#1e293b')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  color: '#64748b',
                  width: '20px',
                }}>
                  #{idx + 1}
                </span>
                <div>
                  <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#f8fafc' }}>
                    {comp.company_name}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                    {comp.role_count} distinct role{comp.role_count > 1 ? 's' : ''}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  color: '#38bdf8',
                  background: 'rgba(56, 189, 248, 0.1)',
                  padding: '3px 8px',
                  borderRadius: '6px',
                }}>
                  {comp.question_count} Qs
                </span>
                <ArrowRight size={14} color="#64748b" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Senior Interview Experiences Tips */}
      {experiences.sample_tips && experiences.sample_tips.length > 0 && (
        <div style={{
          background: '#131b26',
          border: '1px solid #1e293b',
          borderRadius: '12px',
          padding: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}>
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Award size={18} color="#10b981" />
              Senior Candidate Placement Insights & Advice
            </h2>
            <p style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
              Verified candidate advice from actual campus selection rounds
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '1rem',
          }}>
            {experiences.sample_tips.map((exp, idx) => (
              <div
                key={idx}
                style={{
                  background: '#0e1622',
                  border: '1px solid #1e293b',
                  borderRadius: '10px',
                  padding: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Building2 size={14} color="#38bdf8" />
                    <span style={{ fontWeight: 700, fontSize: '0.88rem', color: '#ffffff' }}>
                      {exp.company_name}
                    </span>
                  </div>
                  <span style={{
                    fontSize: '0.7rem',
                    fontWeight: 600,
                    color: '#10b981',
                    background: 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.25)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                  }}>
                    {exp.outcome}
                  </span>
                </div>

                <p style={{ fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.5, fontStyle: 'italic' }}>
                  "{exp.advice}"
                </p>

                <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                  Role: {exp.role_name} • Batch {exp.batch}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
