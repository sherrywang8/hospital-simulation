import { useDeferredValue, useEffect, useMemo, useState } from 'react';
import {
  formatDuration,
  SIMULATION_WEEKDAYS,
  formatInteger,
  formatSimulationClock,
  getEventTone,
  getSimulationWeekdayIndex,
} from '../../../lib/formatters.js';

const EVENT_CATEGORY_OPTIONS = [
  { value: 'all', label: '全部類別' },
  { value: 'arrival', label: '到離院' },
  { value: 'triage', label: '檢傷流程' },
  { value: 'doctor', label: '初診流程' },
  { value: 'exam', label: '檢查流程' },
  { value: 'return', label: '複診流程' },
];

function getEventCategory(eventType = '') {
  if (eventType.includes('抵達') || eventType.includes('離院')) return 'arrival';
  if (eventType.includes('檢傷') || eventType.includes('護理評估') || eventType.includes('Triage')) {
    return 'triage';
  }
  if (eventType.includes('複診')) return 'return';
  if (
    eventType.includes('檢查')
    || eventType.includes('報告')
    || eventType.includes('CT')
    || eventType.includes('Lab')
    || eventType.includes('Xray')
    || eventType.includes('超音波')
    || eventType.includes('Ultrasound')
  ) {
    return 'exam';
  }
  if (eventType.includes('初診')) return 'doctor';
  return 'all';
}

function formatEventType(eventType = '') {
  return eventType
    .replace('護理紀錄與衛教', '護理紀錄')
    .replace('護理紀錄與交班', '護理紀錄');
}

const PAGE_SIZE = 100;

