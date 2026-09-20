import { Activity, Moon, Sun, Server, Database, Sparkles, Brain } from 'lucide-react';
import type { DashboardStats } from '../types';

interface HeaderProps {
  stats: DashboardStats | null;
  darkMode: boolean;
  onToggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({ stats, darkMode, onToggleTheme }) => {
  const cloud = stats?.cloud_services;

  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-icon-box">
          <Activity size={24} />
        </div>
        <div>
          <div className="brand-title">MedFront AI Health Clinic</div>
          <div className="brand-sub">Enterprise Azure Voice AI & Clinical Ambient Intelligence</div>
        </div>
      </div>

      <div className="header-status-pills">
        <div className={`status-pill ${cloud?.cosmos_db === 'CONNECTED' ? 'connected' : 'warning'}`}>
          <Database size={13} />
          <span>Cosmos DB: {cloud?.cosmos_db || 'CHECKING'}</span>
        </div>

        <div className={`status-pill ${cloud?.azure_openai === 'CONNECTED' ? 'connected' : 'warning'}`}>
          <Brain size={13} />
          <span>OpenAI: {cloud?.azure_openai || 'OFFLINE'}</span>
        </div>

        <div className={`status-pill ${cloud?.rag_mode ? 'connected' : 'warning'}`}>
          <Sparkles size={13} />
          <span>RAG: {cloud?.rag_mode || 'LOCAL_CACHE'}</span>
        </div>

        <div className="status-pill">
          <Server size={13} />
          <span>Active Clinicians: {stats?.active_doctors ?? '--'}</span>
        </div>

        <button
          className="theme-toggle-btn"
          onClick={onToggleTheme}
          title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          aria-label="Toggle theme"
        >
          {darkMode ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  );
};
