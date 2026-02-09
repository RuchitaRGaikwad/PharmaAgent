import React from 'react';
import { useTranslation } from 'react-i18next';
import { Heart, User, Calendar, Phone, Mail, MapPin } from 'lucide-react';

function HealthProfile() {
    const { t } = useTranslation();

    // Mock customer data
    const customer = {
        name: 'John Doe',
        email: 'john.doe@email.com',
        phone: '+1 (555) 123-4567',
        address: '123 Main St, Boston, MA 02101',
        dob: '1985-03-15',
        allergies: ['Penicillin', 'Sulfa drugs'],
        conditions: ['Hypertension', 'Type 2 Diabetes'],
        currentMedications: [
            { name: 'Metformin', dosage: '500mg', frequency: 'Twice daily' },
            { name: 'Lisinopril', dosage: '10mg', frequency: 'Once daily' }
        ]
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <h1 className="page-title">❤️ {t('health.title')}</h1>
                <p className="page-subtitle">{t('health.subtitle')}</p>
            </div>

            <div className="cards-grid" style={{ marginBottom: '24px' }}>
                <div className="medicine-card">
                    <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <User size={20} />
                        {t('health.personal_info')}
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-secondary)' }}>
                            <User size={16} />
                            {customer.name}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-secondary)' }}>
                            <Mail size={16} />
                            {customer.email}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-secondary)' }}>
                            <Phone size={16} />
                            {customer.phone}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-secondary)' }}>
                            <MapPin size={16} />
                            {customer.address}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-secondary)' }}>
                            <Calendar size={16} />
                            {t('health.born')}: {new Date(customer.dob).toLocaleDateString()}
                        </div>
                    </div>
                </div>

                <div className="medicine-card">
                    <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Heart size={20} />
                        {t('health.conditions')}
                    </h3>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                        {customer.conditions.map((condition, i) => (
                            <span key={i} className="badge badge-info">{condition}</span>
                        ))}
                    </div>

                    <h4 style={{ margin: '20px 0 12px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        {t('health.allergies')}
                    </h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                        {customer.allergies.map((allergy, i) => (
                            <span key={i} className="badge badge-danger">{allergy}</span>
                        ))}
                    </div>
                </div>
            </div>

            <div className="table-container">
                <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)' }}>
                    <h3>{t('health.medications')}</h3>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>{t('health.medication_name')}</th>
                            <th>{t('health.dosage')}</th>
                            <th>{t('health.frequency')}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {customer.currentMedications.map((med, i) => (
                            <tr key={i}>
                                <td><strong>{med.name}</strong></td>
                                <td>{med.dosage}</td>
                                <td>{med.frequency}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default HealthProfile;