function EventLogTable({ logs }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedWeekday, setSelectedWeekday] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedEventType, setSelectedEventType] = useState('all');
  const [page, setPage] = useState(0);
  const deferredSearchTerm = useDeferredValue(searchTerm);

  const eventTypes = useMemo(
    () => Array.from(new Set((logs || []).map((log) => formatEventType(log.event_type)))).sort(),
    [logs]
  );

  const availableEventTypes = useMemo(
    () =>
      eventTypes.filter(
        (eventType) => selectedCategory === 'all' || getEventCategory(eventType) === selectedCategory
      ),
    [eventTypes, selectedCategory]
  );

  const activeEventType =
    selectedEventType === 'all' || availableEventTypes.includes(selectedEventType)
      ? selectedEventType
      : 'all';

  const filteredLogs = useMemo(() => {
    const keyword = deferredSearchTerm.trim().toLowerCase();
    return (logs || []).filter((log) => {
      const matchesSearch =
        keyword.length === 0
        || [
          log.patient,
          log.triage_level,
          log.event_type,
          log.resource,
          log.desc,
        ].some((value) => String(value || '').toLowerCase().includes(keyword));

      const matchesCategory =
        selectedCategory === 'all' || getEventCategory(log.event_type) === selectedCategory;

      const matchesWeekday =
        selectedWeekday === 'all' || getSimulationWeekdayIndex(log.timestamp) === Number(selectedWeekday);

      const matchesEventType =
        activeEventType === 'all' || formatEventType(log.event_type) === activeEventType;

      return matchesSearch && matchesWeekday && matchesCategory && matchesEventType;
    });
  }, [activeEventType, deferredSearchTerm, logs, selectedCategory, selectedWeekday]);

  const totalPages = Math.max(1, Math.ceil(filteredLogs.length / PAGE_SIZE));
  const pagedLogs = filteredLogs.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  useEffect(() => {
    setPage(0);
  }, [filteredLogs]);

  return (
    <section className="panel-card">
      <div className="panel-head">
        <div>
          <p className="panel-eyebrow">Event Log</p>
          <h2 className="panel-title">事件明細</h2>
        </div>
        <p className="panel-copy">
          顯示第 {formatInteger(page * PAGE_SIZE + 1)}–{formatInteger(Math.min((page + 1) * PAGE_SIZE, filteredLogs.length))} 筆，
          篩選後共 {formatInteger(filteredLogs.length)} / {formatInteger(logs?.length || 0)} 筆。
          每一列都同步帶出病人的到院時刻、離院時刻與初診等待時間，減少自己換算分鐘數的負擔。
        </p>
      </div>

      <div className="filter-controls">
        <label className="search-block">
          <span className="field-label">搜尋事件</span>
          <input
            className="search-input"
            type="text"
            placeholder="搜尋病人、事件名稱、資源或描述"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
        </label>

        <label className="select-block">
          <span className="field-label">星期</span>
          <select
            className="field-input filter-select"
            value={selectedWeekday}
            onChange={(event) => setSelectedWeekday(event.target.value)}
          >
            <option value="all">全部星期</option>
            {SIMULATION_WEEKDAYS.map((day, index) => (
              <option key={day} value={index}>
                {day}
              </option>
            ))}
          </select>
        </label>

        <label className="select-block">
          <span className="field-label">事件分類</span>
          <select
            className="field-input filter-select"
            value={selectedCategory}
            onChange={(event) => {
              setSelectedCategory(event.target.value);
              setSelectedEventType('all');
            }}
          >
            {EVENT_CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="select-block">
          <span className="field-label">事件名稱</span>
          <select
            className="field-input filter-select"
            value={activeEventType}
            onChange={(event) => setSelectedEventType(event.target.value)}
          >
            <option value="all">全部事件</option>
            {availableEventTypes.map((eventType) => (
              <option key={eventType} value={eventType}>
                {eventType}
              </option>
            ))}
          </select>
        </label>

        <button
          className="ghost-button"
          type="button"
          onClick={() => {
            setSearchTerm('');
            setSelectedWeekday('all');
            setSelectedCategory('all');
            setSelectedEventType('all');
          }}
        >
          清除篩選
        </button>
      </div>

      <div className="table-wrap">
        <table className="log-table">
          <thead>
            <tr>
              <th>模擬時刻</th>
              <th>事件</th>
              <th>病人</th>
              <th>檢傷</th>
              <th>到院時刻</th>
              <th>離院時刻</th>
              <th>初診等待</th>
              <th>資源</th>
              <th>描述</th>
            </tr>
          </thead>
          <tbody>
            {pagedLogs.map((log, index) => (
              <tr key={`${log.patient}-${log.timestamp}-${index}`}>
                <td className="mono-cell time-cell">{formatSimulationClock(log.timestamp)}</td>
                <td>
                  <span className={`event-badge ${getEventTone(log.event_type)}`}>
                    {formatEventType(log.event_type)}
                  </span>
                </td>
                <td className="mono-cell">{log.patient}</td>
                <td>{log.triage_level}</td>
                <td className="mono-cell time-cell">{`${formatSimulationClock(log.arrival_clock)} 到院`}</td>
                <td className="mono-cell time-cell">{`${formatSimulationClock(log.departure_clock)} 離院`}</td>
                <td>{formatDuration(log.waiting_time)}</td>
                <td>{log.resource}</td>
                <td>{log.desc}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredLogs.length === 0 ? (
          <div className="empty-state">目前星期或篩選條件下沒有事件。</div>
        ) : null}
      </div>

      {totalPages > 1 ? (
        <div className="pagination">
          <button
            className="ghost-button pagination-btn"
            type="button"
            onClick={() => setPage((p) => p - 1)}
            disabled={page === 0}
          >
            ← 上一頁
          </button>
          <span className="pagination-info">
            第 {page + 1} 頁，共 {totalPages} 頁
          </span>
          <button
            className="ghost-button pagination-btn"
            type="button"
            onClick={() => setPage((p) => p + 1)}
            disabled={page >= totalPages - 1}
          >
            下一頁 →
          </button>
        </div>
      ) : null}
    </section>
  );
}

export default EventLogTable;
