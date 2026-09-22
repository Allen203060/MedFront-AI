import { useCallback, useEffect, useRef, useState } from 'react';
import type { RecognizedPatient, VoiceMessage } from '../types';
import { decodeAudioPayload, downsampleTo16kHz, floatTo16BitPCM } from '../services/audioUtils';

export function useVoiceConsole(onAppointmentBooked?: () => void) {
  const [isCalling, setIsCalling] = useState(false);
  const [status, setStatus] = useState('Idle. Ready to connect.');
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  const [interimText, setInterimText] = useState('');
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [recognizedPatient, setRecognizedPatient] = useState<RecognizedPatient | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);

  const stopPlayback = useCallback(() => {
    if (currentSourceRef.current) {
      try {
        currentSourceRef.current.stop();
        currentSourceRef.current.disconnect();
      } catch {
        // Ignored
      }
      currentSourceRef.current = null;
    }
    setIsAgentSpeaking(false);
  }, []);

  const toggleMute = useCallback(() => {
    setIsMuted(prev => {
      const next = !prev;
      if (micStreamRef.current) {
        const audioTrack = micStreamRef.current.getAudioTracks()[0];
        if (audioTrack) {
          audioTrack.enabled = !next;
        }
      }
      return next;
    });
  }, []);

  const endCall = useCallback(() => {
    setIsCalling(false);
    stopPlayback();

    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch {
        // Ignored
      }
      wsRef.current = null;
    }

    if (processorRef.current) {
      try {
        processorRef.current.disconnect();
      } catch {
        // Ignored
      }
      processorRef.current = null;
    }

    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((t) => t.stop());
      micStreamRef.current = null;
    }

    setStatus('Call ended. Ready to reconnect.');
    setInterimText('');
    setRecognizedPatient(null);
    setIsMuted(false);
  }, [stopPlayback]);

  const playAudioChunk = useCallback(
    async (base64Audio: string) => {
      if (!audioCtxRef.current) return;
      try {
        stopPlayback();
        const buffer = await decodeAudioPayload(audioCtxRef.current, base64Audio);
        const source = audioCtxRef.current.createBufferSource();
        source.buffer = buffer;
        source.connect(audioCtxRef.current.destination);

        source.onended = () => {
          if (currentSourceRef.current === source) {
            currentSourceRef.current = null;
            setIsAgentSpeaking(false);
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
              wsRef.current.send(JSON.stringify({ event: 'playback_end', type: 'playback_end' }));
            }
          }
        };

        currentSourceRef.current = source;
        setIsAgentSpeaking(true);

        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ event: 'playback_start', type: 'playback_start' }));
        }

        source.start(0);
      } catch (err) {
        console.error('Failed to play audio chunk:', err);
      }
    },
    [stopPlayback]
  );

  const startCall = useCallback(
    async (callerId?: string) => {
      try {
        setStatus('Requesting microphone permission...');
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });
        micStreamRef.current = stream;

        // Initialize or resume shared AudioContext
        const AudioCtx =
          window.AudioContext ||
          (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        const ctx = audioCtxRef.current || new AudioCtx();
        if (ctx.state === 'suspended') {
          await ctx.resume();
        }
        audioCtxRef.current = ctx;

        // Connect WebSocket with optional Caller ID ANI query param
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const queryParam = callerId ? `?caller_id=${encodeURIComponent(callerId)}` : '';
        const wsUrl = `${protocol}//${host}/api/telephony/ws/audio-stream${queryParam}`;

        setStatus(
          callerId
            ? `Connecting with Caller ID: ${callerId}...`
            : 'Connecting to Aura Realtime Voice Engine...'
        );
        const ws = new WebSocket(wsUrl);
        ws.binaryType = 'arraybuffer';
        wsRef.current = ws;

        ws.onopen = () => {
          setStatus('🟢 Connected. Listening... Speak naturally.');
          setIsCalling(true);
        };

        ws.onmessage = async (e) => {
          if (typeof e.data === 'string') {
            try {
              const data = JSON.parse(e.data);
              const eventType = data.type || data.event;

              // 1. Instant Barge-In from server
              if (eventType === 'interrupt') {
                stopPlayback();
                return;
              }

              // 2. Real-time Interim hypothesis
              if (eventType === 'interim') {
                stopPlayback();
                setInterimText(data.text || '');
                return;
              }

              // 3. Finalized User Speech Turn
              if (eventType === 'transcript' || eventType === 'final' || data.event === 'user') {
                stopPlayback();
                setInterimText('');
                const callerText = data.text || data.transcript || '';
                if (callerText) {
                  setMessages((prev) => [
                    ...prev,
                    {
                      id: Math.random().toString(),
                      sender: 'caller',
                      text: callerText,
                      timestamp: new Date().toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      }),
                    },
                  ]);
                }
                return;
              }

              // 4. Assistant Speech / Greeting / Tool Execution
              if (
                eventType === 'response' ||
                eventType === 'assistant' ||
                data.event === 'assistant'
              ) {
                if (data.recognized_patient) {
                  setRecognizedPatient(data.recognized_patient);
                }

                const auraText = data.text || data.reply || '';
                if (auraText) {
                  setMessages((prev) => [
                    ...prev,
                    {
                      id: Math.random().toString(),
                      sender: 'aura',
                      text: auraText,
                      timestamp: new Date().toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      }),
                      intent: data.intent,
                      tool: data.tool || data.tool_used,
                    },
                  ]);
                }

                const audioPayload = data.audio || data.data;
                if (audioPayload) {
                  await playAudioChunk(audioPayload);
                }

                if (
                  (data.tool === 'book_appointment' || data.tool_used === 'book_appointment') &&
                  onAppointmentBooked
                ) {
                  onAppointmentBooked();
                }
                return;
              }

              // 5. Raw direct TTS Audio buffer chunk
              if (eventType === 'audio') {
                const audioPayload = data.data || data.audio;
                if (audioPayload) {
                  await playAudioChunk(audioPayload);
                }
                return;
              }
            } catch (err) {
              console.warn('Error parsing message from voice engine:', err);
            }
          }
        };

        ws.onerror = (err) => {
          console.error('Voice WebSocket error:', err);
          setStatus('WebSocket connection error.');
        };

        ws.onclose = () => {
          endCall();
        };

        // Connect mic to AudioWorklet / ScriptProcessor for 16kHz PCM stream
        const sourceNode = ctx.createMediaStreamSource(stream);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 64;
        sourceNode.connect(analyser);
        analyserRef.current = analyser;

        const processor = ctx.createScriptProcessor(4096, 1, 1);
        const muteGain = ctx.createGain();
        muteGain.gain.value = 0; // Prevent mic looping back to local speakers

        processor.onaudioprocess = (evt) => {
          if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
          const inputData = evt.inputBuffer.getChannelData(0);

          // Send continuous 16kHz PCM stream to the backend
          // (Barge-in will now rely exclusively on the server's semantic 'interim' transcription events)

          const downsampled = downsampleTo16kHz(inputData, ctx.sampleRate);
          const pcm16 = floatTo16BitPCM(downsampled);
          wsRef.current.send(pcm16);
        };

        sourceNode.connect(processor);
        processor.connect(muteGain);
        muteGain.connect(ctx.destination);
        processorRef.current = processor;
      } catch (err) {
        console.error('Failed to start voice call:', err);
        setStatus(`Failed to start call: ${(err as Error).message}`);
        endCall();
      }
    },
    [endCall, onAppointmentBooked, playAudioChunk, stopPlayback]
  );

  const sendTextMessage = useCallback((text: string) => {
    if (!text.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    setMessages((prev) => [
      ...prev,
      {
        id: Math.random().toString(),
        sender: 'caller',
        text: text.trim(),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
    wsRef.current.send(JSON.stringify({ event: 'prompt', text: text.trim() }));
  }, []);

  useEffect(() => {
    return () => {
      endCall();
    };
  }, [endCall]);

  return {
    isCalling,
    status,
    messages,
    interimText,
    isAgentSpeaking,
    recognizedPatient,
    analyser: analyserRef.current,
    isMuted,
    toggleMute,
    startCall,
    endCall,
    sendTextMessage,
    stopPlayback,
  };
}
