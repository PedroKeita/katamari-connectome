import { useState, useEffect, useRef } from 'react';

export default function CollectFlash({ collected = 0 }) {
  const [visible,  setVisible]  = useState(false);
  const [count,    setCount]    = useState(collected);
  const prevRef = useRef(collected);

  useEffect(() => {
    if (collected > prevRef.current) {
      setCount(collected);
      setVisible(true);
      const id = setTimeout(() => setVisible(false), 1200);
      prevRef.current = collected;
      return () => clearTimeout(id);
    }
    prevRef.current = collected;
  }, [collected]);

  return (
    <div style={{
      position: 'fixed', top: '50%', left: '25%',
      transform: 'translate(-50%, -50%)',
      fontSize: 20, fontWeight: 700,
      color: 'var(--green-bright)',
      textShadow: '0 0 20px var(--green)',
      letterSpacing: 4, whiteSpace: 'nowrap',
      pointerEvents: 'none', zIndex: 99,
      opacity: visible ? 1 : 0,
      transition: 'opacity 0.4s',
      fontFamily: 'Courier New, monospace',
    }}>
      ✓ COLETADO  #{count}
    </div>
  );
}
