import { Upload } from 'lucide-react';

interface FileUploadProps {
  onFiles: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  title: string;
  description: string;
}

export function FileUpload({ onFiles, accept, multiple = true, title, description }: FileUploadProps) {
  return (
    <label className="flex cursor-pointer flex-col items-center justify-center rounded-[28px] border border-dashed border-[var(--border2)] bg-[var(--bg2)]/50 px-6 py-8 text-center transition hover:border-[var(--amber)] hover:bg-[var(--amber)]/5">
      <Upload className="h-7 w-7 text-[var(--amber)]" />
      <p className="mt-4 font-display text-2xl uppercase tracking-[0.12em] text-[var(--text)]">{title}</p>
      <p className="mt-2 max-w-xl text-sm text-[var(--text2)]">{description}</p>
      <span className="mt-4 rounded-full border border-[var(--border2)] px-4 py-2 text-xs uppercase tracking-[0.28em] text-[var(--text2)]">
        Selecionar arquivos
      </span>
      <input
        type="file"
        accept={accept}
        multiple={multiple}
        className="hidden"
        onChange={(event) => {
          const files = Array.from(event.target.files || []);
          if (files.length) {
            onFiles(files);
          }
          event.currentTarget.value = '';
        }}
      />
    </label>
  );
}
