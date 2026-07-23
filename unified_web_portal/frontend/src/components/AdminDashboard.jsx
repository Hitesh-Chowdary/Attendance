import React, { useState, useEffect } from 'react';

function AdminDashboard({ token, API_BASE_URL }) {
  const [activeTab, setActiveTab] = useState('analytics'); // 'analytics', 'timetable', 'campus', 'import'
  
  // Data states
  const [analytics, setAnalytics] = useState(null);
  const [branches, setBranches] = useState([]);
  const [sections, setSections] = useState([]);
  const [timetable, setTimetable] = useState([]);
  const [classrooms, setClassrooms] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [subjects, setSubjects] = useState([]);
  
  // Form states
  const [newBranch, setNewBranch] = useState({ name: '', code: '' });
  const [newSection, setNewSection] = useState({ branch_id: '', year: 1, section_name: '' });
  const [newTeacher, setNewTeacher] = useState({ name: '', email: '', password: '' });
  const [newSubject, setNewSubject] = useState({ subject_name: '', course_code: '' });
  const [newClassroom, setNewClassroom] = useState({ room_number: '', esp32_hardware_uid: '' });
  const [newSchedule, setNewSchedule] = useState({
    classroom_id: '', teacher_id: '', subject_id: '', section_id: '', day_of_week: 'Monday', start_time: '09:00', end_time: '10:30'
  });
  
  // Status states
  const [importFile, setImportFile] = useState(null);
  const [statusMsg, setStatusMsg] = useState({ text: '', type: '' });
  const [loading, setLoading] = useState(false);

  // Fetch all administrative data independently
  const fetchData = async () => {
    const headers = { 'Authorization': `Bearer ${token}` };
    let isExpired = false;

    const checkUnauthorized = (res) => {
      if (res.status === 401 && !isExpired) {
        isExpired = true;
        showStatus("Session expired. Please click 'Sign Out' and log in again to refresh your token.", "error");
      }
    };
    
    // 1. Fetch Analytics
    try {
      const resAnal = await fetch(`${API_BASE_URL}/api/admin/analytics`, { headers });
      checkUnauthorized(resAnal);
      if (resAnal.ok) setAnalytics(await resAnal.json());
    } catch (err) { console.error("Analytics fetch:", err); }
    
    // 2. Fetch Branches
    try {
      const resBranch = await fetch(`${API_BASE_URL}/api/admin/branches`, { headers });
      checkUnauthorized(resBranch);
      if (resBranch.ok) setBranches(await resBranch.json());
    } catch (err) { console.error("Branches fetch:", err); }

    // 3. Fetch Sections
    try {
      const resSec = await fetch(`${API_BASE_URL}/api/admin/sections`, { headers });
      checkUnauthorized(resSec);
      if (resSec.ok) setSections(await resSec.json());
    } catch (err) { console.error("Sections fetch:", err); }

    // 4. Fetch Timetable
    try {
      const resTime = await fetch(`${API_BASE_URL}/api/admin/timetable`, { headers });
      checkUnauthorized(resTime);
      if (resTime.ok) setTimetable(await resTime.json());
    } catch (err) { console.error("Timetable fetch:", err); }

    // 5. Fetch Classrooms
    try {
      const resClass = await fetch(`${API_BASE_URL}/api/admin/classrooms`, { headers });
      checkUnauthorized(resClass);
      if (resClass.ok) setClassrooms(await resClass.json());
    } catch (err) { console.error("Classrooms fetch:", err); }

    // 6. Fetch Teachers
    try {
      const resTeach = await fetch(`${API_BASE_URL}/api/admin/teachers`, { headers });
      checkUnauthorized(resTeach);
      if (resTeach.ok) setTeachers(await resTeach.json());
    } catch (err) { console.error("Teachers fetch:", err); }

    // 7. Fetch Subjects
    try {
      const resSubj = await fetch(`${API_BASE_URL}/api/admin/subjects`, { headers });
      checkUnauthorized(resSubj);
      if (resSubj.ok) setSubjects(await resSubj.json());
    } catch (err) { console.error("Subjects fetch:", err); }
  };

  useEffect(() => {
    fetchData();
  }, [token, activeTab]);

  const showStatus = (text, type = 'success') => {
    setStatusMsg({ text, type });
    setTimeout(() => setStatusMsg({ text: '', type: '' }), 5000);
  };

  // Add Branch
  const handleAddBranch = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/branches`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newBranch)
      });
      if (res.ok) {
        showStatus("Branch added successfully");
        setNewBranch({ name: '', code: '' });
        fetchData();
      } else {
        const data = await res.json();
        throw new Error(data.detail || "Failed to create branch");
      }
    } catch (err) {
      showStatus(err.message, 'error');
    }
  };

  // Add Section
  const handleAddSection = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/sections`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newSection)
      });
      if (res.ok) {
        showStatus("Section added successfully");
        setNewSection({ branch_id: '', year: 1, section_name: '' });
        fetchData();
      } else {
        const data = await res.json();
        throw new Error(data.detail || "Failed to create section");
      }
    } catch (err) {
      showStatus(err.message, 'error');
    }
  };

  // Add Timetable Slot
  const handleAddSchedule = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/timetable`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newSchedule)
      });
      if (res.ok) {
        showStatus("Timetable slot configured");
        fetchData();
      } else {
        const data = await res.json();
        throw new Error(data.detail || "Failed to configure timetable slot");
      }
    } catch (err) {
      showStatus(err.message, 'error');
    }
  };

  // Delete Timetable Slot
  const handleDeleteSchedule = async (id) => {
    if (!window.confirm("Remove this timetable schedule?")) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/timetable/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        showStatus("Schedule slot deleted");
        fetchData();
      }
    } catch (err) {
      showStatus(err.message, 'error');
    }
  };

  // Add Teacher
  const handleAddTeacher = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/teachers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newTeacher)
      });
      if (res.ok) {
        showStatus("Teacher profile created successfully");
        setNewTeacher({ name: '', email: '', password: '' });
        fetchData();
      } else {
        const data = await res.json();
        throw new Error(data.detail || "Failed to create teacher");
      }
    } catch (err) {
      showStatus(err.message, 'error');
    }
  };

  // Delete Teacher
  const handleDeleteTeacher = async (id) => {
    if (!window.confirm("Remove this teacher profile?")) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/teachers/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        showStatus("Teacher profile deleted");
        fetchData();
      } else {
        const data = await res.json();
        throw new Error(data.detail || "Failed to remove teacher");
      }
    } catch (err) {
      showStatus(err.message, 'error');
    }
  };

  // Add Subject
  const handleAddSubject = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/subjects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newSubject)
      });
      if (res.ok) {
        showStatus("Subject course registered");
        setNewSubject({ subject_name: '', course_code: '' });
        fetchData();
      } else {
        const data = await res.json();
        throw new Error(data.detail || "Failed to add subject");
      }
    } catch (err) {
      showStatus(err.message, 'error');
    }
  };

  // Delete Subject
  const handleDeleteSubject = async (id) => {
    if (!window.confirm("Deregister this subject course?")) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/subjects/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        showStatus("Subject removed");
        fetchData();
      } else {
        const data = await res.json();
        throw new Error(data.detail || "Failed to remove subject");
      }
    } catch (err) {
      showStatus(err.message, 'error');
    }
  };

  // Add Classroom
  const handleAddClassroom = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/classrooms`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newClassroom)
      });
      if (res.ok) {
        showStatus("Classroom registered successfully");
        setNewClassroom({ room_number: '', esp32_hardware_uid: '' });
        fetchData();
      } else {
        const data = await res.json();
        throw new Error(data.detail || "Failed to register classroom");
      }
    } catch (err) {
      showStatus(err.message, 'error');
    }
  };

  // Delete Classroom
  const handleDeleteClassroom = async (id) => {
    if (!window.confirm("Remove this classroom hardware mapping?")) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/classrooms/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        showStatus("Classroom removed");
        fetchData();
      } else {
        const data = await res.json();
        throw new Error(data.detail || "Failed to remove classroom");
      }
    } catch (err) {
      showStatus(err.message, 'error');
    }
  };

  // Import Roster
  const handleImportRoster = async (e) => {
    e.preventDefault();
    if (!importFile) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("file", importFile);

    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/students/import`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        showStatus(data.message);
        setImportFile(null);
        e.target.reset();
      } else {
        const data = await res.json();
        throw new Error(data.detail || "Failed to import roster");
      }
    } catch (err) {
      showStatus(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Download PDF Report
  const handleDownloadPDF = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/report`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) throw new Error("Could not download report PDF");
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'campus_attendance_report.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      showStatus(err.message, 'error');
    }
  };

  return (
    <div style={{ display: 'flex', gap: '32px', maxWidth: '1400px', margin: '0 auto', flexWrap: 'wrap' }}>
      
      {/* Sidebar Controls */}
      <div style={{ width: '260px', flexShrink: 0 }}>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '16px' }}>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 'bold', padding: '0 12px 8px', borderBottom: '1px solid var(--border-glass)' }}>
            CONTROL DASHBOARD
          </p>
          <button 
            className={activeTab === 'analytics' ? 'btn-primary' : 'btn-secondary'} 
            onClick={() => setActiveTab('analytics')}
            style={{ textAlign: 'left', display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 16px', fontSize: '14px' }}
          >
            📊 Analytics & PDF
          </button>
          <button 
            className={activeTab === 'timetable' ? 'btn-primary' : 'btn-secondary'} 
            onClick={() => setActiveTab('timetable')}
            style={{ textAlign: 'left', display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 16px', fontSize: '14px' }}
          >
            🗓️ Timetable Manager
          </button>
          <button 
            className={activeTab === 'campus' ? 'btn-primary' : 'btn-secondary'} 
            onClick={() => setActiveTab('campus')}
            style={{ textAlign: 'left', display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 16px', fontSize: '14px' }}
          >
            🏫 Branches & Sections
          </button>
          <button 
            className={activeTab === 'import' ? 'btn-primary' : 'btn-secondary'} 
            onClick={() => setActiveTab('import')}
            style={{ textAlign: 'left', display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 16px', fontSize: '14px' }}
          >
            📤 Bulk Import Roster
          </button>
        </div>
      </div>

      {/* Main Panel Content */}
      <div style={{ flex: 1, minWidth: '320px' }}>
        
        {/* Status Alerts */}
        {statusMsg.text && (
          <div className="fade-in" style={{
            background: statusMsg.type === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
            border: statusMsg.type === 'error' ? '1px solid rgba(239, 68, 68, 0.2)' : '1px solid rgba(16, 185, 129, 0.2)',
            borderRadius: 'var(--radius-md)',
            color: statusMsg.type === 'error' ? '#f87171' : '#34d399',
            fontSize: '14px',
            padding: '12px 16px',
            marginBottom: '24px'
          }}>
            {statusMsg.text}
          </div>
        )}

        {/* Tab 1: Analytics Dashboard */}
        {activeTab === 'analytics' && analytics && (
          <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className="glass-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '15px' }}>
              <div>
                <h2 style={{ fontSize: '22px', fontWeight: '700' }}>Overall Campus Analytics</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Multi-level attendance metrics and reporting output pipeline.</p>
              </div>
              <button className="btn-primary" onClick={handleDownloadPDF}>
                📄 Export Report (PDF)
              </button>
            </div>

            {/* KPI Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
              <div className="glass-panel">
                <p className="card-title">Campus Average Attendance</p>
                <p className="card-value" style={{ color: 'var(--color-success)' }}>
                  {analytics.baseline_comparison.overall_campus_average}%
                </p>
                <p style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Calculated across all historical sessions</p>
              </div>
              <div className="glass-panel">
                <p className="card-title">First-Year Baseline Average</p>
                <p className="card-value" style={{ color: 'var(--color-accent)' }}>
                  {analytics.baseline_comparison.first_year_average}%
                </p>
                <p style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Baseline threshold comparison metric</p>
              </div>
            </div>

            {/* Visual SVG Branch Attendance Chart */}
            <div className="glass-panel">
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>Attendance ratio by branch (CSE, ECE, IT, ME, etc.)</h3>
              <div style={{ height: '240px', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', paddingTop: '20px', borderBottom: '1px solid var(--border-glass)' }}>
                {analytics.branch_metrics.map((branch, i) => (
                  <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '60px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>{branch.present_percentage}%</div>
                    {/* SVG Cylinder bar */}
                    <div style={{
                      width: '32px',
                      height: `${branch.present_percentage * 1.5}px`,
                      background: 'linear-gradient(to top, #3b82f6, #6366f1)',
                      borderRadius: '6px 6px 0 0',
                      boxShadow: '0 0 10px rgba(59, 130, 246, 0.3)',
                      transition: 'all 0.5s ease-out'
                    }}></div>
                    <div style={{ fontSize: '12px', fontWeight: 'bold', marginTop: '8px' }}>{branch.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Section metrics comparison */}
            <div className="glass-panel">
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>Attendance metrics by student sections</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {analytics.section_metrics.map((sec, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <span style={{ width: '80px', fontSize: '13px', fontWeight: '600' }}>{sec.label}</span>
                    <div style={{ flex: 1 }} className="progress-bar-container">
                      <div className="progress-bar-fill success" style={{ width: `${sec.present_percentage}%` }}></div>
                    </div>
                    <span style={{ width: '45px', fontSize: '13px', textAlign: 'right', fontWeight: '700' }}>{sec.present_percentage}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* At Risk Students Table */}
            <div className="glass-panel">
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px', color: 'var(--color-danger)' }}>⚠️ At-Risk Students (&lt;65% Attendance)</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-secondary)' }}>
                    <th style={{ padding: '8px' }}>Registration No.</th>
                    <th style={{ padding: '8px' }}>Student Name</th>
                    <th style={{ padding: '8px' }}>Section</th>
                    <th style={{ padding: '8px', textAlign: 'right' }}>Attendance</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.at_risk_students.map((stud, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                      <td style={{ padding: '10px 8px' }}>{stud.reg_number}</td>
                      <td style={{ padding: '10px 8px', fontWeight: '500' }}>{stud.name}</td>
                      <td style={{ padding: '10px 8px' }}>{stud.section}</td>
                      <td style={{ padding: '10px 8px', textAlign: 'right', color: 'var(--color-danger)', fontWeight: '600' }}>
                        {stud.present_percentage}%
                      </td>
                    </tr>
                  ))}
                  {analytics.at_risk_students.length === 0 && (
                    <tr>
                      <td colSpan="4" style={{ textAlign: 'center', padding: '12px', color: 'var(--text-muted)' }}>
                        All campus students are clear of the critical 65% boundary!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 2: Timetable Manager */}
        {activeTab === 'timetable' && (
          <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className="glass-panel">
              <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '16px' }}>Timetable Master Planner</h2>
              
              <form onSubmit={handleAddSchedule} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '15px', marginBottom: '24px' }}>
                <div>
                  <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Classroom Station</label>
                  <select 
                    className="form-input" 
                    value={newSchedule.classroom_id} 
                    onChange={e => setNewSchedule({...newSchedule, classroom_id: e.target.value})} 
                    required
                  >
                    <option value="">Select Classroom</option>
                    {classrooms.map(c => <option key={c.id} value={c.id}>{c.room_number}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Teacher Profile</label>
                  <select 
                    className="form-input" 
                    value={newSchedule.teacher_id} 
                    onChange={e => setNewSchedule({...newSchedule, teacher_id: e.target.value})} 
                    required
                  >
                    <option value="">Select Teacher</option>
                    {teachers.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Subject Course</label>
                  <select 
                    className="form-input" 
                    value={newSchedule.subject_id} 
                    onChange={e => setNewSchedule({...newSchedule, subject_id: e.target.value})} 
                    required
                  >
                    <option value="">Select Subject</option>
                    {subjects.map(s => <option key={s.id} value={s.id}>{s.subject_name}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Student Section</label>
                  <select 
                    className="form-input" 
                    value={newSchedule.section_id} 
                    onChange={e => setNewSchedule({...newSchedule, section_id: e.target.value})} 
                    required
                  >
                    <option value="">Select Section</option>
                    {sections.map(s => <option key={s.section_id} value={s.section_id}>{s.section_name}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Day of Week</label>
                  <select 
                    className="form-input" 
                    value={newSchedule.day_of_week} 
                    onChange={e => setNewSchedule({...newSchedule, day_of_week: e.target.value})} 
                    required
                  >
                    {["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Start Time</label>
                  <input 
                    type="time" 
                    className="form-input" 
                    value={newSchedule.start_time} 
                    onChange={e => setNewSchedule({...newSchedule, start_time: e.target.value})} 
                    required
                  />
                </div>
                <div>
                  <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>End Time</label>
                  <input 
                    type="time" 
                    className="form-input" 
                    value={newSchedule.end_time} 
                    onChange={e => setNewSchedule({...newSchedule, end_time: e.target.value})} 
                    required
                  />
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                  <button type="submit" className="btn-primary" style={{ width: '100%', padding: '10px 0' }}>+ Create Slot</button>
                </div>
              </form>

              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>Active Timetable Schedules</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-secondary)', textAlign: 'left' }}>
                    <th style={{ padding: '8px' }}>Room</th>
                    <th style={{ padding: '8px' }}>Subject</th>
                    <th style={{ padding: '8px' }}>Instructor</th>
                    <th style={{ padding: '8px' }}>Section</th>
                    <th style={{ padding: '8px' }}>Day</th>
                    <th style={{ padding: '8px' }}>Duration</th>
                    <th style={{ padding: '8px', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {timetable.map((slot) => (
                    <tr key={slot.schedule_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                      <td style={{ padding: '8px' }}>{slot.classroom_number}</td>
                      <td style={{ padding: '8px', fontWeight: '500' }}>{slot.subject_name}</td>
                      <td style={{ padding: '8px' }}>{slot.teacher_name}</td>
                      <td style={{ padding: '8px' }}>{slot.section_name}</td>
                      <td style={{ padding: '8px' }}>{slot.day_of_week}</td>
                      <td style={{ padding: '8px' }}>{slot.start_time} - {slot.end_time}</td>
                      <td style={{ padding: '8px', textAlign: 'right' }}>
                        <button 
                          onClick={() => handleDeleteSchedule(slot.schedule_id)} 
                          style={{ background: 'none', border: 'none', color: 'var(--color-danger)', cursor: 'pointer', fontWeight: '600' }}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Branches & Sections */}
        {activeTab === 'campus' && (
          <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            
            {/* Row 1: Branches and Sections */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              {/* Branches Card */}
              <div className="glass-panel">
                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Manage Academic Branches</h3>
                <form onSubmit={handleAddBranch} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                  <input 
                    type="text" 
                    className="form-input" 
                    placeholder="Branch Name (e.g. Civil Eng.)" 
                    value={newBranch.name} 
                    onChange={e => setNewBranch({...newBranch, name: e.target.value})}
                    required 
                  />
                  <input 
                    type="text" 
                    className="form-input" 
                    placeholder="Code (e.g. CE)" 
                    value={newBranch.code} 
                    onChange={e => setNewBranch({...newBranch, code: e.target.value})}
                    style={{ width: '100px' }}
                    required 
                  />
                  <button type="submit" className="btn-primary">+</button>
                </form>
                <div style={{ maxHeight: '300px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {branches.map(b => (
                    <div key={b.branch_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(255,255,255,0.02)', borderRadius: 'var(--radius-sm)' }}>
                      <span>{b.name}</span>
                      <strong style={{ color: 'var(--color-accent)' }}>{b.code}</strong>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sections Card */}
              <div className="glass-panel">
                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Manage Sections</h3>
                <form onSubmit={handleAddSection} style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
                  <select 
                    className="form-input" 
                    value={newSection.branch_id} 
                    onChange={e => setNewSection({...newSection, branch_id: e.target.value})}
                    required
                  >
                    <option value="">Select Branch</option>
                    {branches.map(b => <option key={b.branch_id} value={b.branch_id}>{b.name}</option>)}
                  </select>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <input 
                      type="number" 
                      className="form-input" 
                      placeholder="Year (1-4)" 
                      min="1" max="4"
                      value={newSection.year}
                      onChange={e => setNewSection({...newSection, year: parseInt(e.target.value)})}
                      required
                    />
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder="Name (e.g. CSE-3B)" 
                      value={newSection.section_name} 
                      onChange={e => setNewSection({...newSection, section_name: e.target.value})}
                      required 
                    />
                    <button type="submit" className="btn-primary" style={{ padding: '0 20px' }}>+</button>
                  </div>
                </form>
                <div style={{ maxHeight: '230px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {sections.map(s => (
                    <div key={s.section_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(255,255,255,0.02)', borderRadius: 'var(--radius-sm)' }}>
                      <span>Section: {s.section_name}</span>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>Year {s.year} ({s.branch_code})</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Row 2: Teachers and Subjects */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              {/* Teachers Card */}
              <div className="glass-panel">
                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Manage Teacher Profiles</h3>
                <form onSubmit={handleAddTeacher} style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
                  <input 
                    type="text" 
                    className="form-input" 
                    placeholder="Full Name (e.g. Dr. John Doe)" 
                    value={newTeacher.name} 
                    onChange={e => setNewTeacher({...newTeacher, name: e.target.value})}
                    required 
                  />
                  <input 
                    type="email" 
                    className="form-input" 
                    placeholder="Email (e.g. doe@college.edu)" 
                    value={newTeacher.email} 
                    onChange={e => setNewTeacher({...newTeacher, email: e.target.value})}
                    required 
                  />
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <input 
                      type="password" 
                      className="form-input" 
                      placeholder="Login Password" 
                      value={newTeacher.password} 
                      onChange={e => setNewTeacher({...newTeacher, password: e.target.value})}
                      required 
                    />
                    <button type="submit" className="btn-primary" style={{ padding: '0 20px' }}>+</button>
                  </div>
                </form>
                <div style={{ maxHeight: '230px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {teachers.map(t => (
                    <div key={t.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: 'rgba(255,255,255,0.02)', borderRadius: 'var(--radius-sm)' }}>
                      <div>
                        <span style={{ display: 'block', fontWeight: '600' }}>{t.name}</span>
                        <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{t.email}</span>
                      </div>
                      <button 
                        onClick={() => handleDeleteTeacher(t.id)} 
                        style={{ background: 'none', border: 'none', color: 'var(--color-danger)', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Subjects Card */}
              <div className="glass-panel">
                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Manage Course Subjects</h3>
                <form onSubmit={handleAddSubject} style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
                  <input 
                    type="text" 
                    className="form-input" 
                    placeholder="Subject Name (e.g. Embedded Systems)" 
                    value={newSubject.subject_name} 
                    onChange={e => setNewSubject({...newSubject, subject_name: e.target.value})}
                    required 
                  />
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder="Course Code (e.g. EC-302)" 
                      value={newSubject.course_code} 
                      onChange={e => setNewSubject({...newSubject, course_code: e.target.value})}
                      required 
                    />
                    <button type="submit" className="btn-primary" style={{ padding: '0 20px' }}>+</button>
                  </div>
                </form>
                <div style={{ maxHeight: '230px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {subjects.map(s => (
                    <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: 'rgba(255,255,255,0.02)', borderRadius: 'var(--radius-sm)' }}>
                      <div>
                        <span style={{ display: 'block', fontWeight: '600' }}>{s.subject_name}</span>
                        <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Code: {s.course_code}</span>
                      </div>
                      <button 
                        onClick={() => handleDeleteSubject(s.id)} 
                        style={{ background: 'none', border: 'none', color: 'var(--color-danger)', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Row 3: Classrooms */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              {/* Classrooms Card */}
              <div className="glass-panel">
                <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Manage Classroom Stations</h3>
                <form onSubmit={handleAddClassroom} style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
                  <input 
                    type="text" 
                    className="form-input" 
                    placeholder="Room Number (e.g. LH-302)" 
                    value={newClassroom.room_number} 
                    onChange={e => setNewClassroom({...newClassroom, room_number: e.target.value})}
                    required 
                  />
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder="ESP32 Hardware UID (e.g. ESP32_DEV_ROOM302)" 
                      value={newClassroom.esp32_hardware_uid} 
                      onChange={e => setNewClassroom({...newClassroom, esp32_hardware_uid: e.target.value})}
                      required 
                    />
                    <button type="submit" className="btn-primary" style={{ padding: '0 20px' }}>+</button>
                  </div>
                </form>
                <div style={{ maxHeight: '230px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {classrooms.map(c => (
                    <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: 'rgba(255,255,255,0.02)', borderRadius: 'var(--radius-sm)' }}>
                      <div>
                        <span style={{ display: 'block', fontWeight: '600' }}>Room: {c.room_number}</span>
                        <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>UID: {c.esp32_hardware_uid}</span>
                      </div>
                      <button 
                        onClick={() => handleDeleteClassroom(c.id)} 
                        style={{ background: 'none', border: 'none', color: 'var(--color-danger)', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Balance Card */}
              <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', opacity: 0.6 }}>
                <p style={{ fontSize: '36px' }}>🏫</p>
                <h4 style={{ fontWeight: 'bold', marginTop: '10px' }}>College Campus Infrastructure</h4>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', textAlign: 'center', maxWidth: '280px', marginTop: '5px' }}>
                  Add classrooms and map them to their corresponding ESP32 hardware network nodes to support location verification.
                </p>
              </div>
            </div>

          </div>
        )}

        {/* Tab 4: Student Bulk Import */}
        {activeTab === 'import' && (
          <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className="glass-panel">
              <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '8px' }}>Bulk-Import Student Roster</h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '20px' }}>
                Upload student enrollment tables directly. File structures should declare standard columns: 
                <code style={{ color: 'var(--color-accent)', padding: '2px 6px', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '4px', marginLeft: '6px' }}>
                  reg_number, name, password, section_name
                </code>
              </p>

              <form onSubmit={handleImportRoster} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div style={{
                  border: '2px dashed var(--border-glass)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '40px',
                  textAlign: 'center',
                  cursor: 'pointer',
                  background: 'rgba(255,255,255,0.01)',
                  transition: 'var(--transition-smooth)'
                }}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  if (e.dataTransfer.files.length) {
                    setImportFile(e.dataTransfer.files[0]);
                  }
                }}
                >
                  <p style={{ fontSize: '16px', fontWeight: '500', marginBottom: '10px' }}>
                    {importFile ? `Selected: ${importFile.name}` : 'Drag & Drop CSV / Excel spreadsheet here'}
                  </p>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Or click below to browse local directories</p>
                  <input 
                    type="file" 
                    accept=".csv, .xlsx, .xls"
                    onChange={e => setImportFile(e.target.files[0])}
                    style={{ marginTop: '15px' }}
                  />
                </div>

                <button 
                  type="submit" 
                  className="btn-primary" 
                  disabled={loading || !importFile} 
                  style={{ alignSelf: 'flex-start' }}
                >
                  {loading ? 'Uploading & Parsing...' : '📤 Run Spreadsheet Import'}
                </button>
              </form>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default AdminDashboard;
