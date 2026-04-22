import React, { useState, useEffect, useRef } from 'react';
import { Send, Mic, MicOff, Upload, Bot, User } from 'lucide-react';
import { sendMessage } from '../services/api';
import VoiceInput from '../components/VoiceInput';
import PrescriptionUpload from '../components/PrescriptionUpload';

function UserView() {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: "Hello! Welcome to PharmaAgent, your AI pharmacy assistant. 👋\n\nI can help you order medicines, check availability, or answer questions. What would you like today?"
        }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const [showUpload, setShowUpload] = useState(false);
    const messagesEndRef = useRef(null);

    // Auto-scroll to bottom of messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Generate session ID on mount
    useEffect(() => {
        setSessionId(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
    }, []);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = input.trim();
        setInput('');

        // Add user message
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsLoading(true);

        try {
            const response = await sendMessage(userMessage, sessionId, 1); // Default customer ID 1

            // Add assistant response
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: response.response || response.user_message || response.reply || JSON.stringify(response),
                order: response.order
            }]);

            // Check if prescription upload is needed
            if (response.requires_action === 'prescription_upload') {
                setShowUpload(true);
            }
        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: "I'm sorry, I couldn't process your request. Please ensure the backend is running and try again."
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

    const handleVoiceResult = (transcript) => {
        setInput(transcript);
    };

    const handlePrescriptionUploaded = () => {
        setShowUpload(false);
        setMessages(prev => [...prev, {
            role: 'assistant',
            content: "✅ Prescription uploaded successfully! Your prescription has been verified. You can now proceed with your order. Would you like me to continue processing your previous request?"
        }]);
    };

    // Format message content with markdown-like styling
    const formatMessage = (content) => {
        if (!content) return '';

        // Convert **bold** to <strong>
        let formatted = content.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // Convert bullet points
        formatted = formatted.replace(/^• (.+)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/^- (.+)$/gm, '<li>$1</li>');

        // Convert line breaks
        formatted = formatted.replace(/\n/g, '<br/>');

        // Wrap consecutive <li> in <ul>
        formatted = formatted.replace(/(<li>.*<\/li>)(<br\/>)?(<li>)/g, '$1$3');
        formatted = formatted.replace(/(<li>.*<\/li>)/g, '<ul>$1</ul>');
        formatted = formatted.replace(/<\/ul><ul>/g, '');

        return formatted;
    };

    return (
        <div className="chat-container">
            {/* Messages Area */}
            <div className="chat-messages">
                {messages.map((message, index) => (
                    <div key={index} className={`chat-message ${message.role}`}>
                        <div className={`message-avatar ${message.role}`}>
                            {message.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                        </div>
                        <div
                            className="message-content"
                            dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}
                        />
                    </div>
                ))}

                {/* Loading indicator */}
                {isLoading && (
                    <div className="chat-message assistant">
                        <div className="message-avatar assistant">
                            <Bot size={18} />
                        </div>
                        <div className="message-content">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Prescription Upload Modal */}
            {showUpload && (
                <PrescriptionUpload
                    customerId={1}
                    onClose={() => setShowUpload(false)}
                    onUploaded={handlePrescriptionUploaded}
                />
            )}

            {/* Input Area */}
            <div className="chat-input-container">
                <div className="chat-input-wrapper">
                    <VoiceInput onResult={handleVoiceResult} />

                    <input
                        type="text"
                        className="chat-input"
                        placeholder="Type your message... (e.g., 'I need 30 Paracetamol tablets')"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        disabled={isLoading}
                    />

                    <button
                        className="btn btn-icon"
                        onClick={() => setShowUpload(true)}
                        title="Upload Prescription"
                    >
                        <Upload size={20} />
                    </button>

                    <button
                        className="send-btn"
                        onClick={handleSend}
                        disabled={!input.trim() || isLoading}
                        title="Send message"
                    >
                        <Send size={20} />
                    </button>
                </div>
            </div>
        </div>
    );
}

export default UserView;
