import React from 'react';
import { MessageSquare } from 'lucide-react';

export const Header = () => {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
          <MessageSquare size={24} className="text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-secondary">AI Chat Application</h1>
          <p className="text-sm text-gray-500">Chat with your images, CSVs, and documents</p>
        </div>
      </div>
    </header>
  );
};