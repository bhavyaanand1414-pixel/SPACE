import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
});

export const checkHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

export const uploadSatelliteImage = async (file, satelliteType, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  if (satelliteType) {
    formData.append('satellite', satelliteType);
  }
  const response = await apiClient.post('/images/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: onProgress,
  });
  return response.data;
};

export const validateAnalysisPair = async (imageBeforeIdOrPath, imageAfterIdOrPath, satelliteHint) => {
  const response = await apiClient.post('/analyses/validate', {
    image_before_id: imageBeforeIdOrPath,
    image_after_id: imageAfterIdOrPath,
    satellite: satelliteHint,
  });
  return response.data;
};

export const getAnalyses = async () => {
  const response = await apiClient.get('/analyses');
  return response.data;
};

export const getAnalysisDetails = async (analysisId) => {
  const response = await apiClient.get(`/analyses/${analysisId}`);
  return response.data;
};

export const getAnalysisChangePolygons = async (analysisId) => {
  const response = await apiClient.get(`/analyses/${analysisId}/changes`);
  return response.data;
};

export const runAnalysis = async (
  analysisId,
  imageBeforeId,
  imageAfterId,
  confidenceThreshold = 0.5
) => {
  const response = await apiClient.post(`/analyses/${analysisId}/run`, {
    image_before_id: imageBeforeId,
    image_after_id: imageAfterId,
    confidence_threshold: confidenceThreshold,
  });
  return response.data;
};
