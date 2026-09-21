import React, { useState } from 'react';
import { UserPlus, LogIn, UserCircle, Stethoscope, ShieldCheck, PhoneCall } from 'lucide-react';
import { api } from '../services/api';

type Role = 'patient' | 'doctor' | 'admin';

interface AuthPageProps {
  onLogin: (role: Role, userId: string, userName: string) => void;
  onGuestCall: () => void;
}

export const AuthPage: React.FC<AuthPageProps> = ({ onLogin, onGuestCall }) => {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [role, setRole] = useState<Role>('patient');
  
  // Form fields
  const [userId, setUserId] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLoginMode) {
        // Simple mock login validation
        if (!userId.trim()) {
          setError('Please enter your ID.');
          setLoading(false);
          return;
        }

        if (role === 'patient') {
          const patients = await api.getPatients();
          const patient = patients.find(p => p.patient_id === userId || p.patient_id === `P-${userId}`);
          if (patient) {
            onLogin('patient', patient.patient_id, `${patient.first_name} ${patient.last_name}`);
          } else {
            if (userId.toLowerCase() === 'patient' || userId === '01') {
              onLogin('patient', 'P-10023', 'Aarav Sharma');
            } else {
              setError('Patient ID not found.');
            }
          }
        } else if (role === 'doctor') {
          const doctors = await api.getDoctors();
          const doctor = doctors.find(d => d.id === userId || d.id === `DOC-${userId}`);
          if (doctor) {
            onLogin('doctor', doctor.id, doctor.name);
          } else {
            // Fallback for demo
            if (userId === 'DOC-01' || userId === '01') {
              onLogin('doctor', 'DOC-01', 'Dr. Ananya Rao');
            } else {
              setError('Doctor ID not found.');
            }
          }
        } else if (role === 'admin') {
          // Simple mock admin login
          if (userId === 'admin') {
            onLogin('admin', 'ADMIN', 'System Administrator');
          } else {
            setError('Invalid Admin credentials. Try ID "admin".');
          }
        }
      } else {
        // Sign Up Mode
        if (!name.trim()) {
          setError('Please enter your full name.');
          setLoading(false);
          return;
        }
        
        let newId = '';
        if (role === 'patient') {
          const parts = name.trim().split(' ');
          const fn = parts[0];
          const ln = parts.length > 1 ? parts.slice(1).join(' ') : 'Patient';
          try {
            const res = await api.registerPatient({
              first_name: fn,
              last_name: ln,
              date_of_birth: '1990-01-01', // Dummy default for frontend signup
              phone_number: '+91-99999-99999', // Dummy default
            });
            if (res.success && res.patient) {
              newId = (res.patient as any).id || (res.patient as any).patient_id;
            } else {
              setError(res.message || 'Registration failed.');
              setLoading(false);
              return;
            }
          } catch (e: any) {
            setError(e.message || 'Error registering patient.');
            setLoading(false);
            return;
          }
        } else if (role === 'doctor') {
          newId = `DOC-${Math.floor(Math.random() * 90) + 10}`;
        } else {
          newId = 'ADMIN-NEW';
        }

        // Notify user of their new ID (in a real app, this would be emailed or securely shown)
        alert(`Successfully signed up!\n\nYour new ID is: ${newId}\nPlease save this ID to log in next time.`);
        onLogin(role, newId, name);
      }
    } catch (err) {
      setError('An error occurred during authentication.');
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLoginMode(!isLoginMode);
    setError('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: 'var(--bg-color)', padding: '2rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1 style={{ color: 'var(--brand-primary)', fontSize: '2.5rem', marginBottom: '0.5rem', fontWeight: 700 }}>MedFront</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>Welcome to your healthcare portal</p>
      </div>

      <div style={{ background: 'var(--surface-color)', padding: '2.5rem', borderRadius: '16px', boxShadow: '0 10px 25px rgba(0,0,0,0.05)', width: '100%', maxWidth: '450px', border: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginBottom: '2rem' }}>
          <button 
            type="button"
            onClick={() => setRole('patient')}
            style={{ 
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', padding: '1rem', 
              background: role === 'patient' ? 'var(--blue-50)' : 'transparent', 
              color: role === 'patient' ? 'var(--blue-600)' : 'var(--text-secondary)',
              border: `2px solid ${role === 'patient' ? 'var(--blue-500)' : 'var(--border-color)'}`,
              borderRadius: '12px', cursor: 'pointer', flex: 1, transition: 'all 0.2s'
            }}
          >
            <UserCircle size={24} />
            <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Patient</span>
          </button>
          <button 
            type="button"
            onClick={() => setRole('doctor')}
            style={{ 
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', padding: '1rem', 
              background: role === 'doctor' ? 'var(--emerald-50)' : 'transparent', 
              color: role === 'doctor' ? 'var(--emerald-600)' : 'var(--text-secondary)',
              border: `2px solid ${role === 'doctor' ? 'var(--emerald-500)' : 'var(--border-color)'}`,
              borderRadius: '12px', cursor: 'pointer', flex: 1, transition: 'all 0.2s'
            }}
          >
            <Stethoscope size={24} />
            <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Doctor</span>
          </button>
          <button 
            type="button"
            onClick={() => setRole('admin')}
            style={{ 
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', padding: '1rem', 
              background: role === 'admin' ? 'var(--purple-50)' : 'transparent', 
              color: role === 'admin' ? 'var(--purple-600)' : 'var(--text-secondary)',
              border: `2px solid ${role === 'admin' ? 'var(--purple-500)' : 'var(--border-color)'}`,
              borderRadius: '12px', cursor: 'pointer', flex: 1, transition: 'all 0.2s'
            }}
          >
            <ShieldCheck size={24} />
            <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Admin</span>
          </button>
        </div>

        <div style={{ background: 'var(--blue-50)', border: '1px solid var(--blue-200)', borderRadius: '8px', padding: '1rem', marginBottom: '1.5rem', fontSize: '0.85rem', color: 'var(--blue-800)' }}>
          <strong>Demo Credentials:</strong><br/>
          Patient: <code>patient</code> or <code>P-10023</code><br/>
          Doctor: <code>DOC-01</code> or <code>01</code><br/>
          Admin: <code>admin</code>
        </div>

        <form onSubmit={handleSubmit}>
          <h2 style={{ color: 'var(--text-color)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {isLoginMode ? <LogIn size={20} /> : <UserPlus size={20} />}
            {isLoginMode ? `Log In as ${role.charAt(0).toUpperCase() + role.slice(1)}` : `Sign Up as ${role.charAt(0).toUpperCase() + role.slice(1)}`}
          </h2>

          {!isLoginMode && (
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-color)', fontWeight: 500 }}>Full Name</label>
              <input 
                type="text" 
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. John Doe"
                style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-color)' }}
                required={!isLoginMode}
              />
            </div>
          )}

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-color)', fontWeight: 500 }}>
              {isLoginMode ? 'ID / Username' : 'Choose a Username (Optional)'}
            </label>
            <input 
              type="text" 
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder={
                role === 'patient' ? "e.g. P-10023" : 
                role === 'doctor' ? "e.g. DOC-01" : "e.g. admin"
              }
              style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-color)' }}
              required={isLoginMode}
            />
          </div>

          {error && <div style={{ color: 'var(--red-500)', marginBottom: '1.5rem', fontSize: '0.9rem', padding: '0.5rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '6px' }}>{error}</div>}

          <button 
            type="submit" 
            disabled={loading}
            style={{ 
              width: '100%', padding: '0.875rem', 
              background: 'var(--brand-primary)', color: 'white', 
              border: 'none', borderRadius: '8px', cursor: 'pointer', 
              fontWeight: 600, fontSize: '1rem',
              transition: 'background 0.2s'
            }}
          >
            {loading ? 'Processing...' : (isLoginMode ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <div style={{ marginTop: '2rem', textAlign: 'center', borderTop: '1px solid var(--border-color)', paddingTop: '1.5rem' }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
            {isLoginMode ? "Don't have an account?" : "Already have an account?"}
          </p>
          <button 
            onClick={toggleMode} 
            style={{ background: 'none', border: 'none', color: 'var(--brand-primary)', cursor: 'pointer', fontWeight: 600, fontSize: '1rem', marginBottom: '1.5rem', display: 'block', width: '100%' }}
          >
            {isLoginMode ? 'Sign up now' : 'Log in instead'}
          </button>
          
          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1.5rem' }}>
            <button
              onClick={onGuestCall}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', width: '100%', padding: '0.75rem', background: 'var(--surface-color)', border: '2px solid var(--brand-primary)', color: 'var(--brand-primary)', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}
            >
              <PhoneCall size={18} />
              Call MedFront (No Login Required)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
