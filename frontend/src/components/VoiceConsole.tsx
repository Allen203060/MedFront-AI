import { useEffect, useRef, useState } from 'react';
import { Mic, PhoneCall, PhoneOff, Send, VolumeX, Sparkles, ShieldCheck, UserCheck, Zap } from 'lucide-react';
import { useVoiceConsole } from '../hooks/useVoiceConsole';

interface VoiceConsoleProps {
  onAppointmentBooked?: () => void;
}

const PRESET_CALLERS = [
  {
    label: 'Aarav Sharma (+91-98765-43210) — Returning (Has Upcoming Appt)',
    phone: '+91-98765-43210',
    description: 'Upcoming Appt with Dr. Ananya Rao (Cardiology)',
  },
  {
    label: 'Priya Patel (+91-98123-45678) — Returning (No Appt)',
    phone: '+91-98123-45678',
    description: 'Existing patient record in Cosmos DB Layer A',
  },
  {
    label: 'Vikram Malhotra (+91-99887-76655) — Returning Patient',
    phone: '+91-99887-76655',
    description: 'Existing patient record in Cosmos DB Layer A',
  },
  {
    label: 'Unknown / New Patient (Default Greeting)',
    phone: '',
    description: 'Anonymous caller; Aura introduces herself',
  },
];

