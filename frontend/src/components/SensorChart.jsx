import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';

// Custom Tooltip style for Light Theme
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid #e2e8f0',
        padding: '12px',
        borderRadius: '8px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        color: '#0f172a'
      }}>
        <p style={{ margin: 0, fontWeight: 600, borderBottom: '1px solid #e2e8f0', paddingBottom: '6px', marginBottom: '6px' }}>{label}</p>
        {payload.map((entry, index) => (
          <p key={index} style={{ margin: 0, color: entry.color, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{width: 8, height: 8, borderRadius: '50%', backgroundColor: entry.color, display: 'inline-block'}}></span>
            {entry.name}: <span style={{fontWeight: 600, color: '#0f172a'}}>{entry.value}</span>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export function SensorBarChart({ data, dataKey, name, color }) {
  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
          <XAxis dataKey="name" stroke="#64748b" tick={{fill: '#64748b', fontSize: 12}} />
          <YAxis stroke="#64748b" tick={{fill: '#64748b', fontSize: 12}} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{paddingTop: '20px'}}/>
          <Bar dataKey={dataKey} name={name} fill={color} radius={[4, 4, 0, 0]} barSize={40} />
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
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
          <XAxis dataKey="timestamp" stroke="#64748b" tick={{fill: '#64748b', fontSize: 12}} />
          <YAxis stroke="#64748b" tick={{fill: '#64748b', fontSize: 12}} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{paddingTop: '20px'}} />
          {lines.map((line, index) => (
            <Line 
              key={index} 
              type="monotone" 
              dataKey={line.dataKey} 
              name={line.name} 
              stroke={line.color} 
              strokeWidth={3}
              activeDot={{ r: 6, strokeWidth: 0 }} 
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function AreaChartComponent({ data, dataKey, name, color }) {
  return (
    <div style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id={`color${dataKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.4}/>
              <stop offset="95%" stopColor={color} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
          <XAxis dataKey="name" stroke="#64748b" tick={{fill: '#64748b'}} />
          <YAxis stroke="#64748b" tick={{fill: '#64748b'}} />
          <Tooltip content={<CustomTooltip />} />
          <Area type="monotone" dataKey={dataKey} name={name} stroke={color} strokeWidth={3} fillOpacity={1} fill={`url(#color${dataKey})`} />
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
            innerRadius={70}
            outerRadius={100}
            paddingAngle={5}
            dataKey="value"
            stroke="none"
          >
            {data.map((entry, index) => (
               <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend verticalAlign="bottom" height={36} iconType="circle" />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
