import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileText, AlertCircle, Loader2, CheckCircle2, X, RefreshCw } from 'lucide-react';

const SUPPORTED_FORMATS = ['.png', '.jpg', '.jpeg', '.pdf', '.bmp', '.tiff'];
const MAX_SIZE_MB = 10;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;
const UPLOAD_TIMEOUT_MS = 120000; // 120 seconds timeout for CPU-bound OCR and ML inference

const UploadReport = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const abortControllerRef = useRef(null);

  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [uploadStatus, setUploadStatus] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Track elapsed time during analysis to provide transparent user feedback
  useEffect(() => {
    let timer;
    if (isUploading) {
      setElapsedSeconds(0);
      timer = setInterval(() => {
        setElapsedSeconds((prev) => {
          const next = prev + 1;
          if (next < 15) {
            setUploadStatus('Step 1/3: Reading image and extracting text via PaddleOCR...');
          } else if (next < 32) {
            setUploadStatus('Step 2/3: Recognizing biomedical entities, symptoms & measurements...');
          } else {
            setUploadStatus('Step 3/3: Generating patient summary & verifying clinical metrics...');
          }
          return next;
        });
      }, 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => clearInterval(timer);
  }, [isUploading]);

  // Clean up preview object URL on unmount
  useEffect(() => {
    return () => {
      if (previewUrl && previewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const validateFile = (selectedFile) => {
    setErrorMessage('');
    if (!selectedFile) return false;

    const ext = '.' + selectedFile.name.split('.').pop().toLowerCase();
    if (!SUPPORTED_FORMATS.includes(ext)) {
      setErrorMessage(`Unsupported file format. Please upload ${SUPPORTED_FORMATS.join(', ')}.`);
      return false;
    }

    if (selectedFile.size > MAX_SIZE_BYTES) {
      setErrorMessage(`File exceeds the maximum limit of ${MAX_SIZE_MB}MB.`);
      return false;
    }

    if (selectedFile.size === 0) {
      setErrorMessage('The selected file is empty (0 bytes).');
      return false;
    }

    return true;
  };

  const handleFileSelection = (selectedFile) => {
    if (!validateFile(selectedFile)) {
      setFile(null);
      setPreviewUrl(null);
      return;
    }

    setFile(selectedFile);
    if (selectedFile.type.startsWith('image/')) {
      const url = URL.createObjectURL(selectedFile);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleClearFile = (e) => {
    if (e) e.stopPropagation();
    if (isUploading && abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setFile(null);
    setPreviewUrl(null);
    setErrorMessage('');
    setUploadStatus('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUploadAndAnalyze = async () => {
    if (!file) {
      setErrorMessage('Please select a valid report file first.');
      return;
    }

    setIsUploading(true);
    setErrorMessage('');
    setUploadStatus('Step 1/3: Reading image and extracting text via PaddleOCR...');

    const controller = new AbortController();
    abortControllerRef.current = controller;

    // Timeout watchdog to ensure upload never hangs indefinitely
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, UPLOAD_TIMEOUT_MS);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const contentType = response.headers.get('content-type') || '';
      let data;

      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const rawText = await response.text();
        throw new Error(rawText || `Server responded with status ${response.status}`);
      }

      if (!response.ok) {
        throw new Error(data.detail || `Upload failed with status ${response.status}`);
      }

      // Store in session storage for direct routing / page refresh
      sessionStorage.setItem(`mediguide_report_${data.report_id}`, JSON.stringify(data));
      if (previewUrl) {
        sessionStorage.setItem(`mediguide_preview_${data.report_id}`, previewUrl);
      }

      setUploadStatus('Analysis complete! Redirecting...');

      // Navigate to ReportAnalysis with actual data
      navigate(`/patient/reports/${data.report_id}`, {
        state: { report: data, previewUrl },
      });
    } catch (err) {
      if (err.name === 'AbortError') {
        setErrorMessage(
          `Analysis timed out after ${UPLOAD_TIMEOUT_MS / 1000}s. On CPU environments, large documents may take longer. Please try a clearer or smaller document, or click Retry.`
        );
      } else {
        setErrorMessage(err.message || 'An unexpected error occurred during processing.');
      }
    } finally {
      clearTimeout(timeoutId);
      setIsUploading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-800 mb-2">Upload Medical Report</h1>
      <p className="text-slate-500 mb-6 text-sm">
        Upload lab reports, prescriptions, or clinical summaries for automated patient-friendly translation.
      </p>

      {/* Error alert with retry button */}
      {errorMessage && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl flex items-start space-x-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-red-500" />
          <div className="flex-1">
            <p className="font-semibold">Unable to process document</p>
            <p className="mt-0.5 leading-relaxed">{errorMessage}</p>
            {file && (
              <div className="mt-3 flex space-x-3">
                <button
                  type="button"
                  onClick={handleUploadAndAnalyze}
                  className="inline-flex items-center space-x-1.5 bg-red-600 hover:bg-red-700 text-white text-xs px-3 py-1.5 rounded-lg font-medium transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Retry Analysis</span>
                </button>
                <button
                  type="button"
                  onClick={handleClearFile}
                  className="text-xs text-slate-600 hover:text-slate-800 bg-white border border-slate-300 px-3 py-1.5 rounded-lg font-medium transition-colors"
                >
                  Select Another File
                </button>
              </div>
            )}
          </div>
          <button onClick={() => setErrorMessage('')} className="text-red-400 hover:text-red-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-8">
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => e.target.files && handleFileSelection(e.target.files[0])}
          className="hidden"
          accept={SUPPORTED_FORMATS.join(',')}
          disabled={isUploading}
        />

        <div
          onClick={() => !isUploading && fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center transition-all cursor-pointer ${
            isDragging
              ? 'border-teal-500 bg-teal-50/50'
              : 'border-slate-300 hover:border-teal-400 hover:bg-slate-50'
          } ${isUploading ? 'opacity-80 cursor-not-allowed' : ''}`}
        >
          {isUploading ? (
            <div className="py-6 flex flex-col items-center max-w-md mx-auto">
              <Loader2 className="w-12 h-12 text-teal-600 animate-spin mb-4" />
              <h3 className="text-lg font-bold text-slate-800 mb-1">Analyzing Medical Report</h3>
              <p className="text-slate-600 text-sm font-medium mt-1">{uploadStatus}</p>
              <p className="text-slate-400 text-xs mt-1">Elapsed time: {elapsedSeconds}s</p>

              <div className="w-64 bg-slate-100 rounded-full h-2 mt-4 overflow-hidden">
                <div
                  className="bg-teal-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(95, Math.max(10, elapsedSeconds * 2))}%` }}
                ></div>
              </div>

              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  if (abortControllerRef.current) {
                    abortControllerRef.current.abort();
                  }
                }}
                className="mt-6 text-xs text-slate-500 hover:text-red-600 font-medium underline"
              >
                Cancel Analysis
              </button>
            </div>
          ) : file ? (
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-teal-50 text-teal-600 rounded-full flex items-center justify-center mb-3">
                <FileText className="w-8 h-8" />
              </div>
              <p className="font-semibold text-slate-800">{file.name}</p>
              <p className="text-xs text-slate-400 mt-1">
                {(file.size / (1024 * 1024)).toFixed(2)} MB • {file.type || 'Document'}
              </p>
              <div className="flex space-x-3 mt-4">
                <button
                  type="button"
                  onClick={handleClearFile}
                  className="text-xs text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 px-3 py-1.5 rounded-lg font-medium transition-colors"
                >
                  Change File
                </button>
              </div>
            </div>
          ) : (
            <>
              <UploadCloud className="w-12 h-12 text-teal-500 mb-4" />
              <h3 className="text-lg font-bold text-slate-800 mb-1">Click or drag file to this area</h3>
              <p className="text-slate-500 text-sm mb-6 max-w-md">
                Secure OCR and biomedical entity extraction. Documents are processed locally in a privacy-preserving environment.
              </p>
              <div className="bg-teal-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-teal-700 transition-colors shadow-sm">
                Select File
              </div>
              <p className="text-xs text-slate-400 mt-4">
                Supported formats: PDF, JPG, PNG, BMP, TIFF (Max {MAX_SIZE_MB}MB)
              </p>
            </>
          )}
        </div>

        {file && !isUploading && (
          <div className="mt-6 flex justify-end">
            <button
              onClick={handleUploadAndAnalyze}
              className="bg-teal-600 hover:bg-teal-700 text-white font-medium px-6 py-2.5 rounded-lg shadow-sm transition-colors flex items-center space-x-2"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Start Analysis</span>
            </button>
          </div>
        )}
      </div>

      <div className="mt-6 p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500 leading-relaxed">
        <strong>Privacy & Clinical Disclaimer:</strong> MediGuide-AI processes documents exclusively to assist in medical comprehension. It does not provide clinical diagnoses, prescribe medications, or alter medical treatment plans.
      </div>
    </div>
  );
};

export default UploadReport;
