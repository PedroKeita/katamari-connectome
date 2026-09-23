import { useState, useEffect, useRef } from 'react';

const KEY_SETS = [
  ['w', 'a', 'j', 'i'],
  ['w', 'd', 'l', 'i'],
  ['w', 'i'],
  ['a', 'j'],
  ['w', 'a', 'j', 'i', 'ctrl'],
  ['w', 'd', 'l', 'i', 'shift'],
  ['s', 'k'],
  ['w', 'a', 'j', 'i'],
];

const EMPTY = {
  fw_bias: 0, left: 0, center: 0, right: 0, mag: 0,
  collected: 0, pressed_keys: [],
  escape_active: false, threat_level: 0,
  circuits: { reward: { rate: 0 }, escape: { rate: 0 }, orient: { rate: 0 } },
};

function syntheticTick(t) {
  const bias   = Math.sin(t * 0.4) * 0.7;
  const left   = Math.max(0, 0.5 + Math.sin(t * 1.1) * 0.4);
  const center = Math.max(0, 0.6 + Math.sin(t * 0.7) * 0.3);
  const right  = Math.max(0, 0.5 - Math.sin(t * 1.1) * 0.4);
  const escape = t % 20 > 17; // simulate escape burst every 20s
  return {
    fw_bias:       Math.round(bias * 1000) / 1000,
    left:          Math.round(left  * 100) / 100,
    center:        Math.round(center * 100) / 100,
    right:         Math.round(right  * 100) / 100,
    mag:           Math.round((center * 0.6 + Math.max(left, right) * 0.4) * 100) / 100,
    collected:     Math.floor(t / 8),
    pressed_keys:  KEY_SETS[Math.floor(t / 1.5) % KEY_SETS.length],
    escape_active: escape,
    threat_level:  escape ? 0.9 : 0.1,
    circuits: {
      reward: { rate: Math.round(Math.abs(bias) * 0.05 * 10000) / 10000 },
      escape: { rate: escape ? 0.8 : 0 },
      orient: { rate: Math.round(Math.abs(bias) * 0.02 * 10000) / 10000 },
    },
  };
}

export default function useSessionData(wsUrl = 'ws://localhost:8765') {
  const [state,     setState]     = useState(EMPTY);
  const [connected, setConnected] = useState(false);
  const tRef    = useRef(0);
  const liveRef = useRef(false);

  // WebSocket
  useEffect(() => {
    let ws, dead = false;

    function connect() {
      try {
        ws = new WebSocket(wsUrl);
        ws.onopen  = () => { setConnected(true);  liveRef.current = true;  };
        ws.onclose = () => { setConnected(false); liveRef.current = false; if (!dead) setTimeout(connect, 3000); };
        ws.onerror = () => ws.close();
        ws.onmessage = (e) => { try { setState(JSON.parse(e.data)); } catch {} };
      } catch { /* no ws available */ }
    }

    connect();
    return () => { dead = true; ws?.close(); };
  }, [wsUrl]);

  // Synthetic demo when not live
  useEffect(() => {
    let id;
    function tick() {
      if (!liveRef.current) {
        tRef.current += 0.05;
        setState(syntheticTick(tRef.current));
      }
      id = setTimeout(tick, 50);
    }
    id = setTimeout(tick, 50);
    return () => clearTimeout(id);
  }, []);

  return { state, connected };
}
