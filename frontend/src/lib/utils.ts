import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export async function copyToClipboard(text: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'fixed';
  textarea.style.left = '-9999px';
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand('copy');
  document.body.removeChild(textarea);
}

export function fileFromBase64(base64: string, filename: string, mimeType: string) {
  const binary = window.atob(base64);
  const bytes = new Uint8Array(binary.length);

  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }

  return new File([bytes], filename, { type: mimeType });
}

export function splitKeywords(value: string) {
  return value
    .split(/[,\n]/)
    .map((keyword) => keyword.trim())
    .filter(Boolean);
}

export function formatCurrency(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: value < 1 ? 4 : 2,
  }).format(value);
}

export function formatDuration(seconds: number) {
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return '0s';
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);

  if (!minutes) {
    return `${remainingSeconds}s`;
  }

  return `${minutes}m ${remainingSeconds.toString().padStart(2, '0')}s`;
}
