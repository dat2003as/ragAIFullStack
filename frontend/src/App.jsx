import React, { useState, useEffect } from 'react';
import { MainLayout } from './components/Layout/MainLayout';
import { useChat } from './hooks/useChat';
import { v4 as uuidv4 } from 'uuid';
import './App.css';

function App() {
  const [sessionId] = useState(() => {
    // Get or create session ID
    const stored = localStorage.getItem('sessionId');
    if (stored) return stored;
    
    const newId = uuidv4();
    localStorage.setItem('sessionId', newId);
    return newId;
  });

  const { messages, isLoading, error, sendMessage, clearChat } = useChat(sessionId);

  const handleSendMessage = async (message) => {
    try {
      await sendMessage(message);
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  const handleClearChat = async () => {
    if (window.confirm('Are you sure you want to clear the chat history?')) {
      try {
        await clearChat();
      } catch (err) {
        console.error('Failed to clear chat:', err);
      }
    }
  };

  return (
    <MainLayout
      sessionId={sessionId}
      messages={messages}
      onSendMessage={handleSendMessage}
      isLoading={isLoading}
      onClearChat={handleClearChat}
    />
  );
}

export default App;