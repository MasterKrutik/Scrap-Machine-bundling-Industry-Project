import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';

// Custom Tooltip — Dark Glass Theme
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        backgroundColor: 'rgba(17, 24, 45, 0.95)',
        border: '1px solid rgba(99, 102, 241, 0.2)',
        padding: '12px 16px',
        borderRadius: '10px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4), 0 0 1px rgba(99, 102, 241, 0.3)',
        backdropFilter: 'blur(12px)',
        color: '#e2e8f0'
      }}>
        <p style={{ margin: 0, fontWeight: 600, borderBottom: '1px solid rgba(148, 163, 184, 0.1)', paddingBottom: '8px', marginBottom: '8px', color: '#f8fafc', fontSize: '0.85rem' }}>{label}</p>
        {payload.map((entry, index) => (
          <p key={index} style={{ margin: '4px 0', color: '#94a3b8', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{width: 8, height: 8, borderRadius: '50%', backgroundColor: entry.color, display: 'inline-block', boxShadow: `0 0 6px ${entry.color}`}}></span>
            {entry.name}: <span style={{fontWeight: 700, color: entry.color}}>{entry.value}</span>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const GRID_STROKE = 'rgba(148, 163, 184, 0.06)';
const AXIS_STROKE = 'rgba(148, 163, 184, 0.1)';
const TICK_STYLE = { fill: '#64748b', fontSize: 11, fontWeight: 500 };

export function SensorBarChart({ data, dataKey, name, color }) {
  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id={`barGrad-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.9}/>
              <stop offset="100%" stopColor={color} stopOpacity={0.4}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
          <XAxis dataKey="name" stroke={AXIS_STROKE} tick={TICK_STYLE} axisLine={{ stroke: AXIS_STROKE }} />
          <YAxis stroke={AXIS_STROKE} tick={TICK_STYLE} axisLine={{ stroke: AXIS_STROKE }} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99, 102, 241, 0.04)' }} />
          <Legend wrapperStyle={{ paddingTop: '20px', color: '#94a3b8', fontSize: '0.8rem' }} />
          <Bar dataKey={dataKey} name={name} fill={`url(#barGrad-${dataKey})`} radius={[6, 6, 0, 0]} barSize={36} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SensorLineChart({ data, lines }) {
  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
          <XAxis dataKey="timestamp" stroke={AXIS_STROKE} tick={TICK_STYLE} axisLine={{ stroke: AXIS_STROKE }} />
          <YAxis stroke={AXIS_STROKE} tick={TICK_STYLE} axisLine={{ stroke: AXIS_STROKE }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ paddingTop: '20px', color: '#94a3b8', fontSize: '0.8rem' }} />
          {lines.map((line, index) => (
            <Line
              key={index}
              type="monotone"
              dataKey={line.dataKey}
              name={line.name}
              stroke={line.color}
              strokeWidth={2.5}
              activeDot={{ r: 6, strokeWidth: 0, fill: line.color, style: { filter: `drop-shadow(0 0 6px ${line.color})` } }}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function AreaChartComponent({ data, dataKey, name, color }) {
  const gradientId = `areaGrad-${dataKey}-${color.replace('#', '')}`;
  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={color} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
          <XAxis dataKey="name" stroke={AXIS_STROKE} tick={TICK_STYLE} axisLine={{ stroke: AXIS_STROKE }} />
          <YAxis stroke={AXIS_STROKE} tick={TICK_STYLE} axisLine={{ stroke: AXIS_STROKE }} />
          <Tooltip content={<CustomTooltip />} />
          <Area type="monotone" dataKey={dataKey} name={name} stroke={color} strokeWidth={2.5} fillOpacity={1} fill={`url(#${gradientId})`} activeDot={{ r: 5, strokeWidth: 0, fill: color }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function StatusPieChart({ data }) {
  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={65}
            outerRadius={100}
            paddingAngle={4}
            dataKey="value"
            stroke="none"
          >
            {data.map((entry, index) => (
               <Cell key={`cell-${index}`} fill={entry.color} style={{ filter: `drop-shadow(0 0 6px ${entry.color}50)` }} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="bottom"
            height={36}
            iconType="circle"
            wrapperStyle={{ color: '#94a3b8', fontSize: '0.8rem' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
