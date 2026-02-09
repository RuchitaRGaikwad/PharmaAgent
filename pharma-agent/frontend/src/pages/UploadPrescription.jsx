import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Upload, FileText, CheckCircle, AlertCircle, Pill, ClipboardList } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function UploadPrescription() {
    const { t } = useTranslation();
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState(null);
    const [isDragging, setIsDragging] = useState(false);
    const [ocrResult, setOcrResult] = useState(null);
    const fileInputRef = useRef(null);

    const handleFileSelect = (selectedFile) => {
        if (!selectedFile) return;

        const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
        if (!validTypes.includes(selectedFile.type)) {
            setUploadStatus({ type: 'error', message: t('upload.error_type') });
            return;
        }

        if (selectedFile.size > 10 * 1024 * 1024) {
            setUploadStatus({ type: 'error', message: t('upload.error_size') });
            return;
        }

        setFile(selectedFile);
        setUploadStatus(null);
        setOcrResult(null);

        const reader = new FileReader();
        reader.onload = (e) => setPreview(e.target.result);
        reader.readAsDataURL(selectedFile);
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
        setOcrResult(null);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${API_BASE}/prescriptions/upload`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'Upload failed');
            }

            if (result.success) {
                setUploadStatus({ type: 'success', message: t('upload.success') });
                setOcrResult(result);
            } else {
                throw new Error(t('upload.failed'));
            }
        } catch (error) {
            setUploadStatus({ type: 'error', message: error.message || t('common.error') });
        } finally {
            setIsUploading(false);
        }
    };

    const resetUpload = () => {
        setFile(null);
        setPreview(null);
        setUploadStatus(null);
        setOcrResult(null);
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">📋 {t('upload.title')}</h1>
                <p className="page-subtitle">{t('upload.subtitle')}</p>
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
                    accept="image/jpeg,image/png,image/jpg"
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
                ) : (
                    <>
                        <div className="upload-icon">
                            <Upload size={48} style={{ color: 'var(--text-muted)' }} />
                        </div>
                        <p className="upload-text">{t('upload.drag_drop')}</p>
                        <p className="upload-hint">{t('upload.supported')}</p>
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

            {file && !ocrResult && (
                <div style={{ marginTop: '20px', display: 'flex', gap: '12px', justifyContent: 'center' }}>
                    <button
                        className="btn btn-secondary"
                        onClick={resetUpload}
                    >
                        {t('common.cancel')}
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={handleUpload}
                        disabled={isUploading}
                    >
                        {isUploading ? t('upload.processing') : t('upload.analyze')}
                    </button>
                </div>
            )}

            {/* OCR Results Display */}
            {ocrResult && (
                <div style={{ marginTop: '30px' }}>
                    <div className="data-card" style={{ marginBottom: '20px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                            <Pill size={24} style={{ color: 'var(--accent-primary)' }} />
                            <h3 style={{ margin: 0, color: 'var(--text-primary)' }}>{t('upload.detected')}</h3>
                        </div>

                        {ocrResult.detected_medicines && ocrResult.detected_medicines.length > 0 ? (
                            <div className="cards-grid" style={{ marginTop: '15px' }}>
                                {ocrResult.detected_medicines.map((medicine, index) => (
                                    <div key={index} className="medicine-card">
                                        <div className="medicine-name">{medicine.name || medicine}</div>
                                        {medicine.dosage && (
                                            <div className="medicine-info">
                                                <span>{t('upload.dosage')}: {medicine.dosage}</span>
                                            </div>
                                        )}
                                        {medicine.frequency && (
                                            <div style={{ marginTop: '8px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                                                {medicine.frequency}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p style={{ color: 'var(--text-muted)' }}>{t('upload.no_medicines')}</p>
                        )}

                        <div style={{ marginTop: '10px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                            {t('upload.confidence')}: {Math.round((ocrResult.confidence || 0) * 100)}%
                        </div>
                    </div>

                    {ocrResult.extracted_text && (
                        <div className="data-card">
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                                <ClipboardList size={24} style={{ color: 'var(--accent-secondary)' }} />
                                <h3 style={{ margin: 0, color: 'var(--text-primary)' }}>{t('upload.extracted')}</h3>
                            </div>
                            <pre style={{
                                background: 'var(--bg-secondary)',
                                padding: '15px',
                                borderRadius: '8px',
                                whiteSpace: 'pre-wrap',
                                wordWrap: 'break-word',
                                color: 'var(--text-secondary)',
                                fontSize: '0.9rem',
                                maxHeight: '200px',
                                overflow: 'auto'
                            }}>
                                {ocrResult.extracted_text}
                            </pre>
                        </div>
                    )}

                    <div style={{ marginTop: '20px', display: 'flex', gap: '12px', justifyContent: 'center' }}>
                        <button className="btn btn-secondary" onClick={resetUpload}>
                            {t('upload.upload_another')}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

export default UploadPrescription;
