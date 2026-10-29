import React, { useState, useEffect } from 'react';
import { Navbar, type ActiveTab } from './components/Navbar';
import { AIAssistant } from './components/AIAssistant';
import { QuestionLibrary } from './components/QuestionLibrary';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import { api } from './api/client';
import type { FilterOptions, HealthStatus, QuestionItem } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('assistant');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);

  // Cross-page state for intuitive user flow
  const [presetCompany, setPresetCompany] = useState<string | null>(null);
  const [presetCategory, setPresetCategory] = useState<string | null>(null);
  const [chatPrompt, setChatPrompt] = useState<string | undefined>(undefined);

  const fetchHealth = async () => {
    setHealthLoading(true);
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch (err) {
      console.warn('Backend health check error:', err);
    } finally {
      setHealthLoading(false);
    }
  };

  const fetchFilters = async () => {
    try {
      const filters = await api.getFilters();
      setFilterOptions(filters);
    } catch (err) {
      console.warn('Backend filters fetch error:', err);
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchFilters();
  }, []);

  // Handlers for cross-page navigation
  const handleSelectCompanyFromAnalytics = (company: string) => {
    setPresetCompany(company);
    setPresetCategory(null);
    setActiveTab('library');
  };

  const handleSelectCategoryFromAnalytics = (category: string) => {
    setPresetCategory(category);
    setPresetCompany(null);
    setActiveTab('library');
  };

  const handleAskAI = (promptText: string) => {
    setChatPrompt(promptText);
    setActiveTab('assistant');
  };

  const handleJumpToLibraryWithQuestion = (q: QuestionItem) => {
    if (q.metadata.company_name) {
      setPresetCompany(q.metadata.company_name);
    }
    setActiveTab('library');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#0b0f17' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        healthLoading={healthLoading}
        onRefreshHealth={fetchHealth}
      />

      <main style={{ flex: 1 }}>
        {activeTab === 'assistant' && (
          <AIAssistant
            filterOptions={filterOptions}
            initialPrompt={chatPrompt}
            onJumpToLibraryWithQuestion={handleJumpToLibraryWithQuestion}
          />
        )}

        {activeTab === 'library' && (
          <QuestionLibrary
            filterOptions={filterOptions}
            presetCompany={presetCompany}
            presetCategory={presetCategory}
            onAskAI={handleAskAI}
          />
        )}

        {activeTab === 'analytics' && (
          <AnalyticsDashboard
            onSelectCompany={handleSelectCompanyFromAnalytics}
            onSelectCategory={handleSelectCategoryFromAnalytics}
            onAskAIWithTopic={handleAskAI}
          />
        )}
      </main>

      <footer style={{
        borderTop: '1px solid #1e293b',
        padding: '1rem 1.5rem',
        textAlign: 'center',
        fontSize: '0.78rem',
        color: '#64748b',
        backgroundColor: '#090d14',
      }}>
        <div style={{ maxWidth: '1440px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <span>
            <strong>Your AI Placement Assistant</strong> • UCS503P College Capstone RAG Application
          </span>
          <span>
            9,302 Questions • 212 Companies • ChromaDB Vector Store • Sentence-Transformers • Google Gemini
          </span>
        </div>
      </footer>
    </div>
  );
};

export default App;
