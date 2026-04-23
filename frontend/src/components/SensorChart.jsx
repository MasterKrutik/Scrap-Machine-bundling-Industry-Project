import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';

// Neo-Brutalist Tooltip
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        backgroundColor: '#ffffff',
        border: '2px solid #000000',
        padding: '12px 16px',
        borderRadius: '6px',
        boxShadow: '4px 4px 0px 0px #000000',
        color: '#171e19'
      }}>
        <p style={{ margin: 0, fontWeight: 700, borderBottom: '2px solid #e4e4e7', paddingBottom: '6px', marginBottom: '8px', color: '#171e19', fontSize: '0.85rem', fontFamily: 'Space Grotesk, sans-serif' }}>{label}</p>
        {payload.map((entry, index) => (
          <p key={index} style={{ margin: '4px 0', color: '#52524e', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'DM Sans, sans-serif' }}>
            <span style={{width: 10, height: 10, borderRadius: '2px', backgroundColor: entry.color, display: 'inline-block', border: '1px solid #000'}}></span>
            {entry.name}: <span style={{fontWeight: 700, color: '#171e19'}}>{entry.value}</span>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const GRID_STROKE = '#e4e4e7';
const AXIS_STROKE = '#e4e4e7';
const TICK_STYLE = { fill: '#8a8a85', fontSize: 11, fontWeight: 600, fontFamily: 'Space Grotesk, sans-serif' };

export function SensorBarChart({ data, dataKey, name, color }) {
  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
          <XAxis dataKey="name" stroke={AXIS_STROKE} tick={TICK_STYLE} axisLine={{ stroke: '#000', strokeWidth: 2 }} />
          <YAxis stroke={AXIS_STROKE} tick={TICK_STYLE} axisLine={{ stroke: '#000', strokeWidth: 2 }} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255, 225, 124, 0.15)' }} />
          <Legend wrapperStyle={{ paddingTop: '20px', fontSize: '0.8rem', fontFamily: 'DM Sans, sans-serif' }} />
          <Bar dataKey={dataKey} name={name} fill={color} radius={[4, 4, 0, 0]} barSize={36} stroke="#000" strokeWidth={1} />
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
          <XAxis dataKey="timestamp" stroke={AXIS_STROKE} tick={TICK_STYLE} axisLine={{ stroke: '#000', strokeWidth: 2 }} />
          <YAxis stroke={AXIS_STROKE} tick={TICK_STYLE} axisLine={{ stroke: '#000', strokeWidth: 2 }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ paddingTop: '20px', fontSize: '0.8rem', fontFamily: 'DM Sans, sans-serif' }} />
          {lines.map((line, index) => (
            <Line
              key={index}
              type="monotone"
              dataKey={line.dataKey}
              name={line.name}
              stroke={line.color}
              strokeWidth={3}
              activeDot={{ r: 6, strokeWidth: 2, stroke: '#000', fill: line.color }}
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
              <stop offset="5%" stopColor={color} stopOpacity={0.35}/>
              <stop offset="95%" stopColor={color} stopOpacity={0.02}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={GRID_STROKE} vertical={false} />
          <XAxis dataKey="name" stroke={AXIS_STROKE} tick={TICK_STYLE} axisLine={{ stroke: '#000', strokeWidth: 2 }} />
          <YAxis stroke={AXIS_STROKE} tick={TICK_STYLE} axisLine={{ stroke: '#000', strokeWidth: 2 }} />
          <Tooltip content={<CustomTooltip />} />
          <Area type="monotone" dataKey={dataKey} name={name} stroke={color} strokeWidth={3} fillOpacity={1} fill={`url(#${gradientId})`} activeDot={{ r: 5, strokeWidth: 2, stroke: '#000', fill: color }} />
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
            innerRadius={60}
            outerRadius={100}
            paddingAngle={3}
            dataKey="value"
            stroke="#000"
            strokeWidth={2}
          >
            {data.map((entry, index) => (
               <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="bottom"
            height={36}
            iconType="square"
            wrapperStyle={{ fontSize: '0.8rem', fontFamily: 'DM Sans, sans-serif' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
