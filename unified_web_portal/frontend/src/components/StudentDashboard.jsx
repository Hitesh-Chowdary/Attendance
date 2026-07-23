import React, { useState, useEffect } from 'react';

function StudentDashboard({ token, API_BASE_URL }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [slice, setSlice] = useState('overall'); // 'overall', 'monthly', 'weekly'

  useEffect(() => {
    const fetchScorecard = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/student/attendance`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) {
          throw new Error('Failed to fetch scorecard details');
        }
        const resData = await response.json();
        setData(resData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchScorecard();
  }, [token, API_BASE_URL]);

  if (loading) return <div style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: '40px' }}>Loading scorecard...</div>;
  if (error) return <div style={{ color: 'var(--color-danger)', textAlign: 'center', marginTop: '40px' }}>Error: {error}</div>;
  if (!data || !data.subject_metrics.length) {
    return (
      <div style={{ textAlign: 'center', marginTop: '40px' }}>
        <h3 style={{ fontSize: '20px' }}>No active classes found for section {data?.section_name}</h3>
        <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>Please contact campus administrator to set timetable.</p>
      </div>
    );
  }

  // Calculate Overall Averages
  const getPercentageForSubject = (subj) => {
    if (slice === 'weekly') return subj.weekly_percentage;
    if (slice === 'monthly') return subj.monthly_percentage;
    return subj.percentage;
  };

  const avgPercentage = data.subject_metrics.reduce((acc, curr) => acc + getPercentageForSubject(curr), 0) / data.subject_metrics.length;

  const getProgressColorClass = (pct) => {
    if (pct < 65) return 'danger';
    if (pct < 75) return 'warning';
    return 'success';
  };

  const getProgressColorHex = (pct) => {
    if (pct < 65) return 'var(--color-danger)';
    if (pct < 75) return 'var(--color-warning)';
    return 'var(--color-success)';
  };

  return (
    <div className="fade-in" style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Introduction Card */}
      <div className="glass-panel" style={{ marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: '700' }}>Hello, {data.student_name}</h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
            Registered Section: <strong style={{ color: '#fff' }}>{data.section_name}</strong> | Registration Number: <strong style={{ color: '#fff' }}>{data.reg_number}</strong>
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          {['overall', 'monthly', 'weekly'].map((s) => (
            <button
              key={s}
              className={slice === s ? "btn-primary" : "btn-secondary"}
              onClick={() => setSlice(s)}
              style={{ padding: '8px 16px', fontSize: '13px', textTransform: 'capitalize' }}
            >
              {s === 'overall' ? 'Overall' : s === 'monthly' ? 'Monthly Slice' : 'Weekly Slice'}
            </button>
          ))}
        </div>
      </div>

      {/* Primary KPI Indicators */}
      <div className="dashboard-grid" style={{ marginBottom: '28px' }}>
        <div className="glass-panel" style={{ display: 'flex', alignItems: 'center', justifyBetween: 'space-between', gap: '20px' }}>
          <div>
            <p className="card-title">Average Attendance Ratio</p>
            <p className="card-value" style={{ color: getProgressColorHex(avgPercentage) }}>{avgPercentage.toFixed(1)}%</p>
            <span style={{
              fontSize: '12px',
              padding: '4px 8px',
              borderRadius: '12px',
              background: avgPercentage >= 75 ? 'rgba(16, 185, 129, 0.1)' : avgPercentage >= 65 ? 'rgba(245, 158, 11, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              color: getProgressColorHex(avgPercentage),
              fontWeight: '600'
            }}>
              {avgPercentage >= 75 ? 'Safe Zone' : avgPercentage >= 65 ? 'Borderline Level' : 'Critical Action Required'}
            </span>
          </div>
        </div>

        <div className="glass-panel">
          <p className="card-title">Total Enrolled Subjects</p>
          <p className="card-value">{data.subject_metrics.length}</p>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Standard curriculum timetable slots</p>
        </div>

        <div className="glass-panel">
          <p className="card-title">Attended classes</p>
          <p className="card-value">
            {data.subject_metrics.reduce((acc, curr) => acc + curr.present_count, 0)}
            <span style={{ fontSize: '18px', color: 'var(--text-muted)', fontWeight: 'normal' }}>
              {' '}/ {data.subject_metrics.reduce((acc, curr) => acc + curr.total_classes, 0)}
            </span>
          </p>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Calculated across current log boundaries</p>
        </div>
      </div>

      {/* Subject Wise breakdown */}
      <h3 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '20px' }}>Subject-wise Attendance Scorecard</h3>
      <div className="dashboard-grid">
        {data.subject_metrics.map((subj, idx) => {
          const currentPct = getPercentageForSubject(subj);
          const colorClass = getProgressColorClass(currentPct);
          return (
            <div key={idx} className="glass-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '220px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <span style={{ fontSize: '11px', color: 'var(--color-accent)', fontWeight: '600', letterSpacing: '0.05em' }}>
                      {subj.course_code}
                    </span>
                    <h4 style={{ fontSize: '16px', fontWeight: '600', marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '200px' }}>
                      {subj.subject_name}
                    </h4>
                  </div>
                  <div style={{ fontSize: '20px', fontWeight: '700', color: getProgressColorHex(currentPct) }}>
                    {currentPct}%
                  </div>
                </div>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Lecturer: {subj.teacher_name}</p>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                  <span>Check-ins: {subj.present_count} / {subj.total_classes}</span>
                  <span style={{ textTransform: 'capitalize', color: getProgressColorHex(currentPct), fontWeight: '500' }}>
                    {currentPct >= 75 ? 'Safe' : currentPct >= 65 ? 'Borderline' : 'Critical'}
                  </span>
                </div>
                <div className="progress-bar-container">
                  <div 
                    className={`progress-bar-fill ${colorClass}`} 
                    style={{ width: `${Math.min(currentPct, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default StudentDashboard;
