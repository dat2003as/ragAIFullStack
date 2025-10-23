import { useState } from 'react';

export const useFileUpload = (uploadFn) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);

  const upload = async (file) => {
    setIsUploading(true);
    setUploadError(null);

    try {
      const response = await uploadFn(file);
      setUploadedFile(response);
      return response;
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Upload failed';
      setUploadError(errorMsg);
      throw err;
    } finally {
      setIsUploading(false);
    }
  };

  const clear = () => {
    setUploadedFile(null);
    setUploadError(null);
  };

  return {
    isUploading,
    uploadError,
    uploadedFile,
    upload,
    clear,
  };
};