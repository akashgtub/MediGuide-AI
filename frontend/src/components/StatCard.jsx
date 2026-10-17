import { TrendingUp, TrendingDown } from 'lucide-react';

const colorStyles = {
  teal: {
    bg: 'bg-teal-50',
    text: 'text-teal-600',
    border: 'border-teal-100',
    dot: 'bg-teal-500',
    trend: 'text-teal-700 bg-teal-50',
  },
  blue: {
    bg: 'bg-blue-50',
    text: 'text-blue-600',
    border: 'border-blue-100',
    dot: 'bg-blue-500',
    trend: 'text-blue-700 bg-blue-50',
  },
  amber: {
    bg: 'bg-amber-50',
    text: 'text-amber-600',
    border: 'border-amber-100',
    dot: 'bg-amber-500',
    trend: 'text-amber-700 bg-amber-50',
  },
  red: {
    bg: 'bg-rose-50',
    text: 'text-rose-600',
    border: 'border-rose-100',
    dot: 'bg-rose-500',
    trend: 'text-rose-700 bg-rose-50',
  },
  indigo: {
    bg: 'bg-indigo-50',
    text: 'text-indigo-600',
    border: 'border-indigo-100',
    dot: 'bg-indigo-500',
    trend: 'text-indigo-700 bg-indigo-50',
  },
};

const StatCard = ({ title, value, icon, color = 'teal', trend, trendUp = true, subtitle }) => {
  const current = colorStyles[color] || colorStyles.teal;

  return (
    <div className="bg-white rounded-2xl p-5 border border-[#E5EDF5] shadow-card hover:shadow-card-hover transition-all duration-200 group">
      <div className="flex items-center justify-between mb-3">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${current.bg} ${current.text} border ${current.border} transition-transform group-hover:scale-105 duration-200`}>
          {icon}
        </div>
        {trend && (
          <span className={`inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-full ${trendUp ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
            {trendUp ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
            {trend}
          </span>
        )}
      </div>
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">{title}</p>
        <div className="flex items-baseline space-x-2">
          <p className="text-2xl lg:text-3xl font-extrabold text-[#172033] tracking-tight">{value}</p>
          {subtitle && <span className="text-xs text-slate-400 font-medium">{subtitle}</span>}
        </div>
      </div>
    </div>
  );
};

export default StatCard;
