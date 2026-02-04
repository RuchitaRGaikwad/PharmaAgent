import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, Upload, Bot, User, AlertTriangle, Shield, Check } from 'lucide-react';
import { sendMessage } from '../services/api';

/**
 * ChatPanel - Full-Screen AI Pharmacist Chat Interface
 * 
 * Enterprise-grade chat workspace matching ChatGPT Enterprise design:
 * - Full height/width flex layout
 * - Scrollable message list
 * - Sticky input bar at bottom
 * - Agent status indicator
 * - Typing indicator
 */
function ChatPanel() {
    const [messages, setMessages] = useState([
        {
            id: 1,
            role: 'assistant',
            content: `Hello! 👋 I'm PharmaAgent, your AI Pharmacist assistant.

I'm here to help you with:
• 💊 OTC medicine recommendations for common symptoms
• 📋 Checking medicine availability
• 🔍 Drug safety information
• ⏰ Refill reminders

**Before we start:**
- Do you have any known **allergies** to medications?
- Are you currently taking any **other medicines**?

How can I help you today?`,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            status: 'success'
        }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [sessionId] = useState(() => `session_${Date.now()}`);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // Auto-scroll to latest message
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Focus input on mount
    useEffect(() => {
        inputRef.current?.focus();
    }, []);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = {
            id: Date.now(),
            role: 'user',
            content: input.trim(),
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await sendMessage(input.trim(), sessionId, 1);

            setMessages(prev => [...prev, {
                id: Date.now(),
                role: 'assistant',
                content: response.response || response.user_message || 'I received your message.',
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                status: 'success',
                urgency: response.urgency,
                warnings: response.warnings
            }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                id: Date.now(),
                role: 'assistant',
                content: 'I apologize, but I encountered a connection error. Please ensure the backend is running and try again.',
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                status: 'error'
            }]);
        } finally {
            setIsLoading(false);
            inputRef.current?.focus();
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const toggleRecording = () => {
        if (!isRecording) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognition) {
                const recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-IN';

                recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    setInput(transcript);
                    setIsRecording(false);
                };

                recognition.onerror = () => setIsRecording(false);
                recognition.onend = () => setIsRecording(false);

                recognition.start();
                setIsRecording(true);
            }
        } else {
            setIsRecording(false);
        }
    };

    const getAvatarIcon = (role, status) => {
        if (role === 'user') return <User size={18} />;
        if (status === 'error') return <AlertTriangle size={18} />;
        return <Bot size={18} />;
    };

    return (
        <div className="chat-panel">
            {/* Agent Status Bar */}
            <div className="agent-status-bar">
                <div className="agent-info">
                    <div className="agent-avatar">
                        <Bot size={20} />
                    </div>
                    <div className="agent-details">
                        <span className="agent-name">AI Pharmacist</span>
                        <span className="agent-status">
                            <span className="status-dot green"></span>
                            Online • Verified
                        </span>
                    </div>
                </div>
                <div className="agent-badges">
                    <span className="agent-badge">
                        <Shield size={14} />
                        Safety Enabled
                    </span>
                    <span className="agent-badge">
                        <Check size={14} />
                        WHO Compliant
                    </span>
                </div>
            </div>

            {/* Message List - Scrollable */}
            <div className="message-list">
                {messages.length === 0 ? (
                    <div className="empty-state">
                        <Bot size={48} />
                        <h3>Start a conversation</h3>
                        <p>Describe your symptoms or ask about medicines</p>
                    </div>
                ) : (
                    messages.map((msg) => (
                        <div key={msg.id} className={`message ${msg.role} ${msg.status === 'error' ? 'error' : ''}`}>
                            <div className="message-avatar">
                                {getAvatarIcon(msg.role, msg.status)}
                            </div>
                            <div className="message-body">
                                <div className="message-content">{msg.content}</div>
                                {msg.warnings && msg.warnings.length > 0 && (
                                    <div className="message-warnings">
                                        {msg.warnings.map((w, i) => (
                                            <span key={i} className="warning-tag">{w}</span>
                                        ))}
                                    </div>
                                )}
                                <div className="message-time">{msg.time}</div>
                            </div>
                        </div>
                    ))
                )}

                {/* Typing Indicator */}
                {isLoading && (
                    <div className="message assistant">
                        <div className="message-avatar">
                            <Bot size={18} />
                        </div>
                        <div className="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Bar - Sticky Bottom */}
            <div className="chat-input-bar">
                <div className="input-wrapper">
                    <button
                        className="input-action-btn"
                        title="Upload prescription"
                        aria-label="Upload prescription"
                    >
                        <Upload size={20} />
                    </button>

                    <textarea
                        ref={inputRef}
                        className="chat-input"
                        placeholder="Type your message or describe symptoms..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={isLoading}
                        rows={1}
                        aria-label="Chat message input"
                    />

                    <button
                        className={`input-action-btn voice ${isRecording ? 'recording' : ''}`}
                        onClick={toggleRecording}
                        title={isRecording ? 'Stop recording' : 'Voice input'}
                        aria-label={isRecording ? 'Stop recording' : 'Voice input'}
                    >
                        <Mic size={20} />
                    </button>

                    <button
                        className="send-btn"
                        onClick={handleSend}
                        disabled={!input.trim() || isLoading}
                        title="Send message"
                        aria-label="Send message"
                    >
                        <Send size={18} />
                    </button>
                </div>
                <div className="input-hint">
                    Press Enter to send • AI responses may take a moment
                </div>
            </div>

            {/* Emergency Escalation Button */}
            <button className="emergency-btn" title="Emergency Escalation">
                <AlertTriangle size={20} />
            </button>
        </div>
    );
}

export default ChatPanel;
