import React from 'react';
import { Bot, BookOpen, BarChart3, Database, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';
import type { HealthStatus } from '../types';

export type ActiveTab = 'assistant' | 'library' | 'analytics';

interface NavbarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  health: HealthStatus | null;
  healthLoading: boolean;
  onRefreshHealth: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  health,
  healthLoading,
  onRefreshHealth,
}) => {
  return (
    <header style={{
      backgroundColor: '#0d131d',
      borderBottom: '1px solid #1e293b',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      backdropFilter: 'blur(12px)',
    }}>
      <div style={{
        maxWidth: '1440px',
        margin: '0 auto',
        padding: '0.85rem 1.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
      }}>
        {/* Brand / Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            background: 'linear-gradient(135deg, #6366f1 0%, #38bdf8 100%)',
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)',
          }}>
            <Bot size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em' }}>
                Your AI Placement Assistant
              </span>
              <span style={{
                fontSize: '0.65rem',
                fontWeight: 700,
                color: '#38bdf8',
                background: 'rgba(56, 189, 248, 0.12)',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                padding: '2px 6px',
                borderRadius: '4px',
              }}>
                UCS503P
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              RAG Intelligence for Thapar Placement Interviews
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{
          display: 'flex',
          alignItems: 'center',
          background: '#090d14',
          padding: '4px',
          borderRadius: '12px',
          border: '1px solid #1e293b',
        }}>
          <button
            onClick={() => setActiveTab('assistant')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: 600,
              border: 'none',
              background: activeTab === 'assistant' ? 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)' : 'transparent',
              color: activeTab === 'assistant' ? '#ffffff' : '#94a3b8',
              boxShadow: activeTab === 'assistant' ? '0 2px 8px rgba(79, 70, 229, 0.4)' : 'none',
            }}
          >
            <Bot size={16} />
            <span>AI Assistant</span>
          </button>

          <button
            onClick={() => setActiveTab('library')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: 600,
              border: 'none',
              background: activeTab === 'library' ? 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)' : 'transparent',
              color: activeTab === 'library' ? '#ffffff' : '#94a3b8',
              boxShadow: activeTab === 'library' ? '0 2px 8px rgba(79, 70, 229, 0.4)' : 'none',
            }}
          >
            <BookOpen size={16} />
            <span>Question Library</span>
          </button>

          <button
            onClick={() => setActiveTab('analytics')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: 600,
              border: 'none',
              background: activeTab === 'analytics' ? 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)' : 'transparent',
              color: activeTab === 'analytics' ? '#ffffff' : '#94a3b8',
              boxShadow: activeTab === 'analytics' ? '0 2px 8px rgba(79, 70, 229, 0.4)' : 'none',
            }}
          >
            <BarChart3 size={16} />
            <span>Interview Insights</span>
          </button>
        </nav>

        {/* System Status Indicators */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Vector Store Status */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: '#131b26',
            padding: '5px 12px',
            borderRadius: '20px',
            border: '1px solid #1e293b',
            fontSize: '0.75rem',
            color: '#cbd5e1',
          }}>
            <Database size={13} color="#38bdf8" />
            <span style={{ fontWeight: 600 }}>
              {health?.collection_count ? `${health.collection_count.toLocaleString()} Qs` : '9,302 Qs'}
            </span>
            <span style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: '#10b981',
              display: 'inline-block',
            }} />
          </div>

          {/* Gemini Status */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            background: health?.gemini_configured ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
            border: `1px solid ${health?.gemini_configured ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)'}`,
            padding: '5px 10px',
            borderRadius: '20px',
            fontSize: '0.75rem',
            color: health?.gemini_configured ? '#34d399' : '#fbbf24',
          }}>
            {health?.gemini_configured ? (
              <>
                <CheckCircle2 size={13} />
                <span>Gemini Ready</span>
              </>
            ) : (
              <>
                <AlertTriangle size={13} />
                <span>Local RAG Mode</span>
              </>
            )}
          </div>

          {/* Refresh Button */}
          <button
            onClick={onRefreshHealth}
            title="Refresh connection status"
            disabled={healthLoading}
            style={{
              background: '#131b26',
              border: '1px solid #1e293b',
              color: '#94a3b8',
              borderRadius: '8px',
              padding: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <RefreshCw size={14} className={healthLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>
    </header>
  );
};
