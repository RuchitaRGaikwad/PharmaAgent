import React, { useState, useEffect, useCallback } from 'react';
import {
    Activity, ExternalLink, RefreshCw, Clock, Bot, Shield, Pill, Brain,
    Search, Filter, ChevronLeft, ChevronRight, BarChart3, Zap
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'https://pharmaagent.onrender.com';

function TracesPanel() {
    const [traces, setTraces] = useState([]);
    const [links, setLinks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('traces');
    const [stats, setStats] = useState(null);
    const [agents, setAgents] = useState([]);

    // Filters
    const [agentFilter, setAgentFilter] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');

    // Pagination
    const [total, setTotal] = useState(0);
    const [offset, setOffset] = useState(0);
    const [limit] = useState(20);

    // Auto-refresh
    const [autoRefresh, setAutoRefresh] = useState(false);

    useEffect(() => {
        loadAgents();
        loadStats();
    }, []);

    useEffect(() => {
        loadTraces();
    }, [agentFilter, searchQuery, dateFrom, dateTo, offset]);

    useEffect(() => {
        let interval;
        if (autoRefresh) {
            interval = setInterval(loadTraces, 5000);
        }
        return () => clearInterval(interval);
    }, [autoRefresh, agentFilter, searchQuery, dateFrom, dateTo, offset]);

    const loadAgents = async () => {
        try {
            const response = await fetch(`${API_BASE}/admin/traces/agents`);
            const data = await response.json();
            setAgents(data.agents || []);
        } catch (error) {
            console.error('Failed to load agents:', error);
        }
    };

    const loadStats = async () => {
        try {
            const response = await fetch(`${API_BASE}/admin/traces/stats`);
            const data = await response.json();
            setStats(data);
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    };

    const loadTraces = useCallback(async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams({
                limit: limit.toString(),
                offset: offset.toString()
            });

            if (agentFilter) params.append('agent_name', agentFilter);
            if (searchQuery) params.append('search', searchQuery);
            if (dateFrom) params.append('date_from', dateFrom);
            if (dateTo) params.append('date_to', dateTo);

            const response = await fetch(`${API_BASE}/admin/traces?${params}`);
            const data = await response.json();
            setTraces(data.agent_traces || []);
            setLinks(data.observability_links || []);
            setTotal(data.total || 0);
        } catch (error) {
            console.error('Failed to load traces:', error);
        } finally {
            setLoading(false);
        }
    }, [agentFilter, searchQuery, dateFrom, dateTo, offset, limit]);

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

    const handleNextPage = () => {
        if (offset + limit < total) {
            setOffset(offset + limit);
        }
    };

    const handlePrevPage = () => {
        if (offset > 0) {
            setOffset(Math.max(0, offset - limit));
        }
    };

    const currentPage = Math.floor(offset / limit) + 1;
    const totalPages = Math.ceil(total / limit);

    return (
        <div className="traces-panel">
            {/* Stats Cards */}
            {stats && (
                <div className="traces-stats-bar">
                    <div className="stat-chip">
                        <BarChart3 size={14} />
                        <span>{stats.total_traces} Total</span>
                    </div>
                    <div className="stat-chip">
                        <Zap size={14} />
                        <span>{stats.recent_24h} Last 24h</span>
                    </div>
                    <div className="stat-chip">
                        <Clock size={14} />
                        <span>{stats.avg_duration_ms}ms Avg</span>
                    </div>
                </div>
            )}

            {/* Tab Navigation & Filters */}
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

                <div className="toolbar-actions">
                    <label className="auto-refresh-toggle">
                        <input
                            type="checkbox"
                            checked={autoRefresh}
                            onChange={(e) => setAutoRefresh(e.target.checked)}
                        />
                        Auto-refresh
                    </label>
                    <button className="btn-secondary" onClick={loadTraces}>
                        <RefreshCw size={16} className={loading ? 'spinning' : ''} />
                        Refresh
                    </button>
                </div>
            </div>

            {/* Filter Bar */}
            {activeTab === 'traces' && (
                <div className="filter-bar">
                    <div className="filter-group">
                        <Filter size={14} />
                        <select
                            value={agentFilter}
                            onChange={(e) => { setAgentFilter(e.target.value); setOffset(0); }}
                            className="filter-select"
                        >
                            <option value="">All Agents</option>
                            {agents.map(agent => (
                                <option key={agent} value={agent}>{agent}</option>
                            ))}
                        </select>
                    </div>

                    <div className="filter-group search">
                        <Search size={14} />
                        <input
                            type="text"
                            placeholder="Search traces..."
                            value={searchQuery}
                            onChange={(e) => { setSearchQuery(e.target.value); setOffset(0); }}
                            className="filter-input"
                        />
                    </div>

                    <div className="filter-group">
                        <input
                            type="date"
                            value={dateFrom}
                            onChange={(e) => { setDateFrom(e.target.value); setOffset(0); }}
                            className="filter-date"
                            placeholder="From"
                        />
                        <span className="date-separator">to</span>
                        <input
                            type="date"
                            value={dateTo}
                            onChange={(e) => { setDateTo(e.target.value); setOffset(0); }}
                            className="filter-date"
                            placeholder="To"
                        />
                    </div>
                </div>
            )}

            {loading ? (
                <div className="loading-state">Loading traces...</div>
            ) : activeTab === 'traces' ? (
                <>
                    <div className="traces-list">
                        {traces.length === 0 ? (
                            <div className="empty-state">
                                <Activity size={48} />
                                <h3>No Traces Found</h3>
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
                                            {trace.action && (
                                                <span className="trace-action">{trace.action}</span>
                                            )}
                                            <span className="trace-duration">
                                                <Clock size={12} />
                                                {trace.duration_ms || 0}ms
                                            </span>
                                        </div>
                                    </div>
                                    <div className="trace-body">
                                        {trace.input && (
                                            <div className="trace-section">
                                                <label>Input</label>
                                                <p>{trace.input}</p>
                                            </div>
                                        )}
                                        {trace.output && (
                                            <div className="trace-section">
                                                <label>Output</label>
                                                <p>{trace.output}</p>
                                            </div>
                                        )}
                                        {trace.decision && (
                                            <div className="trace-section">
                                                <label>Decision</label>
                                                <p className="trace-decision">{trace.decision}</p>
                                            </div>
                                        )}
                                        {trace.reason && (
                                            <div className="trace-section">
                                                <label>Reason</label>
                                                <p>{trace.reason}</p>
                                            </div>
                                        )}
                                    </div>
                                    <div className="trace-footer">
                                        <span className="trace-timestamp">
                                            {trace.timestamp ? new Date(trace.timestamp).toLocaleString() : 'Unknown'}
                                        </span>
                                        {trace.session_id && (
                                            <span className="trace-session">Session: {trace.session_id}</span>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {/* Pagination */}
                    {total > limit && (
                        <div className="pagination-bar">
                            <span className="pagination-info">
                                Showing {offset + 1}-{Math.min(offset + limit, total)} of {total}
                            </span>
                            <div className="pagination-controls">
                                <button
                                    className="pagination-btn"
                                    onClick={handlePrevPage}
                                    disabled={offset === 0}
                                >
                                    <ChevronLeft size={16} />
                                </button>
                                <span className="pagination-page">
                                    Page {currentPage} of {totalPages}
                                </span>
                                <button
                                    className="pagination-btn"
                                    onClick={handleNextPage}
                                    disabled={offset + limit >= total}
                                >
                                    <ChevronRight size={16} />
                                </button>
                            </div>
                        </div>
                    )}
                </>
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
