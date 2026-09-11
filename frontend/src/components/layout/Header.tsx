import { Link } from 'react-router-dom';
import { CheckCircle2, KeyRound, Languages, Mic2, Settings2, Wand2 } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';

interface HeaderProps {
  authenticated: boolean;
}

export function Header({ authenticated }: HeaderProps) {
  const selectedVoice = useAppStore((state) => state.selectedVoice);
  const hasAudio = useAppStore((state) => Boolean(state.generatedAudio));
  const language = useAppStore((state) => state.language);
  const setLanguage = useAppStore((state) => state.setLanguage);
  const videoStyle = useAppStore((state) => state.videoStyle);
  const setVideoStyle = useAppStore((state) => state.setVideoStyle);

  function toggleLanguage() {
    setLanguage(language === 'pt' ? 'en' : 'pt');
  }

  function toggleVideoStyle() {
    setVideoStyle(videoStyle === 'cinematic' ? 'stickfigure' : 'cinematic');
  }

  return (
    <header className="mb-8 flex flex-col gap-4 rounded-[28px] border border-[var(--border)] bg-[linear-gradient(135deg,rgba(20,23,32,0.96),rgba(8,10,12,0.96))] px-5 py-5 md:flex-row md:items-center md:justify-between">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-[var(--amber)]">React + Vite / FastAPI</p>
        <h2 className="mt-2 font-display text-4xl uppercase tracking-[0.08em] text-[var(--text)]">Frontend Cinemático</h2>
      </div>

      <div className="flex flex-wrap items-center gap-3 text-sm">
        <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border2)] bg-[var(--bg2)] px-4 py-2 text-[var(--text2)]">
          <KeyRound className="h-4 w-4 text-[var(--amber)]" />
          Sessão {authenticated ? 'ativa' : 'inativa'}
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border2)] bg-[var(--bg2)] px-4 py-2 text-[var(--text2)]">
          <Mic2 className="h-4 w-4 text-[var(--blue)]" />
          Voz {selectedVoice}
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border2)] bg-[var(--bg2)] px-4 py-2 text-[var(--text2)]">
          <CheckCircle2 className={`h-4 w-4 ${hasAudio ? 'text-[var(--green)]' : 'text-[var(--text3)]'}`} />
          Áudio {hasAudio ? 'pronto' : 'pendente'}
        </div>

        {/* Language toggle */}
        <button
          id="header-language-toggle"
          type="button"
          onClick={toggleLanguage}
          title={language === 'pt' ? 'Mudar para English' : 'Mudar para Português'}
          className="inline-flex items-center gap-2 rounded-full border border-[var(--border2)] bg-[var(--bg2)] px-4 py-2 text-[var(--text2)] transition hover:border-[var(--amber)] hover:text-[var(--amber)]"
        >
          <Languages className="h-4 w-4" />
          <span className="font-semibold tracking-wide">
            {language === 'pt' ? 'PT' : 'EN'}
          </span>
        </button>

        {/* Video style toggle */}
        <button
          id="header-style-toggle"
          type="button"
          onClick={toggleVideoStyle}
          title={videoStyle === 'cinematic' ? 'Mudar para Stick Figure' : 'Mudar para Cinemático'}
          className="inline-flex items-center gap-2 rounded-full border border-[var(--border2)] bg-[var(--bg2)] px-4 py-2 text-[var(--text2)] transition hover:border-[var(--amber)] hover:text-[var(--amber)]"
        >
          <Wand2 className="h-4 w-4" />
          <span className="font-semibold tracking-wide">
            {videoStyle === 'cinematic' ? 'Cinemático' : 'Stick Figure'}
          </span>
        </button>

        <Link
          to="/settings"
          className="inline-flex items-center gap-2 rounded-full border border-[var(--amber)] bg-[var(--amber)]/10 px-4 py-2 text-[var(--amber)] transition hover:bg-[var(--amber)]/20"
        >
          <Settings2 className="h-4 w-4" />
          Settings
        </Link>
      </div>
    </header>
  );
}
