import { useState, useEffect, useCallback } from 'react';
import { chatAPI } from '../services/api';

export const useChat = (sessionId) => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load history on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const data = await chatAPI.getHistory(sessionId);
        setMessages(data.history || []);
      } catch (err) {
        console.error('Failed to load history:', err);
      }
    };
    
    loadHistory();
  }, [sessionId]);

  const sendMessage = useCallback(async (message) => {
    if (!message.trim()) return;

    setIsLoading(true);
    setError(null);

    // Add user message immediately
    const userMessage = {
      role: 'user',
      content: message,
      timestamp: Date.now() / 1000,
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await chatAPI.sendMessage(sessionId, message);
      
      // Add assistant response
      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: response.timestamp,
      };
      setMessages(prev => [...prev, assistantMessage]);
      
      return response;
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to send message');
      // Remove user message on error
      setMessages(prev => prev.slice(0, -1));
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const clearChat = useCallback(async () => {
    try {
      await chatAPI.clearHistory(sessionId);
      setMessages([]);
    } catch (err) {
      setError('Failed to clear chat');
      throw err;
    }
  }, [sessionId]);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
  };
};