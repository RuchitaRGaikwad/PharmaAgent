import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, Upload, Bot, User, X, Check } from 'lucide-react';
import { sendMessage } from '../services/api';

function AIPharmacist() {
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

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

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
                content: response.response || response.user_message || response.reply || JSON.stringify(response),
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                status: 'success'
            }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                id: Date.now(),
                role: 'error',
                content: 'Connection error. Please verify backend services are running.',
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                status: 'error'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const toggleRecording = () => {
        if (!isRecording) {
            // Start recording
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognition) {
                const recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';

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

    const getMessageClass = (role) => {
        if (role === 'error') return 'message error';
        return `message ${role}`;
    };

    const getAvatarIcon = (role, status) => {
        if (role === 'user') return <User size={16} />;
        if (status === 'error' || role === 'error') return <X size={16} />;
        return <Check size={16} />;
    };

    return (
        <div className="chat-container">
            <div className="chat-messages">
                {messages.map((msg) => (
                    <div key={msg.id} className={getMessageClass(msg.role)}>
                        <div className="message-avatar">
                            {getAvatarIcon(msg.role, msg.status)}
                        </div>
                        <div>
                            <div className="message-content">{msg.content}</div>
                            <div className="message-time">{msg.time}</div>
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="message assistant">
                        <div className="message-avatar">
                            <Bot size={16} />
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

            <div className="chat-input-area">
                <div className="chat-input-wrapper">
                    <button className="upload-btn" title="Upload file">
                        <Upload size={20} />
                    </button>

                    <input
                        type="text"
                        className="chat-input"
                        placeholder="Type your message or describe symptom"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        disabled={isLoading}
                    />

                    <button
                        className={`voice-btn ${isRecording ? 'recording' : ''}`}
                        onClick={toggleRecording}
                        title={isRecording ? 'Stop recording' : 'Voice input'}
                    >
                        <Mic size={20} />
                    </button>

                    <button
                        className="send-btn"
                        onClick={handleSend}
                        disabled={!input.trim() || isLoading}
                        title="Send message"
                    >
                        <Send size={18} />
                    </button>
                </div>
            </div>
        </div>
    );
}

export default AIPharmacist;
