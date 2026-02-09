import React, { useState, useEffect } from 'react';
import { Activity, ExternalLink, RefreshCw, Clock, Bot, Shield, Pill, Brain } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function TracesPanel() {
    const [traces, setTraces] = useState([]);
    const [links, setLinks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('traces');

    useEffect(() => {
        loadTraces();
    }, []);

    const loadTraces = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE}/admin/traces`);
            const data = await response.json();
            setTraces(data.agent_traces || []);
            setLinks(data.observability_links || []);
        } catch (error) {
            console.error('Failed to load traces:', error);
        } finally {
            setLoading(false);
        }
    };

    const getAgentIcon = (agentName) => {
        const name = agentName?.toLowerCase() || '';
        if (name.includes('safety')) return <Shield className="agent-icon safety" />;
        if (name.includes('refill')) return <Pill className="agent-icon refill" />;
        if (name.includes('chat') || name.includes('conversation')) return <Bot className="agent-icon chat" />;
        return <Brain className="agent-icon default" />;
    };

    const getToolIcon = (tool) => {
        return tool === 'langfuse' ? '🔍' : '🔗';
    };

    return (
        <div className="traces-panel">
            {/* Tab Navigation */}
            <div className="panel-toolbar">
                <div className="filter-tabs">
                    <button
                        className={`filter-tab ${activeTab === 'traces' ? 'active' : ''}`}
                        onClick={() => setActiveTab('traces')}
                    >
                        <Activity size={16} />
                        Agent Traces
                    </button>
                    <button
                        className={`filter-tab ${activeTab === 'links' ? 'active' : ''}`}
                        onClick={() => setActiveTab('links')}
                    >
                        <ExternalLink size={16} />
                        Observability Links
                    </button>
                </div>
                <button className="btn-secondary" onClick={loadTraces}>
                    <RefreshCw size={16} />
                    Refresh
                </button>
            </div>

            {loading ? (
                <div className="loading-state">Loading traces...</div>
            ) : activeTab === 'traces' ? (
                <div className="traces-list">
                    {traces.length === 0 ? (
                        <div className="empty-state">
                            <Activity size={48} />
                            <h3>No Traces Yet</h3>
                            <p>Agent traces will appear here as the AI processes requests.</p>
                        </div>
                    ) : (
                        traces.map(trace => (
                            <div key={trace.id} className="trace-card">
                                <div className="trace-header">
                                    {getAgentIcon(trace.agent_name)}
                                    <div className="trace-info">
                                        <span className="trace-agent">{trace.agent_name}</span>
                                        <span className="trace-id">{trace.id}</span>
                                    </div>
                                    <div className="trace-meta">
                                        <span className="trace-confidence">
                                            {(trace.confidence * 100).toFixed(0)}% confidence
                                        </span>
                                        <span className="trace-duration">
                                            <Clock size={12} />
                                            {trace.duration_ms}ms
                                        </span>
                                    </div>
                                </div>
                                <div className="trace-body">
                                    <div className="trace-section">
                                        <label>Input</label>
                                        <p>{trace.input}</p>
                                    </div>
                                    <div className="trace-section">
                                        <label>Output</label>
                                        <p>{trace.output}</p>
                                    </div>
                                    <div className="trace-section">
                                        <label>Decision</label>
                                        <p className="trace-decision">{trace.decision}</p>
                                    </div>
                                </div>
                                <div className="trace-footer">
                                    <span className="trace-timestamp">
                                        {trace.timestamp ? new Date(trace.timestamp).toLocaleString() : 'Unknown'}
                                    </span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            ) : (
                <div className="links-grid">
                    {links.map(link => (
                        <a
                            key={link.id}
                            href={link.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="link-card"
                        >
                            <div className="link-tool">
                                {getToolIcon(link.tool)} {link.tool}
                            </div>
                            <h4 className="link-name">{link.name}</h4>
                            <p className="link-description">{link.description}</p>
                            <div className="link-action">
                                <span>Open Dashboard</span>
                                <ExternalLink size={14} />
                            </div>
                        </a>
                    ))}
                </div>
            )}
        </div>
    );
}

export default TracesPanel;
