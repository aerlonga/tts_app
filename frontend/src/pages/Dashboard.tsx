import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getHealthDetails } from '@/api/health';
import { getUsageSummary } from '@/api/usage';
import { Loading } from '@/components/common/Loading';
import { formatCurrency } from '@/lib/utils';

const quickLinks = [
  { to: '/scripts', label: 'Gerar roteiro', description: 'Começar a partir de uma URL' },
  { to: '/tts', label: 'TTS streaming', description: 'Gerar narração com SSE' },
  { to: '/assembly', label: 'Montar vídeo', description: 'Assets + áudio + polling' },
  { to: '/shorts', label: 'Gerar shorts', description: 'Cards com production_pack' },
];

export function Dashboard() {
  const healthQuery = useQuery({
    queryKey: ['health-details'],
    queryFn: getHealthDetails,
  });
  const usageQuery = useQuery({
    queryKey: ['usage-summary'],
    queryFn: () => getUsageSummary(),
  });

  if (healthQuery.isLoading || usageQuery.isLoading) {
    return <Loading label="Carregando visão geral do backend..." />;
  }

  const health = healthQuery.data;
  const usage = usageQuery.data;

  return (
    <section className="space-y-6">
      <div className="grid gap-4 xl:grid-cols-4">
        <div className="rounded-[28px] border border-[var(--border)] bg-[var(--bg2)] p-5">
          <p className="text-xs uppercase tracking-[0.28em] text-[var(--text3)]">Health</p>
          <p className="mt-3 font-display text-4xl uppercase tracking-[0.08em] text-[var(--text)]">{health?.status || 'n/a'}</p>
          <p className="mt-2 text-sm text-[var(--text2)]">FFmpeg {health?.ffmpeg_available ? 'disponível' : 'ausente'}</p>
        </div>
        <div className="rounded-[28px] border border-[var(--border)] bg-[var(--bg2)] p-5">
          <p className="text-xs uppercase tracking-[0.28em] text-[var(--text3)]">Banco</p>
          <p className="mt-3 font-display text-4xl uppercase tracking-[0.08em] text-[var(--text)]">
            {health?.database_reachable ? 'OK' : 'FAIL'}
          </p>
          <p className="mt-2 text-sm text-[var(--text2)]">{health?.python_version}</p>
        </div>
        <div className="rounded-[28px] border border-[var(--border)] bg-[var(--bg2)] p-5">
          <p className="text-xs uppercase tracking-[0.28em] text-[var(--text3)]">Custo IA</p>
          <p className="mt-3 font-display text-4xl uppercase tracking-[0.08em] text-[var(--text)]">
            {formatCurrency(usage?.total_estimated_cost_usd || 0)}
          </p>
          <p className="mt-2 text-sm text-[var(--text2)]">{usage?.total_calls || 0} chamadas registradas</p>
        </div>
        <div className="rounded-[28px] border border-[var(--border)] bg-[var(--bg2)] p-5">
          <p className="text-xs uppercase tracking-[0.28em] text-[var(--text3)]">Projeção</p>
          <p className="mt-3 font-display text-4xl uppercase tracking-[0.08em] text-[var(--text)]">
            {formatCurrency(usage?.projected_monthly_cost_usd || 0)}
          </p>
          <p className="mt-2 text-sm text-[var(--text2)]">{usage?.active_days || 0} dias ativos</p>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
        <div className="rounded-[32px] border border-[var(--border)] bg-[linear-gradient(180deg,rgba(14,16,20,0.96),rgba(8,10,12,0.96))] p-6">
          <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">Quick Links</p>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {quickLinks.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="rounded-[24px] border border-[var(--border2)] bg-[var(--bg3)]/50 p-5 transition hover:border-[var(--amber)] hover:bg-[var(--amber)]/6"
              >
                <p className="font-display text-2xl uppercase tracking-[0.08em] text-[var(--text)]">{item.label}</p>
                <p className="mt-2 text-sm text-[var(--text2)]">{item.description}</p>
              </Link>
            ))}
          </div>
        </div>

        <div className="rounded-[32px] border border-[var(--border)] bg-[var(--bg2)] p-6">
          <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">Serviços Externos</p>
          <div className="mt-5 space-y-3">
            {health?.external_services.map((service) => (
              <div key={service.name} className="rounded-2xl border border-[var(--border)] bg-[var(--bg3)]/60 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-[var(--text)]">{service.name}</p>
                  <span className={`rounded-full px-3 py-1 text-xs uppercase tracking-[0.22em] ${service.configured ? 'bg-[var(--green)]/12 text-[var(--green)]' : 'bg-[var(--red)]/12 text-[var(--red)]'}`}>
                    {service.configured ? 'Configurado' : 'Pendente'}
                  </span>
                </div>
                <p className="mt-2 text-sm text-[var(--text2)]">{service.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
