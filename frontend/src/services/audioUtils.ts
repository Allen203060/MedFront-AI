export function downsampleTo16kHz(buffer: Float32Array, inputSampleRate: number): Float32Array {
  if (inputSampleRate === 16000) return buffer;
  const ratio = inputSampleRate / 16000;
  const newLength = Math.round(buffer.length / ratio);
  const result = new Float32Array(newLength);
  let offsetResult = 0;
  let offsetBuffer = 0;

  while (offsetResult < result.length) {
    const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
    let accum = 0;
    let count = 0;
    for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
      accum += buffer[i];
      count++;
    }
    result[offsetResult] = count > 0 ? accum / count : buffer[offsetBuffer];
    offsetResult++;
    offsetBuffer = nextOffsetBuffer;
  }
  return result;
}

export function floatTo16BitPCM(input: Float32Array): ArrayBuffer {
  const pcm16 = new Int16Array(input.length);
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i]));
    pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return pcm16.buffer;
}

export async function decodeAudioPayload(
  audioCtx: AudioContext,
  base64Audio: string
): Promise<AudioBuffer> {
  const binaryString = window.atob(base64Audio);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }

  // Check for RIFF header
  const isRiffWav =
    bytes.length >= 4 &&
    bytes[0] === 0x52 && // 'R'
    bytes[1] === 0x49 && // 'I'
    bytes[2] === 0x46 && // 'F'
    bytes[3] === 0x46; // 'F'

  if (isRiffWav) {
    try {
      return await audioCtx.decodeAudioData(bytes.buffer.slice(0));
    } catch {
      // Fall through to manual PCM
    }
  }

  // Fallback: 16kHz 16-bit Mono PCM
  const headerOffset = isRiffWav && bytes.length > 44 ? 44 : 0;
  const dataBytes = bytes.subarray(headerOffset);
  const sampleCount = Math.floor(dataBytes.length / 2);
  const audioBuffer = audioCtx.createBuffer(1, sampleCount, 16000);
  const channelData = audioBuffer.getChannelData(0);
  const dataView = new DataView(dataBytes.buffer, dataBytes.byteOffset, dataBytes.byteLength);

  for (let i = 0; i < sampleCount; i++) {
    const int16 = dataView.getInt16(i * 2, true);
    channelData[i] = int16 < 0 ? int16 / 0x8000 : int16 / 0x7fff;
  }

  return audioBuffer;
}
