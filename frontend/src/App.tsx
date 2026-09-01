import React, { useState } from 'react';
import { ProjectPanel } from './components/ProjectPanel';
import { ViewerPanel } from './components/ViewerPanel';
import { InfoPanel } from './components/InfoPanel';
import { StatusBar } from './components/StatusBar';
import type { Project } from './types';
import './App.css';

function App() {
  const [project, setProject] = useState<Project | null>(null);

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand-lockup">
          <div className="brand-mark"><span>◇</span></div>
          <div>
            <div className="brand-name">DepthWizard</div>
            <div className="brand-tagline">Single-view elevation reconstruction</div>
          </div>
        </div>
        <div className="header-meta">
          <span className="header-status"><i /> LOCAL ENGINE</span>
          <span className="header-version">v0.1.0</span>
        </div>
      </header>

      <main className="app-main">
        <aside className="panel panel-left"><ProjectPanel project={project} onProjectChange={setProject} /></aside>
        <section className="panel panel-center"><ViewerPanel project={project} /></section>
        <aside className="panel panel-right"><InfoPanel project={project} /></aside>
      </main>

      <footer className="app-status"><StatusBar project={project} /></footer>
    </div>
  );
}

export default App;
