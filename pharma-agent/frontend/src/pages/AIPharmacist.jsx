import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, Upload, Bot, User, X, Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { sendMessage } from '../services/api';

function AIPharmacist() {
    const { t } = useTranslation();
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [sessionId] = useState(() => `session_${Date.now()}`);
    const messagesEndRef = useRef(null);

    // Initialize/Update welcome message when language changes
    // Only if the chat is empty or contains only the previous welcome message
    useEffect(() => {
        const welcomeMessage = {
            id: 'welcome',
            role: 'assistant',
            content: `${t('chat.welcome')}

${t('chat.intro_p1')}
• 💊 ${t('chat.intro_l1')}
• 📋 ${t('chat.intro_l2')}
• 🔍 ${t('chat.intro_l3')}
• ⏰ ${t('chat.intro_l4')}

**${t('chat.intro_disclaimer_title')}**
- ${t('chat.intro_disclaimer_1')}
- ${t('chat.intro_disclaimer_2')}

${t('chat.intro_prompt')}`,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            status: 'success'
        };

        setMessages(prev => {
            if (prev.length === 0) return [welcomeMessage];
            // If the first message is the welcome message (id 1 or 'welcome'), update it
            if (prev.length > 0 && (prev[0].id === 1 || prev[0].id === 'welcome')) {
                const newMessages = [...prev];
                newMessages[0] = { ...newMessages[0], content: welcomeMessage.content };
                return newMessages;
            }
            return prev;
        });
    }, [t]);

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
                        placeholder={t('chat.placeholder')}
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
