import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
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
    const { t, i18n } = useTranslation();

    // Generate welcome message based on current language
    const getWelcomeMessage = () => ({
        id: 1,
        role: 'assistant',
        content: `${t('chat.welcome_greeting')}

${t('chat.welcome_intro')}
• 💊 ${t('chat.help_otc')}
• 📋 ${t('chat.help_availability')}
• 🔍 ${t('chat.help_safety')}
• ⏰ ${t('chat.help_refills')}

**${t('chat.before_start')}**
- ${t('chat.question_allergies')}
- ${t('chat.question_medicines')}

${t('chat.how_help')}`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: 'success'
    });

    const [messages, setMessages] = useState([getWelcomeMessage()]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [sessionId] = useState(() => `session_${Date.now()}`);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // Update welcome message when language changes
    useEffect(() => {
        setMessages(prev => {
            if (prev.length === 1 && prev[0].id === 1) {
                return [getWelcomeMessage()];
            }
            return prev;
        });
    }, [i18n.language]);

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
                content: response.response || response.user_message || t('chat.received_message'),
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                status: 'success',
                urgency: response.urgency,
                warnings: response.warnings
            }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                id: Date.now(),
                role: 'assistant',
                content: t('chat.connection_error'),
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
                recognition.lang = i18n.language === 'hi' ? 'hi-IN' :
                    i18n.language === 'mr' ? 'mr-IN' :
                        i18n.language === 'es' ? 'es-ES' :
                            i18n.language === 'fr' ? 'fr-FR' :
                                i18n.language === 'de' ? 'de-DE' : 'en-IN';

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
                        <span className="agent-name">{t('chat.agent_name')}</span>
                        <span className="agent-status">
                            <span className="status-dot green"></span>
                            {t('chat.agent_status')}
                        </span>
                    </div>
                </div>
                <div className="agent-badges">
                    <span className="agent-badge">
                        <Shield size={14} />
                        {t('chat.safety_enabled')}
                    </span>
                    <span className="agent-badge">
                        <Check size={14} />
                        {t('chat.who_compliant')}
                    </span>
                </div>
            </div>

            {/* Message List - Scrollable */}
            <div className="message-list">
                {messages.length === 0 ? (
                    <div className="empty-state">
                        <Bot size={48} />
                        <h3>{t('chat.start_conversation')}</h3>
                        <p>{t('chat.describe_symptoms')}</p>
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
                        title={t('chat.upload_prescription')}
                        aria-label={t('chat.upload_prescription')}
                    >
                        <Upload size={20} />
                    </button>

                    <textarea
                        ref={inputRef}
                        className="chat-input"
                        placeholder={t('chat.input_placeholder')}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={isLoading}
                        rows={1}
                        aria-label={t('chat.input_label')}
                    />

                    <button
                        className={`input-action-btn voice ${isRecording ? 'recording' : ''}`}
                        onClick={toggleRecording}
                        title={isRecording ? t('chat.stop_recording') : t('chat.voice_input')}
                        aria-label={isRecording ? t('chat.stop_recording') : t('chat.voice_input')}
                    >
                        <Mic size={20} />
                    </button>

                    <button
                        className="send-btn"
                        onClick={handleSend}
                        disabled={!input.trim() || isLoading}
                        title={t('chat.send_message')}
                        aria-label={t('chat.send_message')}
                    >
                        <Send size={18} />
                    </button>
                </div>
                <div className="input-hint">
                    {t('chat.input_hint')}
                </div>
            </div>

            {/* Emergency Escalation Button */}
            <button className="emergency-btn" title={t('chat.emergency')}>
                <AlertTriangle size={20} />
            </button>
        </div>
    );
}

export default ChatPanel;

