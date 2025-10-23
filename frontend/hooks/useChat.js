import { useState, useCallback } from 'react';
import { sendMessage } from '../services/api';

export const useChat = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const addMessage = useCallback((message) => {
    setMessages(prev => [...prev, message]);
  }, []);

  const sendChatMessage = useCallback(async (content, files = []) => {
    setIsLoading(true);
    setError(null);

    // Thêm tin nhắn của user
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };
    addMessage(userMessage);

    try {
      const response = await sendMessage(content, files);
      
      // Thêm tin nhắn phản hồi từ AI
      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.message,
        timestamp: new Date().toISOString()
      };
      addMessage(aiMessage);

      return response.data;
    } catch (err) {
      setError(err.message || 'Có lỗi xảy ra khi gửi tin nhắn');
      console.error('Chat error:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [addMessage]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendChatMessage,
    clearMessages,
    addMessage
  };
};