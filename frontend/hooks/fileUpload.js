import { useState, useCallback } from 'react';
import { uploadFile } from '../services/api';

export const useFileUpload = () => {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const uploadFiles = useCallback(async (files, fileType = 'document') => {
    setIsUploading(true);
    setUploadError(null);
    setUploadProgress(0);

    const formData = new FormData();
    
    // Thêm từng file vào FormData
    Array.from(files).forEach((file) => {
      formData.append('files', file);
    });
    formData.append('fileType', fileType);

    try {
      const response = await uploadFile(formData, (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        setUploadProgress(percentCompleted);
      });

      const newFiles = response.data.files || [];
      setUploadedFiles(prev => [...prev, ...newFiles]);
      
      return newFiles;
    } catch (err) {
      const errorMessage = err.response?.data?.message || 'Có lỗi khi tải file lên';
      setUploadError(errorMessage);
      console.error('Upload error:', err);
      throw err;
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, []);

  const removeFile = useCallback((fileId) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
  }, []);

  const clearFiles = useCallback(() => {
    setUploadedFiles([]);
    setUploadError(null);
  }, []);

  return {
    uploadedFiles,
    isUploading,
    uploadError,
    uploadProgress,
    uploadFiles,
    removeFile,
    clearFiles
  };
};