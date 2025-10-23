// src/components/Sidebar/ImageUpload.jsx
import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Image as ImageIcon, X, Upload } from 'lucide-react';
import { Card } from '../UI/Card';
import { Button } from '../UI/Button';
import { LoadingSpinner } from '../UI/LoadingSpinner';
import { imageAPI } from '../../services/api';

export const ImageUpload = ({ sessionId, onUploadSuccess }) => {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null);

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file (PNG, JPG)');
      return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('Image size must be less than 10MB');
      return;
    }

    setIsUploading(true);
    setError(null);

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);

    try {
      const response = await imageAPI.upload(sessionId, file);
      setUploadedImage(response);
      if (onUploadSuccess) onUploadSuccess(response);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload image');
      setPreview(null);
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemove = async () => {
    try {
      await imageAPI.delete(sessionId);
      setUploadedImage(null);
      setPreview(null);
      setError(null);
    } catch (err) {
      console.error('Failed to delete image:', err);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp']
    },
    maxFiles: 1,
    disabled: isUploading || uploadedImage !== null
  });

  return (
    <Card>
      <div className="flex items-center gap-2 mb-3">
        <ImageIcon size={20} className="text-primary" />
        <h3 className="font-semibold text-secondary">Image Upload</h3>
      </div>

      {!uploadedImage ? (
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
                {isDragActive
                  ? 'Drop the image here'
                  : 'Drag & drop an image, or click to select'}
              </p>
              <p className="text-xs text-gray-400 mt-1">PNG, JPG up to 10MB</p>
            </>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {preview && (
            <img
              src={preview}
              alt="Preview"
              className="w-full h-48 object-cover rounded-lg"
            />
          )}
          <div className="flex items-center justify-between">
            <div className="flex-1 truncate">
              <p className="text-sm font-medium">{uploadedImage.filename}</p>
              <p className="text-xs text-gray-500">
                {(uploadedImage.size_bytes / 1024).toFixed(1)} KB
              </p>
            </div>
            <Button
              variant="danger"
              onClick={handleRemove}
              className="ml-2"
            >
              <X size={16} />
            </Button>
          </div>
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