export const VoiceConsole: React.FC<VoiceConsoleProps> = ({ onAppointmentBooked }) => {
  const {
    isCalling,
    status,
    messages,
    interimText,
    isAgentSpeaking,
    recognizedPatient,
    analyser,
    startCall,
    endCall,
    sendTextMessage,
    stopPlayback,
  } = useVoiceConsole(onAppointmentBooked);

  const [selectedCallerPhone, setSelectedCallerPhone] = useState('+91-98765-43210');
  const [customPhone, setCustomPhone] = useState('');
  const [textInput, setTextInput] = useState('');
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const feedEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, interimText]);

  // Waveform visualization loop
  useEffect(() => {
    if (!isCalling || !analyser || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    let animId: number;

    const renderWave = () => {
      animId = requestAnimationFrame(renderWave);
      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const barWidth = (canvas.width / dataArray.length) * 2;
      let x = 0;

      for (let i = 0; i < dataArray.length; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height;
        ctx.fillStyle = isAgentSpeaking ? '#0284c7' : '#0d9488';
        ctx.fillRect(x, canvas.height - barHeight, barWidth - 1, barHeight);
        x += barWidth;
      }
    };

    renderWave();
    return () => {
      cancelAnimationFrame(animId);
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    };
  }, [isCalling, analyser, isAgentSpeaking]);

  const handleToggleCall = () => {
    if (isCalling) {
      endCall();
    } else {
      const activePhone = selectedCallerPhone === 'custom' ? customPhone.trim() : selectedCallerPhone;
      startCall(activePhone);
    }
  };

  const handleSendText = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) {
      sendTextMessage(textInput);
      setTextInput('');
    }
  };

  return (
    <div className="voice-console-grid">
      {/* Left Control Card */}
      <div className="voice-control-card">
        <div style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ShieldCheck size={20} color="#0d9488" />
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Aura Voice AI Caller</h2>
        </div>

        <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginBottom: '1.25rem', maxWidth: '340px' }}>
          Real-time full-duplex conversational voice agent with zero-latency RMS energy barge-in and instant Caller ID auto-lookup.
        </p>

        {/* Caller ID Auto-Lookup Selector */}
        <div style={{ width: '100%', marginBottom: '1.25rem', textAlign: 'left' }}>
          <label style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
            Simulate Incoming Caller ID (ANI):
          </label>
          <select
            className="form-input"
            value={selectedCallerPhone}
            onChange={(e) => setSelectedCallerPhone(e.target.value)}
            disabled={isCalling}
            style={{ fontSize: '0.8rem', padding: '0.45rem 0.65rem' }}
          >
            {PRESET_CALLERS.map((c, i) => (
              <option key={i} value={c.phone}>
                {c.label}
              </option>
            ))}
            <option value="custom">Custom Phone Number...</option>
          </select>

          {selectedCallerPhone === 'custom' && (
            <input
              type="text"
              className="form-input"
              placeholder="e.g. +91-98765-43210"
              value={customPhone}
              onChange={(e) => setCustomPhone(e.target.value)}
              disabled={isCalling}
              style={{ marginTop: '0.5rem', fontSize: '0.8rem', padding: '0.4rem 0.6rem' }}
            />
          )}
        </div>

        {/* Recognized Patient Badge */}
        {recognizedPatient && (
          <div
            style={{
              width: '100%',
              background: '#f0fdf4',
              border: '1px solid #bbf7d0',
              borderRadius: '8px',
              padding: '0.6rem 0.75rem',
              marginBottom: '1rem',
              textAlign: 'left',
              fontSize: '0.78rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#166534', fontWeight: 600, marginBottom: '2px' }}>
              <UserCheck size={14} /> Verified Caller Identity (200ms Handshake)
            </div>
            <div style={{ color: '#15803d' }}>
              <strong>{recognizedPatient.name}</strong> (MRN: {recognizedPatient.patient_id})
            </div>
            {recognizedPatient.upcoming_doctor && (
              <div style={{ color: '#166534', fontSize: '0.74rem', marginTop: '2px' }}>
                Upcoming: {recognizedPatient.upcoming_doctor} ({recognizedPatient.appointment_date})
              </div>
            )}
          </div>
        )}

        <button
          className={`voice-circle-btn ${isCalling ? 'calling' : ''}`}
          onClick={handleToggleCall}
          title={isCalling ? 'Hangup Call' : 'Start Voice Call'}
        >
          {isCalling ? <PhoneOff size={38} /> : <PhoneCall size={38} />}
        </button>

        <div style={{ fontWeight: 600, fontSize: '0.95rem', marginTop: '0.5rem', marginBottom: '0.25rem' }}>
          {isCalling ? 'Call Active (Full Duplex 16kHz)' : 'Click to Start Voice Call'}
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
          {status}
        </div>

        {/* Live Audio Waveform Canvas */}
        <canvas ref={canvasRef} className="waveform-canvas" width={320} height={50} />

        {/* Barge-in status & controls */}
        {isCalling && (
          <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.4rem' }}>
            {isAgentSpeaking ? (
              <>
                <div style={{ fontSize: '0.76rem', color: '#0284c7', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
                  <Zap size={13} color="#0284c7" /> Aura Speaking — Speak to Barge-in
                </div>
                <button className="btn-danger" onClick={stopPlayback} title="Barge-in Interrupt">
                  <VolumeX size={14} style={{ marginRight: '4px' }} /> Interrupt Aura
                </button>
              </>
            ) : (
              <div style={{ fontSize: '0.76rem', color: 'var(--teal-600)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Mic size={14} /> Listening for speech...
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right Conversation Feed */}
      <div className="med-card" style={{ display: 'flex', flexDirection: 'column', height: '100%', margin: 0 }}>
        <div className="med-card-header" style={{ marginBottom: '0.75rem' }}>
          <div className="med-card-title">
            <Sparkles size={18} color="#0d9488" />
            <span>Real-time Conversation Stream</span>
          </div>
          <span className="badge badge-confirmed">
            {messages.length} Messages
          </span>
        </div>

        <div className="transcript-feed">
          {messages.length === 0 && !interimText && (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)', margin: 'auto', padding: '2rem' }}>
              No messages yet. Select an incoming Caller ID and click "Start Voice Call" to hear Aura's instant personalized greeting.
            </div>
          )}

          {messages.map((m) => (
            <div key={m.id} className={`chat-bubble ${m.sender}`}>
              <div style={{ fontWeight: 600, fontSize: '0.75rem', marginBottom: '0.2rem', opacity: 0.8 }}>
                {m.sender === 'caller' ? 'You (Caller)' : 'Aura (MedFront Receptionist)'}
              </div>
              <div>{m.text}</div>
              <div className="chat-meta">
                {m.tool && <span>⚙️ {m.tool}</span>}
                {m.intent && <span>🎯 {m.intent}</span>}
                <span>{m.timestamp}</span>
              </div>
            </div>
          ))}

          {interimText && (
            <div className="chat-bubble caller" style={{ opacity: 0.8, fontStyle: 'italic', borderLeft: '3px solid #0d9488' }}>
              <div style={{ fontSize: '0.72rem', marginBottom: '0.2rem' }}>Transcribing (Interim Hypotheses)...</div>
              <div>{interimText}</div>
            </div>
          )}

          <div ref={feedEndRef} />
        </div>

        {/* Text prompt fallback form */}
        <form onSubmit={handleSendText} style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
          <input
            type="text"
            className="form-input"
            placeholder={isCalling ? "Type prompt to Aura (e.g. 'Dr. Vikram Sen knee pain')..." : "Start call to enable prompt..."}
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            disabled={!isCalling}
          />
          <button type="submit" className="btn-primary" disabled={!isCalling || !textInput.trim()}>
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
};
