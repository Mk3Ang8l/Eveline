import React, { useState, useEffect, useRef } from 'react';
import './LiveMonitor.css';

const LiveMonitor = () => {
    const [events, setEvents] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const scrollRef = useRef(null);
    const wsRef = useRef(null);

    useEffect(() => {
        // Determine WS URL based on current host
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        // Proxied via Vite/Docker or direct access
        const wsUrl = `${protocol}//${host}:8000/api/realtime/ws`;

        const connect = () => {
            console.log('Connecting to LiveMonitor WS:', wsUrl);
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                setIsConnected(true);
                console.log('LiveMonitor WS Connected');
                // Auto-start stream on backend if needed
                fetch('/api/realtime/start', { method: 'POST' }).catch(console.error);
            };

            ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                if (msg.type === 'INIT') {
                    setEvents(msg.data);
                } else if (msg.type === 'UPDATE') {
                    setEvents(prev => [...prev, ...msg.data].slice(-100)); // Keep last 100
                }
            };

            ws.onclose = () => {
                setIsConnected(false);
                console.log('LiveMonitor WS Closed. Reconnecting...');
                setTimeout(connect, 3000);
            };

            ws.onerror = (err) => {
                console.error('LiveMonitor WS Error:', err);
                ws.close();
            };
        };

        connect();

        return () => {
            if (wsRef.current) wsRef.current.close();
        };
    }, []);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [events]);

    return (
        <div className="live-monitor-container">
            <div className="live-monitor-header">
                <span className={`status-indicator ${isConnected ? 'online' : 'offline'}`}></span>
                <h3>CERTSTREAM_LIVE_FEED</h3>
                <span className="event-count">{events.length} certificates</span>
            </div>
            <div className="live-monitor-body" ref={scrollRef}>
                {events.map((ev, i) => (
                    <div key={i} className="live-event-row">
                        <span className="event-time">[{new Date(ev.timestamp).toLocaleTimeString()}]</span>
                        <span className="event-type">SSL_CERT</span>
                        <span className="event-domain">{ev.domain}</span>
                        <span className="event-issuer">issued by: {ev.issuer || 'Unknown'}</span>
                    </div>
                ))}
                {events.length === 0 && <div className="loading-feed">Waiting for data...</div>}
            </div>
        </div>
    );
};

export default LiveMonitor;
