export default function EventLogTimeline({ patientLogs }) {
  return (
    <div className="timeline-container">
      {patientLogs.map((log, index) => (
        <div className="timeline-item" key={index}>
          <span className="timeline-time">{Math.round(log.timestamp)} 分</span>
          <div className="timeline-content">
            <h5>{log.event_type}</h5>
            {log.desc && log.desc !== '-' && <p>{log.desc}</p>}
            {log.resource && log.resource !== '-' && (
              <span className="resource-tag">{log.resource}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
