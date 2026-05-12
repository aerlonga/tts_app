import { useState } from 'react';
import { getErrorMessage, resolveApiUrl } from '@/api/client';
import type { StreamProgress, TtsLogItem } from '@/types/media';
import { fileFromBase64 } from '@/lib/utils';

interface StreamPayload {
  text: string;
  voice: string;
  session_id?: string | null;
}

function toLog(level: TtsLogItem['level'], message: string): TtsLogItem {
  return {
    id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    level,
    message,
  };
}

export function useSSE() {
  const [logs, setLogs] = useState<TtsLogItem[]>([]);
  const [progress, setProgress] = useState<StreamProgress>({
    current: 0,
    total: 0,
    label: 'Aguardando',
  });
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  async function runStream(payload: StreamPayload) {
    setLogs([]);
    setProgress({ current: 0, total: 0, label: 'Conectando ao stream...' });
    setIsStreaming(true);

    try {
      const response = await fetch(resolveApiUrl('/media/generate-tts-stream'), {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Falha ao iniciar TTS streaming.');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Stream indisponível no navegador.');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let audioFile: File | null = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const rawLine of lines) {
          const line = rawLine.startsWith('data: ') ? rawLine.slice(6) : rawLine;
          if (!line.trim()) {
            continue;
          }

          let event: Record<string, unknown>;
          try {
            event = JSON.parse(line);
          } catch {
            continue;
          }

          if (event.type === 'session') {
            const nextSessionId = String(event.session_id || '');
            setSessionId(nextSessionId || null);
            setLogs((current) => [...current, toLog('info', `Sessão ${nextSessionId.slice(0, 8)} iniciada.`)]);
            continue;
          }

          if (event.type === 'skipped') {
            const chunk = Number(event.chunk || 0);
            const total = Number(event.total || chunk || 0);
            setProgress({
              current: chunk,
              total,
              label: `Chunk ${chunk} recuperado do cache`,
            });
            setLogs((current) => [...current, toLog('ok', `Chunk ${chunk}/${total} recuperado do cache.`)]);
            continue;
          }

          if (event.type === 'progress') {
            const currentChunk = Number(event.current || 0);
            const total = Number(event.total || 0);
            setProgress({
              current: currentChunk,
              total,
              label: `Processando chunk ${currentChunk} de ${total}`,
            });
            setLogs((current) => [
              ...current,
              toLog('ok', `Chunk ${currentChunk}/${total}: ${String(event.preview || '').trim()}`),
            ]);
            continue;
          }

          if (event.type === 'waiting') {
            const chunk = Number(event.chunk || 0);
            const total = Number(event.total || chunk || 0);
            const seconds = Number(event.seconds || 0);
            setProgress({
              current: chunk,
              total,
              label: `Aguardando quota da API por ${seconds}s`,
            });
            setLogs((current) => [
              ...current,
              toLog('warn', `Chunk ${chunk}/${total}: aguardando quota por ${seconds}s.`),
            ]);
            continue;
          }

          if (event.type === 'error') {
            setLogs((current) => [
              ...current,
              toLog('error', `Chunk ${String(event.chunk || '?')}: ${String(event.message || 'erro')}`),
            ]);
            continue;
          }

          if (event.type === 'done') {
            const chunksProcessed = Number(event.chunks_processed || 1);
            setProgress({
              current: chunksProcessed,
              total: chunksProcessed,
              label: 'Finalizado',
            });
            setSessionId(null);
            setLogs((current) => [...current, toLog('ok', `${chunksProcessed} chunks processados com sucesso.`)]);
            audioFile = fileFromBase64(
              String(event.audio_b64 || ''),
              `narration_${payload.voice.toLowerCase()}.wav`,
              'audio/wav',
            );
          }
        }
      }

      if (!audioFile) {
        throw new Error('Nenhum áudio foi retornado pelo backend.');
      }

      return audioFile;
    } catch (error) {
      const message = getErrorMessage(error, 'Falha no stream TTS.');
      setLogs((current) => [...current, toLog('error', message)]);
      throw new Error(message);
    } finally {
      setIsStreaming(false);
    }
  }

  return {
    isStreaming,
    logs,
    progress,
    sessionId,
    runStream,
  };
}
