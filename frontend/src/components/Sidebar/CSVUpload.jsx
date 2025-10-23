
// src/components/Sidebar/CSVUpload.jsx
import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { FileSpreadsheet, X, Upload, Link as LinkIcon } from 'lucide-react';
import { Card } from '../UI/Card';
import { Button } from '../UI/Button';
import { LoadingSpinner } from '../UI/LoadingSpinner';
import { csvAPI } from '../../services/api';

export const CSVUpload = ({ sessionId, onUploadSuccess }) => {
  const [uploadedCSV, setUploadedCSV] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [csvUrl, setCsvUrl] = useState('');
  const [showUrlInput, setShowUrlInput] = useState(false);

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      const response = await csvAPI.upload(sessionId, file);
      setUploadedCSV(response);
      if (onUploadSuccess) onUploadSuccess(response);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload CSV');
    } finally {
      setIsUploading(false);
    }
  };

  const handleUrlUpload = async () => {
    if (!csvUrl.trim()) return;

    setIsUploading(true);
    setError(null);

    try {
      const response = await csvAPI.uploadFromURL(sessionId, csvUrl);
      setUploadedCSV(response);
      setCsvUrl('');
      setShowUrlInput(false);
      if (onUploadSuccess) onUploadSuccess(response);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load CSV from URL');
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemove = async () => {
    try {
      await csvAPI.delete(sessionId);
      setUploadedCSV(null);
      setError(null);
    } catch (err) {
      console.error('Failed to delete CSV:', err);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv']
    },
    maxFiles: 1,
    disabled: isUploading || uploadedCSV !== null
  });

  return (
    <Card>
      <div className="flex items-center gap-2 mb-3">
        <FileSpreadsheet size={20} className="text-primary" />
        <h3 className="font-semibold text-secondary">CSV Upload</h3>
      </div>

      {!uploadedCSV ? (
        <>
          {/* File Upload */}
          {!showUrlInput && (
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors mb-2 ${
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
                    {isDragActive ? 'Drop CSV here' : 'Upload CSV file'}
                  </p>
                </>
              )}
            </div>
          )}

          {/* URL Input */}
          {showUrlInput ? (
            <div className="space-y-2">
              <input
                type="url"
                value={csvUrl}
                onChange={(e) => setCsvUrl(e.target.value)}
                placeholder="https://example.com/data.csv"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent"
                disabled={isUploading}
              />
              <div className="flex gap-2">
                <Button
                  onClick={handleUrlUpload}
                  disabled={!csvUrl.trim() || isUploading}
                  className="flex-1 text-sm"
                >
                  Load
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setShowUrlInput(false);
                    setCsvUrl('');
                  }}
                  className="text-sm"
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <Button
              variant="outline"
              onClick={() => setShowUrlInput(true)}
              className="w-full text-sm flex items-center justify-center gap-2"
              disabled={isUploading}
            >
              <LinkIcon size={16} />
              Load from URL
            </Button>
          )}
        </>
      ) : (
        <div className="space-y-2">
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm font-medium text-green-800">
              {uploadedCSV.filename || 'CSV loaded'}
            </p>
            <p className="text-xs text-green-600 mt-1">
              {uploadedCSV.rows} rows × {uploadedCSV.columns?.length || 0} columns
            </p>
          </div>
          <Button
            variant="danger"
            onClick={handleRemove}
            className="w-full text-sm flex items-center justify-center gap-2"
          >
            <X size={16} />
            Remove CSV
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