import { useMemo, useState } from 'react';
import EventLogTimeline from './EventLogTimeline.jsx';

const WEEKDAYS = ['週一', '週二', '週三', '週四', '週五', '週六', '週日'];

function formatSimTime(minutes) {
  const day = Math.floor(minutes / 1440) + 1;
  const hh = String(Math.floor((minutes % 1440) / 60)).padStart(2, '0');
  const mm = String(Math.floor(minutes % 60)).padStart(2, '0');
  return `D${day} ${hh}:${mm}`;
}

export default function PatientDashboard({ logs }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDay, setSelectedDay] = useState('All');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedPatientId, setSelectedPatientId] = useState(null);

  const { patientMap, patients, triageLevels } = useMemo(() => {
    const map = new Map();
    for (const log of logs) {
      const id = log.patient;
      if (!map.has(id)) map.set(id, []);
      map.get(id).push(log);
    }

    const patientsArr = [];
    const levelsSet = new Set();

    for (const [id, patLogs] of map) {
      const arrivalMinutes = patLogs[0].timestamp;
      const dischargeMinutes = patLogs[patLogs.length - 1].timestamp;
      const triageLevel = patLogs[0].triage_level || '-';
      const dayIndex = Math.floor(arrivalMinutes / 1440) % 7;
      levelsSet.add(triageLevel);
      patientsArr.push({
        id,
        logs: patLogs,
        arrivalTime: formatSimTime(arrivalMinutes),
        dischargeTime: formatSimTime(dischargeMinutes),
        dayIndex,
        triageLevel,
      });
    }

    return { patientMap: map, patients: patientsArr, triageLevels: [...levelsSet].sort() };
  }, [logs]);

  const filteredPatients = useMemo(() => {
    return patients.filter((p) => {
      if (searchQuery && !p.id.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      if (selectedDay !== 'All' && WEEKDAYS[p.dayIndex] !== selectedDay) return false;
      if (selectedCategory !== 'All' && p.triageLevel !== selectedCategory) return false;
      return true;
    });
  }, [patients, searchQuery, selectedDay, selectedCategory]);

  // Fall back to first visible patient when current selection is filtered out
  const effectiveId =
    filteredPatients.find((p) => p.id === selectedPatientId)
      ? selectedPatientId
      : (filteredPatients[0]?.id ?? null);

  const selectedLogs = patientMap.get(effectiveId) ?? [];

  return (
    <div className="patient-dashboard">
      <div className="filter-bar">
        <input
          type="text"
          className="filter-input"
          placeholder="🔍 搜尋病患代號 (例如 P0069)..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <select
          className="filter-select"
          value={selectedDay}
          onChange={(e) => setSelectedDay(e.target.value)}
        >
          <option value="All">所有星期</option>
          {WEEKDAYS.map((day) => (
            <option key={day} value={day}>{day}</option>
          ))}
        </select>
        <select
          className="filter-select"
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
        >
          <option value="All">所有檢傷</option>
          {triageLevels.map((level) => (
            <option key={level} value={level}>{level}</option>
          ))}
        </select>
      </div>

      <div className="patient-list">
        {filteredPatients.length === 0 ? (
          <p style={{ color: 'var(--ink-soft)', padding: '8px' }}>找不到符合條件的病患。</p>
        ) : (
          filteredPatients.map((patient) => (
            <div
              key={patient.id}
              className={`patient-card${effectiveId === patient.id ? ' active' : ''}`}
              onClick={() => setSelectedPatientId(patient.id)}
            >
              <h4>{patient.id}</h4>
              <p>{patient.logs.length} 個事件 · {patient.triageLevel}</p>
              <div className="patient-card-times">
                <span>進：{patient.arrivalTime}</span>
                <span>出：{patient.dischargeTime}</span>
              </div>
            </div>
          ))
        )}
      </div>

      {effectiveId && <EventLogTimeline patientLogs={selectedLogs} />}
    </div>
  );
}
