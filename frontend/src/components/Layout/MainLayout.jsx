import React from 'react';
import { Header } from './Header';
import { Sidebar } from '../Sidebar/Sidebar';
import { ChatContainer } from '../Chat/ChatContainer';

export const MainLayout = ({ 
  sessionId, 
  messages, 
  onSendMessage, 
  isLoading,
  onClearChat 
}) => {
  return (
    <div className="flex flex-col h-screen">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar sessionId={sessionId} onClearChat={onClearChat} />
        <div className="flex-1 flex flex-col">
          <ChatContainer
            messages={messages}
            onSendMessage={onSendMessage}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
};