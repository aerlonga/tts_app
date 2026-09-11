export interface VoiceOption {
  id: string;
  label: string;
  desc: string;
}

export const VOICES: VoiceOption[] = [
  {
    id: 'Charon',
    label: 'Charon',
    desc: 'Narração firme e grave para documentários e explicações densas.',
  },
  {
    id: 'Kore',
    label: 'Kore',
    desc: 'Voz clara e direta, boa para tutoriais e conteúdo informativo.',
  },
  {
    id: 'Puck',
    label: 'Puck',
    desc: 'Entrega mais leve e expressiva para vídeos curtos e dinâmicos.',
  },
  {
    id: 'Fenrir',
    label: 'Fenrir',
    desc: 'Tom intenso e cinematográfico para hooks e histórias dramáticas.',
  },
  {
    id: 'Aoede',
    label: 'Aoede',
    desc: 'Voz suave e natural para leituras longas e narração emocional.',
  },
  {
    id: 'Leda',
    label: 'Leda',
    desc: 'Presença equilibrada para apresentações, resumos e locuções neutras.',
  },
  {
    id: 'Umbriel',
    label: 'Umbriel',
    desc: 'Tom denso e investigativo, perfeito para mistérios e revelações de arquivos confidenciais.', // Ajuste a descrição como preferir
  },
];
