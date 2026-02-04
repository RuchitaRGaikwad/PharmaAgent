import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadPrescription } from '../services/api';

function UploadPrescription() {
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef(null);

    const handleFileSelect = (selectedFile) => {
        if (!selectedFile) return;

        const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
        if (!validTypes.includes(selectedFile.type)) {
            setUploadStatus({ type: 'error', message: 'Please upload JPG, PNG, or PDF files only.' });
            return;
        }

        if (selectedFile.size > 10 * 1024 * 1024) {
            setUploadStatus({ type: 'error', message: 'File size must be less than 10MB.' });
            return;
        }

        setFile(selectedFile);
        setUploadStatus(null);

        if (selectedFile.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => setPreview(e.target.result);
            reader.readAsDataURL(selectedFile);
        } else {
            setPreview(null);
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
        const droppedFile = e.dataTransfer.files[0];
        handleFileSelect(droppedFile);
    };

    const handleUpload = async () => {
        if (!file) return;

        setIsUploading(true);
        try {
            await uploadPrescription(1, file); // Customer ID 1
            setUploadStatus({ type: 'success', message: 'Prescription uploaded and verified successfully!' });
            setFile(null);
            setPreview(null);
        } catch (error) {
            setUploadStatus({ type: 'error', message: 'Upload failed. Please try again.' });
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">📋 Upload Prescription</h1>
                <p className="page-subtitle">Upload your prescription for AI-powered extraction and verification</p>
            </div>

            <div
                className={`upload-area ${isDragging ? 'dragover' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{
                    background: isDragging ? 'rgba(32, 211, 178, 0.05)' : 'var(--bg-tertiary)',
                    borderColor: isDragging ? 'var(--accent-primary)' : undefined
                }}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*,.pdf"
                    onChange={(e) => handleFileSelect(e.target.files[0])}
                    style={{ display: 'none' }}
                />

                {preview ? (
                    <div style={{ textAlign: 'center' }}>
                        <img
                            src={preview}
                            alt="Preview"
                            style={{
                                maxWidth: '200px',
                                maxHeight: '200px',
                                borderRadius: '8px',
                                marginBottom: '16px'
                            }}
                        />
                        <p style={{ color: 'var(--accent-primary)' }}>{file.name}</p>
                    </div>
                ) : file ? (
                    <div style={{ textAlign: 'center' }}>
                        <FileText size={48} className="upload-icon" />
                        <p style={{ color: 'var(--accent-primary)' }}>{file.name}</p>
                    </div>
                ) : (
                    <>
                        <div className="upload-icon">
                            <Upload size={48} style={{ color: 'var(--text-muted)' }} />
                        </div>
                        <p className="upload-text">Drag and drop or click to upload</p>
                        <p className="upload-hint">Supports: JPG, PNG, PDF</p>
                    </>
                )}
            </div>

            {uploadStatus && (
                <div
                    className={`alert-banner`}
                    style={{
                        marginTop: '20px',
                        background: uploadStatus.type === 'success'
                            ? 'rgba(34, 197, 94, 0.1)'
                            : 'rgba(239, 68, 68, 0.1)',
                        borderColor: uploadStatus.type === 'success'
                            ? 'rgba(34, 197, 94, 0.3)'
                            : 'rgba(239, 68, 68, 0.3)'
                    }}
                >
                    <div className="alert-content" style={{
                        color: uploadStatus.type === 'success' ? 'var(--success)' : 'var(--danger)'
                    }}>
                        {uploadStatus.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
                        {uploadStatus.message}
                    </div>
                </div>
            )}

            {file && (
                <div style={{ marginTop: '20px', display: 'flex', gap: '12px', justifyContent: 'center' }}>
                    <button
                        className="btn btn-secondary"
                        onClick={() => { setFile(null); setPreview(null); setUploadStatus(null); }}
                    >
                        Cancel
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={handleUpload}
                        disabled={isUploading}
                    >
                        {isUploading ? 'Uploading...' : 'Upload Prescription'}
                    </button>
                </div>
            )}
        </div>
    );
}

export default UploadPrescription;
