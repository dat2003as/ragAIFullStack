// src/components/Sidebar/DocumentUpload.jsx
import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { FileText, X, Upload } from 'lucide-react';
import { Card } from '../UI/Card';
import { Button } from '../UI/Button';
import { LoadingSpinner } from '../UI/LoadingSpinner';
import { documentAPI } from '../../services/api';

export const DocumentUpload = ({ sessionId, onUploadSuccess }) => {
  const [uploadedDoc, setUploadedDoc] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      const response = await documentAPI.upload(sessionId, file);
      setUploadedDoc(response);
      if (onUploadSuccess) onUploadSuccess(response);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload document');
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemove = async () => {
    try {
      await documentAPI.delete(sessionId);
      setUploadedDoc(null);
      setError(null);
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md']
    },
    maxFiles: 1,
    disabled: isUploading || uploadedDoc !== null
  });

  return (
    <Card>
      <div className="flex items-center gap-2 mb-3">
        <FileText size={20} className="text-primary" />
        <h3 className="font-semibold text-secondary">Document Upload</h3>
      </div>

      {!uploadedDoc ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-primary bg-red-50'
              : 'border-gray-300 hover:border-primary'
          } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <input {...getInputProps()} />
          {isUploading ? (
            <LoadingSpinner />
          ) : (
            <>
              <Upload size={32} className="mx-auto mb-2 text-gray-400" />
              <p className="text-sm text-gray-600">
                {isDragActive ? 'Drop document here' : 'Upload a document'}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                PDF, DOCX, TXT, MD up to 20MB
              </p>
            </>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm font-medium text-blue-800 truncate">
              {uploadedDoc.filename}
            </p>
            <div className="text-xs text-blue-600 mt-1 space-y-1">
              <p>{uploadedDoc.metadata?.char_count?.toLocaleString()} characters</p>
              <p>{uploadedDoc.metadata?.word_count?.toLocaleString()} words</p>
            </div>
            {uploadedDoc.metadata?.preview && (
              <p className="text-xs text-gray-600 mt-2 line-clamp-2">
                {uploadedDoc.metadata.preview}
              </p>
            )}
          </div>
          <Button
            variant="danger"
            onClick={handleRemove}
            className="w-full text-sm flex items-center justify-center gap-2"
          >
            <X size={16} />
            Remove Document
          </Button>
        </div>
      )}

      {error && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600">
          {error}
        </div>
      )}
    </Card>
  );
};