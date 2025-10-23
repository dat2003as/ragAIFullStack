// src/components/Sidebar/Sidebar.jsx
import React from 'react';
import { ImageUpload } from './ImageUpload';
import { CSVUpload } from './CSVUpload';
import { DocumentUpload } from './DocumentUpload';
import { Button } from '../UI/Button';
import { Trash2 } from 'lucide-react';

export const Sidebar = ({ sessionId, onClearChat }) => {
  return (
    <div className="w-80 bg-surface border-r border-gray-200 flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-xl font-bold text-secondary">AI Chat Assistant</h2>
        <p className="text-sm text-gray-500 mt-1">Upload files to get started</p>
      </div>

      {/* Upload Sections */}
      <div className="flex-1 p-4 space-y-4">
        <ImageUpload sessionId={sessionId} />
        <CSVUpload sessionId={sessionId} />
        <DocumentUpload sessionId={sessionId} />
      </div>

      {/* Clear Chat Button */}
      <div className="p-4 border-t border-gray-200">
        <Button
          variant="outline"
          onClick={onClearChat}
          className="w-full flex items-center justify-center gap-2"
        >
          <Trash2 size={16} />
          Clear Chat
        </Button>
      </div>
    </div>
  );
};